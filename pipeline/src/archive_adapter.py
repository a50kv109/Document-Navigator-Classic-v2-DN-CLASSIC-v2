"""
DN CLASSIC — Deterministic Archive & Document Adapter.
Handles reading ZIP archives or directories, computing SHA-256 digests,
normalizing text (NFC), and producing ReadOnlySource and AnalysisSnapshot.
"""
from __future__ import annotations
import os
import zipfile
import hashlib
import unicodedata
from typing import Dict
from upstream_types import ReadOnlySource, AnalysisSnapshot

BINARY_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".tiff", ".webp",
    ".pdf", ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pyc", ".pyd", ".pyo", ".class", ".o", ".a", ".woff", ".woff2", ".ttf",
}


def compute_sha256(data: bytes) -> str:
    """Deterministic SHA-256 hash of raw byte data."""
    return hashlib.sha256(data).hexdigest()


def normalize_text_nfc(text: str) -> str:
    """Deterministic NFC Unicode normalization matching CORE requirements."""
    return unicodedata.normalize("NFC", text)


def is_text_file(filename: str) -> bool:
    """Returns True if the file should be treated as text."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return False
    return True


def read_zip_bytes(zip_bytes: bytes, snapshot_id: str = "snapshot-zip") -> AnalysisSnapshot:
    """Reads a ZIP archive from raw bytes deterministically."""
    import io
    sources: Dict[str, ReadOnlySource] = {}
    total_bytes = len(zip_bytes)
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        # Sort names for deterministic ordering
        for name in sorted(zf.namelist()):
            # Skip directories, metadata, and binary file extensions
            if name.endswith("/") or name.startswith("__MACOSX/") or name.startswith("._"):
                continue
            if not is_text_file(name):
                continue
            raw = zf.read(name)
            # Only process if text decodable
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                # Skip non-utf8 files deterministically
                continue
            norm_text = normalize_text_nfc(text)
            file_hash = compute_sha256(raw)
            sources[name] = ReadOnlySource(
                source_id=name,
                raw_bytes=raw,
                text_content=norm_text,
                sha256_hash=file_hash,
            )
            
    hasher = hashlib.sha256()
    for name in sorted(sources.keys()):
        hasher.update(name.encode("utf-8"))
        hasher.update(sources[name].sha256_hash.encode("utf-8"))
    snapshot_hash = hasher.hexdigest()
    
    return AnalysisSnapshot(
        snapshot_id=snapshot_id,
        sources=sources,
        total_bytes=total_bytes,
        computed_hash=snapshot_hash,
    )


def read_archive_or_directory(source_input: str | bytes) -> AnalysisSnapshot:
    """Reads an archive (.zip file path, bytes) or a directory of text files deterministically."""
    if isinstance(source_input, bytes):
        return read_zip_bytes(source_input, snapshot_id="in_memory_archive.zip")

    path = source_input
    if not os.path.exists(path):
        raise FileNotFoundError(f"Source path does not exist: {path}")
        
    if os.path.isfile(path) and (path.endswith(".zip") or zipfile.is_zipfile(path)):
        with open(path, "rb") as f:
            raw_bytes = f.read()
        return read_zip_bytes(raw_bytes, snapshot_id=os.path.basename(path))
        
    if os.path.isdir(path):
        sources: Dict[str, ReadOnlySource] = {}
        total_bytes = 0
        all_files = []
        for root, _, files in os.walk(path):
            for f in files:
                if f.startswith(".") or f.startswith("._"):
                    continue
                if not is_text_file(f):
                    continue
                rel_path = os.path.relpath(os.path.join(root, f), path)
                all_files.append((rel_path, os.path.join(root, f)))
                
        for rel_path, full_path in sorted(all_files, key=lambda x: x[0]):
            with open(full_path, "rb") as f:
                raw = f.read()
            total_bytes += len(raw)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            norm_text = normalize_text_nfc(text)
            file_hash = compute_sha256(raw)
            sources[rel_path] = ReadOnlySource(
                source_id=rel_path,
                raw_bytes=raw,
                text_content=norm_text,
                sha256_hash=file_hash,
            )
            
        hasher = hashlib.sha256()
        for name in sorted(sources.keys()):
            hasher.update(name.encode("utf-8"))
            hasher.update(sources[name].sha256_hash.encode("utf-8"))
        snapshot_hash = hasher.hexdigest()
        
        return AnalysisSnapshot(
            snapshot_id=os.path.basename(path.rstrip("/\\")),
            sources=sources,
            total_bytes=total_bytes,
            computed_hash=snapshot_hash,
        )
        
    raise ValueError(f"Unsupported path format: {path}")


def extract_text_from_zip(zip_path: str) -> Dict[str, str]:
    """Compatibility wrapper for extracting dictionary of text documents from zip."""
    snapshot = read_archive_or_directory(zip_path)
    return {k: v.text_content for k, v in snapshot.sources.items()}
