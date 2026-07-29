from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from access_audit import (
    ReviewError,
    apply_suppressions,
    compare_reports,
    generate_explorer,
    verify_comparison,
    verify_review,
)

REPORT = Path("evidence/failing-report.json").read_bytes()
SUPPRESSIONS = Path("fixtures/suppressions.json").read_bytes()
AS_OF = date(2026, 7, 29)


def _suppression(**updates: object) -> bytes:
    artifact = json.loads(SUPPRESSIONS)
    artifact.update(updates)
    return json.dumps(artifact).encode()


def _report_with_findings(findings: list[dict[str, object]]) -> bytes:
    envelope = json.loads(REPORT)
    envelope["payload"]["findings"] = findings
    envelope["sha256"] = hashlib.sha256(
        (
            json.dumps(
                envelope["payload"],
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode(),
    ).hexdigest()
    return json.dumps(envelope).encode()


def test_review_summary_preserves_report_and_minimizes_suppression() -> None:
    before = bytes(REPORT)
    summary = json.loads(apply_suppressions(REPORT, SUPPRESSIONS, as_of=AS_OF))
    assert before == REPORT
    assert summary["total_count"] == 13
    assert summary["active_count"] == 12
    assert summary["suppressed_count"] == 1
    assert summary["suppressed"] == [
        {
            "finding_key": "AA005:7:img",
            "owner": "accessibility-team",
            "rationale": "pending_fix",
            "suppression_id": "synthetic-image-review",
        },
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema", "unknown"),
        ("report_sha256", "0" * 64),
        ("as_of", "2026-7-29"),
        ("as_of", "2026-07-28"),
    ],
)
def test_suppression_artifact_rejects_invalid_top_level(field: str, value: str) -> None:
    with pytest.raises(ReviewError):
        apply_suppressions(REPORT, _suppression(**{field: value}), as_of=AS_OF)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("suppression_id", "Not Safe"),
        ("owner", "../owner"),
        ("rationale", "because I said so"),
        ("created_on", "2026-02-30"),
        ("expires_on", "2026-07-28"),
        ("expires_on", "2028-01-01"),
        ("finding_key", "AA999:0:html"),
    ],
)
def test_suppression_entry_fails_closed(field: str, value: str) -> None:
    artifact = json.loads(SUPPRESSIONS)
    artifact["entries"][0][field] = value
    with pytest.raises(ReviewError):
        apply_suppressions(REPORT, json.dumps(artifact).encode(), as_of=AS_OF)


def test_duplicate_target_and_unknown_fields_are_rejected() -> None:
    artifact = json.loads(SUPPRESSIONS)
    duplicate = dict(artifact["entries"][0])
    duplicate["suppression_id"] = "another-id"
    artifact["entries"].append(duplicate)
    with pytest.raises(ReviewError):
        apply_suppressions(REPORT, json.dumps(artifact).encode(), as_of=AS_OF)
    artifact = json.loads(SUPPRESSIONS)
    artifact["unexpected"] = True
    with pytest.raises(ReviewError):
        apply_suppressions(REPORT, json.dumps(artifact).encode(), as_of=AS_OF)


def test_comparison_classifies_all_transitions_and_regressions() -> None:
    baseline_findings = json.loads(REPORT)["payload"]["findings"][:2]
    current_findings = [dict(item) for item in baseline_findings]
    current_findings[0]["severity"] = "warning"
    current_findings.pop()
    added = dict(json.loads(REPORT)["payload"]["findings"][4])
    current_findings.append(added)
    result = json.loads(
        compare_reports(
            _report_with_findings(baseline_findings),
            _report_with_findings(current_findings),
        ),
    )
    assert result["has_regression"] is True
    assert result["new"] == ["AA005:7:img"]
    assert result["resolved"] == ["AA002:0:html"]
    assert result["severity_decreased"] == ["AA001:0:html"]


def test_identical_comparison_is_deterministic_and_not_regression() -> None:
    first = compare_reports(REPORT, REPORT)
    assert first == compare_reports(REPORT, REPORT)
    result = json.loads(first)
    assert result["has_regression"] is False
    assert len(result["unchanged"]) == 13


def test_independent_verifiers_reject_tampering() -> None:
    summary = apply_suppressions(REPORT, SUPPRESSIONS, as_of=AS_OF)
    comparison = compare_reports(REPORT, REPORT)
    verify_review(REPORT, SUPPRESSIONS, summary, as_of=AS_OF)
    verify_comparison(REPORT, REPORT, comparison)
    with pytest.raises(ReviewError):
        verify_review(REPORT, SUPPRESSIONS, summary + b" ", as_of=AS_OF)
    with pytest.raises(ReviewError):
        verify_comparison(REPORT, REPORT, comparison + b" ")


def test_explorer_is_semantic_minimized_and_escaped() -> None:
    output = generate_explorer(REPORT)
    assert output.startswith(b"<!doctype html>")
    assert b"<caption>" in output
    assert b"<th scope='row'>" in output
    assert b'role="status"' in output
    assert b"Content-Security-Policy" in output
    assert b"93d85a" not in output
    assert b'<script src="/explorer.js"></script>' in output
