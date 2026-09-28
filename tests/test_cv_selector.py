import pytest
from src.cv_selector import CVManager, detect_language

def test_detect_language_indonesian():
    text = "Kami sedang mencari Fullstack Developer yang berpengalaman dalam pengembangan web dan REST API."
    assert detect_language(text) == "id"

def test_detect_language_english():
    text = "We are seeking a senior AI Engineer to build LLM pipelines and integrate multi-provider APIs."
    assert detect_language(text) == "en"

def test_detect_language_with_id_domain():
    # Sinyal domain .id atau context Indonesia
    text = "it Terik Dibutuhkan segera tenaga IT untuk penempatan kantor"
    assert detect_language(text, email_or_domain="hr@terik.id") == "id"

def test_detect_language_fallback_zone_id():
    text = "it Terik"
    assert detect_language(text, default_lang="id", email_or_domain="hr@terik.id") == "id"

def test_cv_manager_select_cv(tmp_path):
    cv_id = tmp_path / "cv_id.pdf"
    cv_en = tmp_path / "cv_en.pdf"
    cv_id.write_bytes(b"%PDF-id")
    cv_en.write_bytes(b"%PDF-en")

    manager = CVManager(cv_id_path=str(cv_id), cv_en_path=str(cv_en))

    assert manager.get_cv_for_text("Lowongan kerja Fullstack Web Developer") == str(cv_id)
    assert manager.get_cv_for_text("Hiring Junior Software Engineer in Jakarta") == str(cv_en)
    assert manager.get_cv(lang="id") == str(cv_id)
    assert manager.get_cv(lang="en") == str(cv_en)
