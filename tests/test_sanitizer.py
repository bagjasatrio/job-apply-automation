from src.templates.text_sanitizer import clean_markdown_slop, extract_company_from_email

def test_clean_markdown_slop_removes_asterisks():
    text = "Saya mengembangkan **ClipMax Mobile** menggunakan **Flutter/Dart** dan **Whisper.cpp**."
    cleaned = clean_markdown_slop(text)
    assert "**" not in cleaned
    assert "ClipMax Mobile" in cleaned
    assert "Flutter/Dart" in cleaned

def test_clean_markdown_slop_removes_placeholders():
    text = "Best regards,\n**Muhammad Bagja Satrio**\n[Your Phone Number] | [Your Email] | [Your LinkedIn URL]"
    cleaned = clean_markdown_slop(text)
    assert "[Your Phone Number]" not in cleaned
    assert "+62 812-2068-4832" in cleaned
    assert "muhammad.bagjasatrio28@gmail.com" in cleaned

def test_extract_company_from_email():
    assert extract_company_from_email("hrd@genesysindonesia.com") == "Genesys Indonesia"
    assert extract_company_from_email("career@game-consign.com") == "Game Consign"
    assert extract_company_from_email("recruitment@tokopedia.com") == "Tokopedia"
    # Fallback for gmail
    assert extract_company_from_email("recruitment.pertamina@gmail.com", fallback="Pertamina") == "Pertamina"
