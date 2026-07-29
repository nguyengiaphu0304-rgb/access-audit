from __future__ import annotations

import gzip
import io
import tarfile
from typing import TYPE_CHECKING

import pytest

from scripts.package_release import ROOT, _canonical_sdist, _read_sdist, _validate_path

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "name",
    ["../escape", "/absolute", f"{ROOT}/../escape", f"{ROOT}/node_modules/file"],
)
def test_archive_path_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(ValueError, match=r"archive|sdist|forbidden"):
        _validate_path(name, root_required=True)


def test_canonical_sdist_is_byte_identical(tmp_path: Path) -> None:
    entries = [
        (ROOT, True, b""),
        (f"{ROOT}/PKG-INFO", False, b"Metadata-Version: 2.4\nVersion: 1.0.0\n"),
        (f"{ROOT}/README.md", False, b"release fixture\n"),
    ]
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"
    _canonical_sdist(entries, first)
    _canonical_sdist(list(reversed(entries)), second)
    assert first.read_bytes() == second.read_bytes()
    assert _read_sdist(first) == sorted(entries)
    with (
        gzip.open(first) as compressed,
        tarfile.open(fileobj=io.BytesIO(compressed.read())) as archive,
    ):
        assert all(member.uid == 0 and member.gid == 0 for member in archive.getmembers())


def test_sdist_rejects_link_member(tmp_path: Path) -> None:
    path = tmp_path / "link.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo(f"{ROOT}/link")
        member.type = tarfile.SYMTYPE
        member.linkname = "../target"
        archive.addfile(member)
    with pytest.raises(ValueError, match="unsafe-sdist-member"):
        _read_sdist(path)


def test_sdist_rejects_duplicate_member(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        for _ in range(2):
            member = tarfile.TarInfo(f"{ROOT}/duplicate")
            member.size = 0
            archive.addfile(member, io.BytesIO())
    with pytest.raises(ValueError, match="sdist-member-budget"):
        _read_sdist(path)
