from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import shutil
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

VERSION = "1.0.0"
ROOT = f"access_audit-{VERSION}"
WHEEL_PREFIXES = ("access_audit/", f"access_audit-{VERSION}.dist-info/")
MAX_WHEEL_BYTES = 1_048_576
MAX_SDIST_BYTES = 2_097_152
MAX_WHEEL_MEMBERS = 64
MAX_SDIST_MEMBERS = 160
FORBIDDEN_ANYWHERE = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}
FORBIDDEN_ROOT_OUTPUTS = {"dist", "release"}


def _fail(reason: str) -> None:
    raise ValueError(reason)


def _validate_path(name: str, *, root_required: bool) -> None:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        _fail("unsafe-archive-path")
    if any(part in FORBIDDEN_ANYWHERE for part in path.parts):
        _fail("forbidden-archive-path")
    if root_required and (not path.parts or path.parts[0] != ROOT):
        _fail("wrong-sdist-root")
    if root_required and len(path.parts) > 1 and path.parts[1] in FORBIDDEN_ROOT_OUTPUTS:
        _fail("forbidden-archive-path")


def _validate_wheel(path: Path) -> None:
    if path.stat().st_size > MAX_WHEEL_BYTES:
        _fail("wheel-too-large")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) > MAX_WHEEL_MEMBERS:
            _fail("wheel-member-budget")
        for info in archive.infolist():
            _validate_path(info.filename, root_required=False)
            if info.is_dir() or not info.filename.startswith(WHEEL_PREFIXES):
                _fail("unexpected-wheel-member")
            mode = info.external_attr >> 16
            if mode and (mode & 0o170000) not in {0, 0o100000}:
                _fail("unsafe-wheel-member")
        metadata = archive.read(f"access_audit-{VERSION}.dist-info/METADATA")
        if f"\nVersion: {VERSION}\n".encode() not in b"\n" + metadata:
            _fail("wheel-version-mismatch")


def _read_sdist(path: Path) -> list[tuple[str, bool, bytes]]:
    if path.stat().st_size > MAX_SDIST_BYTES:
        _fail("sdist-too-large")
    result: list[tuple[str, bool, bytes]] = []
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or len(names) > MAX_SDIST_MEMBERS:
            _fail("sdist-member-budget")
        for member in members:
            _validate_path(member.name, root_required=True)
            if not (member.isfile() or member.isdir()):
                _fail("unsafe-sdist-member")
            extracted = None if member.isdir() else archive.extractfile(member)
            if not member.isdir() and extracted is None:
                _fail("unreadable-sdist-member")
            payload = b"" if extracted is None else extracted.read()
            result.append((member.name, member.isdir(), payload))
    package_info = {name: payload for name, is_dir, payload in result if not is_dir}
    metadata = package_info.get(f"{ROOT}/PKG-INFO")
    if metadata is None or f"\nVersion: {VERSION}\n".encode() not in b"\n" + metadata:
        _fail("sdist-version-mismatch")
    return result


def _canonical_sdist(entries: list[tuple[str, bool, bytes]], output: Path) -> None:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, is_directory, payload in sorted(entries):
            member = tarfile.TarInfo(name)
            member.mtime = 0
            member.uid = 0
            member.gid = 0
            member.uname = ""
            member.gname = ""
            member.mode = 0o755 if is_directory else 0o644
            member.type = tarfile.DIRTYPE if is_directory else tarfile.REGTYPE
            member.size = 0 if is_directory else len(payload)
            archive.addfile(member, None if is_directory else io.BytesIO(payload))
    with (
        output.open("wb") as destination,
        gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed,
    ):
        compressed.write(tar_buffer.getvalue())


def _write_checksums(output: Path, artifacts: list[Path]) -> None:
    lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in sorted(artifacts)
    ]
    output.joinpath("SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and canonicalize release packages")
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    wheels = list(arguments.dist.glob(f"access_audit-{VERSION}-*.whl"))
    sdists = list(arguments.dist.glob(f"access_audit-{VERSION}.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        _fail("expected-one-wheel-and-sdist")
    _validate_wheel(wheels[0])
    entries = _read_sdist(sdists[0])
    arguments.output.mkdir(parents=True, exist_ok=False)
    wheel_output = arguments.output.joinpath(wheels[0].name)
    sdist_output = arguments.output.joinpath(sdists[0].name)
    shutil.copyfile(wheels[0], wheel_output)
    _canonical_sdist(entries, sdist_output)
    _validate_wheel(wheel_output)
    _read_sdist(sdist_output)
    _write_checksums(arguments.output, [wheel_output, sdist_output])


if __name__ == "__main__":
    main()
