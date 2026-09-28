from src.scraper.email_extractor import extract_hr_emails_and_leads

def test_extract_snippet_surrounding_context():
    long_text = (
        "Home Page About Us Services Contact\n"
        "Lowongan Kerja: Dibutuhkan segera Backend Developer yang menguasai Python, FastAPI, dan PostgreSQL. "
        "Kirim CV lengkap dan portofolio Anda ke recruitment@startuptech.id sebelum akhir bulan. "
        "Gaji dan benefit kompetitif.\n"
        "Footer Copyright 2026 All Rights Reserved."
    )
    leads = extract_hr_emails_and_leads(long_text, source_url="https://startuptech.id/careers")

    assert len(leads) == 1
    assert leads[0]["email"] == "recruitment@startuptech.id"
    assert leads[0]["source_url"] == "https://startuptech.id/careers"
    # Snippet should contain the relevant requirements, not just "Home Page About Us"
    assert "FastAPI" in leads[0]["snippet"]
    assert "Python" in leads[0]["snippet"]
