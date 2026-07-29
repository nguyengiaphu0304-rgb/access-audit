from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(source: Path, output: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(  # noqa: S603 - fixed interpreter argv, no shell
        [
            sys.executable,
            "-m",
            "access_audit",
            str(source),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def test_cli_exit_codes_and_structured_summary(tmp_path: Path) -> None:
    passing = _run(ROOT / "fixtures/passing.html", tmp_path / "passing.json")
    failing = _run(ROOT / "fixtures/failing.html", tmp_path / "failing.json")
    assert passing.returncode == 0
    assert failing.returncode == 1
    summary = json.loads(failing.stderr)
    assert summary["event"] == "audit.complete"
    assert summary["finding_count"] > 0
    assert str(ROOT) not in failing.stderr


def test_cli_sanitizes_invalid_input_failure(tmp_path: Path) -> None:
    source = tmp_path / "private-name.html"
    source.write_bytes(b"\xff")
    result = _run(source, tmp_path / "report.json")
    assert result.returncode == 2
    assert result.stderr == '{"event":"audit.failed","reason":"invalid_or_unreadable_input"}\n'
    assert "private-name" not in result.stderr
