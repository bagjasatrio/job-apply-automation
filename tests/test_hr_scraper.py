from src.scraper.email_extractor import extract_hr_emails_and_leads

def test_extract_hr_emails():
    sample_text = """
    PT Inovasi Digital sedang membuka lowongan Backend Python Developer.
    Silakan kirimkan CV Anda ke recruitment@inovasidigital.co.id atau hrd.inovasi@gmail.com dengan subject Backend Dev.
    Info lebih lanjut hubungi support@inovasidigital.co.id (jangan kirim CV ke sini).
    """
    leads = extract_hr_emails_and_leads(sample_text, default_company="PT Inovasi Digital", default_position="Backend Developer")
    emails = [l["email"] for l in leads]

    assert "recruitment@inovasidigital.co.id" in emails
    assert "hrd.inovasi@gmail.com" in emails
    assert "support@inovasidigital.co.id" not in emails

def test_extract_filters_invalid_emails():
    text = "Kunjungi https://schema.org/JobPosting image test@png.jpg w3c@w3.org"
    leads = extract_hr_emails_and_leads(text)
    assert len(leads) == 0
