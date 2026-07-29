"""Auditable suppression, baseline comparison, and explorer generation."""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from datetime import date
from typing import Any, Final

SUPPRESSION_SCHEMA: Final = "access-audit/suppressions-v1"
REVIEW_SCHEMA: Final = "access-audit/review-v1"
COMPARISON_SCHEMA: Final = "access-audit/comparison-v1"
MAX_ARTIFACT_BYTES: Final = 1_048_576
MAX_SUPPRESSIONS: Final = 2_000
MAX_OWNER_LENGTH: Final = 64
MAX_ID_LENGTH: Final = 64
MAX_FINDING_KEY_LENGTH: Final = 128
MAX_SUPPRESSION_DAYS: Final = 366
RATIONALES: Final = {"accepted_risk", "false_positive", "pending_fix", "third_party"}
SEVERITY_RANK: Final = {"warning": 1, "error": 2}
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class ReviewError(ValueError):
    """Raised when review evidence is malformed, ambiguous, or unsafe."""


def _canonical(value: object) -> bytes:
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"{serialized}\n".encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _object(value: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ReviewError("unexpected fields")
    return value


def _parse_json(value: bytes) -> dict[str, Any]:
    if len(value) > MAX_ARTIFACT_BYTES:
        raise ReviewError("artifact exceeds byte limit")
    try:
        parsed = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReviewError("invalid json") from error
    if not isinstance(parsed, dict):
        raise ReviewError("artifact must be an object")
    return parsed


def _report(value: bytes) -> dict[str, Any]:
    envelope = _object(_parse_json(value), {"payload", "schema_version", "sha256"})
    payload = envelope["payload"]
    if not isinstance(payload, dict) or envelope["schema_version"] != "access-audit/report-v1":
        raise ReviewError("unsupported report")
    if envelope["sha256"] != _sha256(_canonical(payload)):
        raise ReviewError("report checksum mismatch")
    findings = payload.get("findings")
    if not isinstance(findings, list) or len(findings) > 10_000:
        raise ReviewError("invalid findings")
    return envelope


def _finding_key(finding: dict[str, Any]) -> str:
    rule_id = finding.get("rule_id")
    tag = finding.get("element_tag")
    index = finding.get("element_index")
    severity = finding.get("severity")
    if (
        not isinstance(rule_id, str)
        or not isinstance(tag, str)
        or not isinstance(index, int)
        or index < 0
        or severity not in SEVERITY_RANK
    ):
        raise ReviewError("invalid finding")
    return f"{rule_id}:{index}:{tag}"


def _iso_date(value: object) -> date:
    if not isinstance(value, str):
        raise ReviewError("invalid date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ReviewError("invalid date") from error
    if parsed.isoformat() != value:
        raise ReviewError("non-canonical date")
    return parsed


def _suppression_entries(
    value: bytes,
    *,
    report_sha256: str,
    as_of: date,
) -> dict[str, dict[str, Any]]:
    artifact = _object(_parse_json(value), {"as_of", "entries", "report_sha256", "schema"})
    if artifact["schema"] != SUPPRESSION_SCHEMA or artifact["report_sha256"] != report_sha256:
        raise ReviewError("suppression lineage mismatch")
    if _iso_date(artifact["as_of"]) != as_of:
        raise ReviewError("as-of mismatch")
    entries = artifact["entries"]
    if not isinstance(entries, list) or len(entries) > MAX_SUPPRESSIONS:
        raise ReviewError("invalid suppression count")
    result: dict[str, dict[str, Any]] = {}
    normalized_ids: set[str] = set()
    targets: set[str] = set()
    for raw in entries:
        entry = _object(
            raw,
            {
                "created_on",
                "expires_on",
                "finding_key",
                "owner",
                "rationale",
                "suppression_id",
            },
        )
        suppression_id = entry["suppression_id"]
        owner = entry["owner"]
        rationale = entry["rationale"]
        target = entry["finding_key"]
        if not isinstance(suppression_id, str) or not SAFE_ID.fullmatch(suppression_id):
            raise ReviewError("invalid suppression id")
        normalized_id = unicodedata.normalize("NFC", suppression_id)
        if normalized_id in normalized_ids:
            raise ReviewError("duplicate suppression id")
        normalized_ids.add(normalized_id)
        if (
            not isinstance(owner, str)
            or len(owner) > MAX_OWNER_LENGTH
            or not SAFE_ID.fullmatch(owner)
            or rationale not in RATIONALES
            or not isinstance(target, str)
            or len(target) > MAX_FINDING_KEY_LENGTH
            or target in targets
        ):
            raise ReviewError("invalid suppression entry")
        targets.add(target)
        created = _iso_date(entry["created_on"])
        expires = _iso_date(entry["expires_on"])
        if expires < as_of or expires < created or (expires - created).days > MAX_SUPPRESSION_DAYS:
            raise ReviewError("expired or overlong suppression")
        result[target] = entry
    return result


def apply_suppressions(report: bytes, suppressions: bytes, *, as_of: date) -> bytes:
    """Create a minimized review summary without mutating the source report."""
    envelope = _report(report)
    report_sha = _sha256(report)
    entries = _suppression_entries(suppressions, report_sha256=report_sha, as_of=as_of)
    findings = envelope["payload"]["findings"]
    finding_map = {_finding_key(finding): finding for finding in findings}
    if len(finding_map) != len(findings) or not set(entries).issubset(finding_map):
        raise ReviewError("suppression target mismatch")
    suppressed = [
        {
            "finding_key": key,
            "owner": entries[key]["owner"],
            "rationale": entries[key]["rationale"],
            "suppression_id": entries[key]["suppression_id"],
        }
        for key in sorted(entries)
    ]
    summary = {
        "schema": REVIEW_SCHEMA,
        "as_of": as_of.isoformat(),
        "report_sha256": report_sha,
        "active_count": len(findings) - len(suppressed),
        "suppressed": suppressed,
        "suppressed_count": len(suppressed),
        "total_count": len(findings),
    }
    return _canonical(summary)


def verify_review(
    report: bytes,
    suppressions: bytes,
    summary: bytes,
    *,
    as_of: date,
) -> None:
    """Independently reproduce and verify a review summary."""
    if (
        len(summary) > MAX_ARTIFACT_BYTES
        or apply_suppressions(
            report,
            suppressions,
            as_of=as_of,
        )
        != summary
    ):
        raise ReviewError("review summary mismatch")


def compare_reports(baseline: bytes, current: bytes) -> bytes:
    """Compare reports without allowing suppression state to hide regressions."""
    baseline_report = _report(baseline)
    current_report = _report(current)
    before = {_finding_key(item): item for item in baseline_report["payload"]["findings"]}
    after = {_finding_key(item): item for item in current_report["payload"]["findings"]}
    if len(before) != len(baseline_report["payload"]["findings"]) or len(after) != len(
        current_report["payload"]["findings"],
    ):
        raise ReviewError("duplicate finding identity")
    result: dict[str, list[str]] = {
        "new": [],
        "resolved": [],
        "severity_decreased": [],
        "severity_increased": [],
        "unchanged": [],
    }
    for key in sorted(set(before) | set(after)):
        if key not in before:
            result["new"].append(key)
        elif key not in after:
            result["resolved"].append(key)
        else:
            old_rank = SEVERITY_RANK[before[key]["severity"]]
            new_rank = SEVERITY_RANK[after[key]["severity"]]
            bucket = (
                "severity_increased"
                if new_rank > old_rank
                else "severity_decreased"
                if new_rank < old_rank
                else "unchanged"
            )
            result[bucket].append(key)
    payload = {
        "schema": COMPARISON_SCHEMA,
        "baseline_report_sha256": _sha256(baseline),
        "current_report_sha256": _sha256(current),
        "has_regression": bool(result["new"] or result["severity_increased"]),
        **result,
    }
    return _canonical(payload)


def verify_comparison(baseline: bytes, current: bytes, comparison: bytes) -> None:
    """Independently reproduce and verify a comparison artifact."""
    if len(comparison) > MAX_ARTIFACT_BYTES or compare_reports(baseline, current) != comparison:
        raise ReviewError("comparison mismatch")


def generate_explorer(report: bytes) -> bytes:
    """Generate a static semantic explorer containing only minimized finding fields."""
    envelope = _report(report)
    findings = envelope["payload"]["findings"]
    rows = "".join(
        "<tr data-severity='{severity}'><th scope='row'>{rule}</th><td>{severity}</td>"
        "<td>{tag}</td><td>{index}</td><td>{line}:{column}</td></tr>".format(
            rule=html.escape(str(item["rule_id"])),
            severity=html.escape(str(item["severity"])),
            tag=html.escape(str(item["element_tag"])),
            index=int(item["element_index"]),
            line=int(item["line"]),
            column=int(item["column"]),
        )
        for item in findings
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy"
 content="default-src 'none'; style-src 'self'; script-src 'self'">
<title>Access Audit finding explorer</title><link rel="stylesheet" href="/explorer.css"></head>
<body><a class="skip" href="#findings">Skip to findings</a><main>
<h1>Finding explorer</h1><p>Automated findings are review signals, not WCAG conformance.</p>
<fieldset><legend>Filter by severity</legend>
<button type="button" data-filter="all" aria-pressed="true">All</button>
<button type="button" data-filter="error" aria-pressed="false">Errors</button>
<button type="button" data-filter="warning" aria-pressed="false">Warnings</button>
</fieldset><p id="result-count" role="status" aria-live="polite">{len(findings)} findings shown</p>
<div class="table-wrap"><table id="findings"><caption>Privacy-minimized static findings</caption>
<thead><tr><th scope="col">Rule</th><th scope="col">Severity</th><th scope="col">Element</th>
<th scope="col">Index</th><th scope="col">Source location</th></tr></thead><tbody>{rows}</tbody>
</table></div><p id="empty" hidden>No findings match this filter.</p>
</main><script src="/explorer.js"></script></body></html>
"""
    return document.encode()
