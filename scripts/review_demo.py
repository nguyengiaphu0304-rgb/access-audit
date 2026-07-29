from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from access_audit import (
    apply_suppressions,
    compare_reports,
    generate_explorer,
    verify_comparison,
    verify_review,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic review workflow evidence")
    parser.add_argument("--output-directory", type=Path, required=True)
    arguments = parser.parse_args()
    report = Path("evidence/failing-report.json").read_bytes()
    suppressions = Path("fixtures/suppressions.json").read_bytes()
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    review = apply_suppressions(report, suppressions, as_of=date(2026, 7, 29))
    comparison = compare_reports(report, report)
    verify_review(report, suppressions, review, as_of=date(2026, 7, 29))
    verify_comparison(report, report, comparison)
    arguments.output_directory.joinpath("review-summary.json").write_bytes(review)
    arguments.output_directory.joinpath("comparison.json").write_bytes(comparison)
    arguments.output_directory.joinpath("explorer.html").write_bytes(generate_explorer(report))


if __name__ == "__main__":
    main()
