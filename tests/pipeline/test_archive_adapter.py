"""
DN CLASSIC — Archive Adapter Test Suite.
Verifies deterministic reading, SHA-256 hashing, NFC normalization,
and error handling across ZIP archives and directories.
"""
import io
import os
import zipfile
import pytest

from archive_adapter import (
    read_archive_or_directory,
    read_zip_bytes,
    extract_text_from_zip,
    compute_sha256,
    normalize_text_nfc,
    is_text_file,
)
from upstream_types import ReadOnlySource, AnalysisSnapshot


def test_compute_sha256():
    data = b"test payload"
    expected = "813ca5285c28ccee5cab8b10ebda9c908fd6d78ed9dc94cc65ea6cb67a7f13ae"
    assert compute_sha256(data) == expected


def test_normalize_text_nfc():
    decomposed = "e\u0301"  # 'e' + combining acute accent
    precomposed = "\u00e9"  # 'é'
    assert decomposed != precomposed
    assert normalize_text_nfc(decomposed) == precomposed


def test_is_text_file():
    assert is_text_file("document.txt") is True
    assert is_text_file("readme.md") is True
    assert is_text_file("data.json") is True
    assert is_text_file("image.jpg") is False
    assert is_text_file("binary.exe") is False
    assert is_text_file("archive.zip") is False


def test_read_zip_bytes_deterministic(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("b_doc.txt", "Document B content".encode("utf-8"))
        zf.writestr("a_doc.txt", "Document A content".encode("utf-8"))
        zf.writestr("photo.png", b"\x89PNG\r\n\x1a\nfake")
    
    zip_bytes = buf.getvalue()
    snapshot = read_zip_bytes(zip_bytes, snapshot_id="test-zip")
    
    assert snapshot.snapshot_id == "test-zip"
    assert "photo.png" not in snapshot.sources
    assert list(snapshot.sources.keys()) == ["a_doc.txt", "b_doc.txt"]
    assert snapshot.sources["a_doc.txt"].text_content == "Document A content"
    assert snapshot.sources["b_doc.txt"].text_content == "Document B content"
    assert len(snapshot.computed_hash) == 64


def test_read_directory_deterministic(tmp_path):
    dir_path = tmp_path / "docs_dir"
    dir_path.mkdir()
    
    (dir_path / "file2.txt").write_text("Second file", encoding="utf-8")
    (dir_path / "file1.txt").write_text("First file", encoding="utf-8")
    (dir_path / "ignore.bin").write_bytes(b"\x00\x01\x02")
    
    snapshot = read_archive_or_directory(str(dir_path))
    assert list(snapshot.sources.keys()) == ["file1.txt", "file2.txt"]
    assert snapshot.sources["file1.txt"].text_content == "First file"
    assert snapshot.sources["file2.txt"].text_content == "Second file"


def test_read_nonexistent_path():
    with pytest.raises(FileNotFoundError):
        read_archive_or_directory("/nonexistent/path/here.zip")


def test_extract_text_from_zip(tmp_path):
    zip_file = tmp_path / "simple.zip"
    with zipfile.ZipFile(zip_file, "w") as zf:
        zf.writestr("doc.txt", "Extracted text".encode("utf-8"))
    
    extracted = extract_text_from_zip(str(zip_file))
    assert extracted == {"doc.txt": "Extracted text"}
