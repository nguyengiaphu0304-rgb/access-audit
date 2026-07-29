from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from access_audit import AuditError, create_report, parse_html, verify_report
from access_audit.engine import MAX_FINDINGS, audit

ROOT = Path(__file__).resolve().parents[1]


def _page(body: str, *, lang: str = "en", title: str = "Example") -> bytes:
    return (
        f"<!doctype html><html lang='{lang}'><head><title>{title}</title></head>"
        f"<body><main><h1>Heading</h1>{body}</main></body></html>"
    ).encode()


def _rules(source: bytes) -> list[str]:
    return [finding.rule_id for finding in audit(parse_html(source))]


def test_passing_fixture_has_no_static_findings() -> None:
    source = (ROOT / "fixtures/passing.html").read_bytes()
    assert audit(parse_html(source)) == ()
    report = json.loads(create_report(source))
    assert report["payload"]["summary"]["finding_count"] == 0


def test_failing_fixture_covers_every_v01_rule() -> None:
    source = (ROOT / "fixtures/failing.html").read_bytes()
    assert set(_rules(source)) == {f"AA{number:03}" for number in range(1, 13)}


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("<img src='x'>", "AA005"),
        ("<input>", "AA006"),
        ("<button></button>", "AA007"),
        ("<a href='/'></a>", "AA008"),
        ("<div tabindex='1'></div>", "AA011"),
        ("<table><tr><td>X</td></tr></table>", "AA012"),
    ],
)
def test_single_element_rules(body: str, expected: str) -> None:
    assert expected in _rules(_page(body))


@pytest.mark.parametrize(
    ("body", "absent"),
    [
        ("<img src='x' alt=''>", "AA005"),
        ("<img src='x' role='presentation'>", "AA005"),
        ("<img src='x' role=' NONE '>", "AA005"),
        ("<label for='x'>Name</label><input id='x'>", "AA006"),
        ("<label>Name<input></label>", "AA006"),
        ("<input aria-label='Name'>", "AA006"),
        ("<button>Save</button>", "AA007"),
        ("<input type='submit' value='Save'>", "AA007"),
        ("<a href='/'><img alt='Home' src='x'></a>", "AA008"),
        ("<table><caption>Results</caption></table>", "AA012"),
        ("<table aria-label='Results'></table>", "AA012"),
    ],
)
def test_valid_static_signals_avoid_specific_findings(body: str, absent: str) -> None:
    assert absent not in _rules(_page(body))


def test_missing_and_multiple_main_landmarks_share_stable_rule() -> None:
    missing = b"<html lang='en'><head><title>T</title></head><body><h1>H</h1></body></html>"
    multiple = _page("</main><main><h2>Other</h2>")
    assert _rules(missing).count("AA003") == 1
    assert _rules(multiple).count("AA003") == 1


def test_heading_skip_and_missing_h1_are_reported() -> None:
    missing = (
        b"<html lang='en'><head><title>T</title></head><body><main><h2>H</h2></main></body></html>"
    )
    assert "AA004" in _rules(missing)
    assert "AA004" in _rules(_page("<h3>Skipped</h3>"))


def test_nfc_colliding_ids_are_both_reported() -> None:
    composed = "café"
    decomposed = unicodedata.normalize("NFD", composed)
    findings = audit(parse_html(_page(f"<div id='{composed}'></div><div id='{decomposed}'></div>")))
    duplicates = [finding for finding in findings if finding.rule_id == "AA009"]
    assert len(duplicates) == 2


@pytest.mark.parametrize(
    "attribute",
    [
        "aria-labelledby",
        "aria-describedby",
        "aria-controls",
        "aria-owns",
        "aria-activedescendant",
    ],
)
def test_missing_aria_reference_is_reported(attribute: str) -> None:
    assert "AA010" in _rules(_page(f"<div {attribute}='missing'></div>"))


def test_existing_aria_reference_is_accepted() -> None:
    assert "AA010" not in _rules(_page("<p id='help'>Help</p><input aria-describedby='help'>"))


def test_ambiguous_aria_reference_is_reported() -> None:
    source = _page("<p id='help'>One</p><p id='help'>Two</p><input aria-describedby='help'>")
    assert "AA010" in _rules(source)


def test_hidden_only_control_and_link_content_do_not_create_name_signal() -> None:
    body = (
        "<button><span aria-hidden='true'>icon</span></button>"
        "<a href='/'><img alt='Home' aria-hidden='true'></a>"
    )
    rules = _rules(_page(body))
    assert "AA007" in rules
    assert "AA008" in rules


def test_report_is_canonical_reproducible_and_privacy_minimized() -> None:
    source = _page("<label for='secret'>Private person</label><input id='secret'>")
    first = create_report(source)
    second = create_report(source)
    assert first == second
    verify_report(source, first)
    assert b"Private person" not in first
    assert b"secret" not in first
    parsed = json.loads(first)
    assert parsed["schema_version"] == "access-audit/report-v1"
    assert parsed["payload"]["summary"]["truncated"] is False
    assert parsed["payload"]["limitations"][-1] == "not_wcag_conformance_evidence"


def test_report_verification_rejects_tampering_and_wrong_source() -> None:
    source = _page("<button>Save</button>")
    report = create_report(source)
    with pytest.raises(AuditError, match="does not match"):
        verify_report(source, report.replace(b'"finding_count":0', b'"finding_count":1'))
    with pytest.raises(AuditError, match="does not match"):
        verify_report(_page("<button></button>"), report)


def test_findings_are_stably_sorted() -> None:
    source = _page("<img><button></button><a href='/'></a>")
    findings = audit(parse_html(source))
    keys = [(item.rule_id, item.line, item.column, item.element_index) for item in findings]
    assert keys == sorted(keys)


def test_empty_document_fails_closed() -> None:
    with pytest.raises(AuditError, match="no elements"):
        create_report(b"")


def test_finding_budget_fails_closed() -> None:
    repeated = "".join("<img id='same'>" for _ in range((MAX_FINDINGS // 2) + 1))
    with pytest.raises(AuditError, match="finding limit"):
        create_report(_page(repeated))
