from __future__ import annotations

import argparse
from pathlib import Path

from access_audit import create_report, verify_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic audit evidence")
    parser.add_argument("--fixture", type=Path, default=Path("fixtures/failing.html"))
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    source = arguments.fixture.read_bytes()
    report = create_report(source)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(report)
    verify_report(source, report)


if __name__ == "__main__":
    main()
