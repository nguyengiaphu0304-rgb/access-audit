"""Privacy-preserving command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from access_audit import AuditError, ParseError, create_report


def _read_source(path: str) -> bytes:
    if path == "-":
        return sys.stdin.buffer.read()
    return Path(path).read_bytes()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Static HTML accessibility preflight; not WCAG conformance evidence",
    )
    parser.add_argument("source", help="HTML file path or - for stdin")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        report = create_report(_read_source(arguments.source))
        parsed = json.loads(report)
        finding_count = int(parsed["payload"]["summary"]["finding_count"])
        error_count = int(parsed["payload"]["summary"]["error_count"])
        warning_count = int(parsed["payload"]["summary"]["warning_count"])
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_bytes(report)
        event = {
            "error_count": error_count,
            "event": "audit.complete",
            "finding_count": finding_count,
            "warning_count": warning_count,
        }
        sys.stderr.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        raise SystemExit(1 if finding_count else 0)
    except (AuditError, OSError, ParseError):
        sys.stderr.write('{"event":"audit.failed","reason":"invalid_or_unreadable_input"}\n')
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
