import os
from src.tailor.resume_tailor import ResumeTailor
from src.templates.email_styler import render_html_cover_letter
from src.tailor.cover_letter_pdf import build_cover_letter_pdf

def test_resume_english_no_ai_slop(tmp_path):
    tailor = ResumeTailor(output_dir=str(tmp_path))
    pdf_path = tailor.build_tailored_resume("TechCorp", "Software Engineer", "Need Python and Flutter", lang="en")

    assert os.path.exists(pdf_path)
    assert "Resume_Muhammad_Bagja_Satrio" in os.path.basename(pdf_path)

def test_resume_indonesian_naming(tmp_path):
    tailor = ResumeTailor(output_dir=str(tmp_path))
    pdf_path = tailor.build_tailored_resume("TechCorp", "Software Engineer", "Butuh Python dan Laravel", lang="id")

    assert os.path.exists(pdf_path)
    assert "CV_Muhammad_Bagja_Satrio" in os.path.basename(pdf_path)

def test_email_styler_language_consistency_english():
    html = render_html_cover_letter(
        body_text="Dear Team,\n\nI am applying for this role.",
        position="Software Engineer",
        company="GlobalTech",
        lang="en"
    )
    assert "Target Position:" in html
    assert "at GlobalTech" in html
    assert "Education:" in html
    assert "View Portfolio Website" in html
    assert "LinkedIn Profile" in html
    assert "Target Posisi:" not in html
    assert "Buka Website Portofolio" not in html

def test_email_styler_language_consistency_indonesian():
    html = render_html_cover_letter(
        body_text="Dengan hormat,\n\nSaya melamar posisi ini.",
        position="Software Engineer",
        company="LokalTech",
        lang="id"
    )
    assert "Target Posisi:" in html
    assert "di LokalTech" in html
    assert "Pendidikan:" in html
    assert "Buka Website Portofolio" in html
    assert "Target Position:" not in html
    assert "View Portfolio Website" not in html

def test_resume_summary_maintains_required_trait_id():
    tailor = ResumeTailor()
    res = tailor.extract_keywords_and_summary("PT Nusantara", "Fullstack Developer", "", lang="id")
    summary = res["summary"]
    assert "Mampu bekerja sama dalam tim" in summary
    assert "mudah beradaptasi dengan lingkungan dan tantangan baru" in summary
    assert "berkomitmen untuk bekerja secara profesional dan bertanggung jawab" in summary

def test_resume_summary_maintains_required_trait_en():
    tailor = ResumeTailor()
    res = tailor.extract_keywords_and_summary("Global Systems", "Software Engineer", "", lang="en")
    summary = res["summary"]
    assert "collaborate" in summary.lower() or "team" in summary.lower()
    assert "adapt" in summary.lower()

