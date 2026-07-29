from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from access_audit import (
    AuditError,
    __version__,
    apply_suppressions,
    compare_reports,
    create_report,
    generate_explorer,
    verify_comparison,
    verify_report,
    verify_review,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_object(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        reason = "expected-object"
        raise TypeError(reason)
    return value


def _assert_tamper_rejected(source: bytes, report: bytes) -> None:
    value = _load_object(report)
    payload = value["payload"]
    if not isinstance(payload, dict):
        reason = "expected-payload-object"
        raise TypeError(reason)
    summary = payload["summary"]
    if not isinstance(summary, dict):
        reason = "expected-summary-object"
        raise TypeError(reason)
    summary["finding_count"] = int(summary["finding_count"]) + 1
    tampered = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    try:
        verify_report(source, tampered)
    except AuditError:
        return
    reason = "tampered-report-accepted"
    raise RuntimeError(reason)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic v1 release evidence")
    parser.add_argument("--output-directory", type=Path, required=True)
    arguments = parser.parse_args()
    failing_source = Path("fixtures/failing.html").read_bytes()
    passing_source = Path("fixtures/passing.html").read_bytes()
    suppressions = Path("fixtures/suppressions.json").read_bytes()
    failing_report = create_report(failing_source)
    passing_report = create_report(passing_source)
    review = apply_suppressions(
        failing_report,
        suppressions,
        as_of=date(2026, 7, 29),
    )
    comparison = compare_reports(passing_report, failing_report)
    explorer = generate_explorer(failing_report)

    verify_report(failing_source, failing_report)
    verify_report(passing_source, passing_report)
    verify_review(
        failing_report,
        suppressions,
        review,
        as_of=date(2026, 7, 29),
    )
    verify_comparison(passing_report, failing_report, comparison)
    _assert_tamper_rejected(failing_source, failing_report)

    outputs = {
        "comparison.json": comparison,
        "explorer.html": explorer,
        "failing-report.json": failing_report,
        "passing-report.json": passing_report,
        "review-summary.json": review,
    }
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    for name, payload in outputs.items():
        arguments.output_directory.joinpath(name).write_bytes(payload)

    failing = _load_object(failing_report)
    passing = _load_object(passing_report)
    compared = _load_object(comparison)
    reviewed = _load_object(review)
    manifest = {
        "artifact": "access-audit-release-evidence",
        "checks": [
            "comparison-replay",
            "report-replay",
            "review-replay",
            "tamper-rejection",
        ],
        "files": {
            name: {"bytes": len(payload), "sha256": _sha256(payload)}
            for name, payload in sorted(outputs.items())
        },
        "schema_version": 1,
        "summary": {
            "comparison_regression": compared["has_regression"],
            "failing_findings": failing["payload"]["summary"]["finding_count"],
            "passing_findings": passing["payload"]["summary"]["finding_count"],
            "suppressed_findings": reviewed["suppressed_count"],
        },
        "tool_version": __version__,
    }
    arguments.output_directory.joinpath("release-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
