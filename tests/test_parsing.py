from __future__ import annotations

import zipfile
from pathlib import Path

from src.parsing.parser import clean_text, extract_text_from_docx, segment_cv, tokenize_and_normalize
from src.parsing.preprocessor import TextPreprocessor


def test_clean_text_removes_contact_artifacts():
    raw = "Contact me at dev@example.com or +33 6 12 34 56 78. Portfolio: https://example.com\nPython Developer"
    cleaned = clean_text(raw)
    assert "example.com" not in cleaned
    assert "@example" not in cleaned
    assert "python developer" in cleaned


def test_tokenize_and_normalize_filters_stopwords():
    tokens = tokenize_and_normalize("Python developers are building scalable APIs and data pipelines.")
    assert "python" in tokens
    assert "scalable" in tokens
    assert "are" not in tokens


def test_segment_cv_detects_sections():
    text = """PROFIL
Ingenieur logiciel
EXPERIENCE
5 ans sur Python et FastAPI
COMPETENCES
Python, SQL, Docker
LANGUES
Francais, Anglais
FORMATION
Master informatique
"""
    sections = segment_cv(text)
    assert "python" in sections["experience"].lower()
    assert "docker" in sections["skills"].lower()
    assert "master" in sections["education"].lower()


def test_extract_text_from_docx_zip_fallback(monkeypatch):
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>Python Engineer</w:t></w:r></w:p>
        <w:tbl>
          <w:tr><w:tc><w:p><w:r><w:t>Docker</w:t></w:r></w:p></w:tc></w:tr>
        </w:tbl>
      </w:body>
    </w:document>"""
    base_dir = Path(__file__).resolve().parents[1] / "tests_tmp"
    base_dir.mkdir(exist_ok=True)
    file_path = base_dir / "sample.docx"
    try:
        with zipfile.ZipFile(file_path, "w") as archive:
            archive.writestr("word/document.xml", document_xml)

        monkeypatch.setattr("src.parsing.parser.Document", None)
        text = extract_text_from_docx(str(file_path))
        assert "python engineer" in text.lower()
        assert "docker" in text.lower()
    finally:
        file_path.unlink(missing_ok=True)


def test_text_preprocessor_uses_cache():
    preprocessor = TextPreprocessor()
    texts = ["Python developer with FastAPI", "Python developer with FastAPI"]
    first = preprocessor.fit_transform(texts)
    second = preprocessor.fit_transform(texts)
    assert first[0]["clean_text"] == second[0]["clean_text"]
    assert preprocessor.cache_hits >= 2
