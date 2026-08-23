import os
import zipfile
from upstream_pipeline import process_archive
from archive_adapter import extract_text_from_zip
from source_boundary import SourceDocument

def test_pipeline_extraction(tmp_path):
    zip_path = str(tmp_path / "test.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test1.txt", "Hello World".encode("utf-8"))
        zf.writestr("test2.txt", "Normalized \u00e9".encode("utf-8"))
        zf.writestr("ignore.jpg", b"fake image")
    
    docs = process_archive(zip_path)
    assert len(docs) == 2
    
    doc_ids = {d.document_id for d in docs}
    assert "test1.txt" in doc_ids
    assert "test2.txt" in doc_ids
    
    doc2 = next(d for d in docs if d.document_id == "test2.txt")
    
    import unicodedata
    assert doc2.text == unicodedata.normalize("NFC", "Normalized \u00e9")
    assert doc2.verify_span(0, 10, "Normalized")
