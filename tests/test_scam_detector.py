from src.security.scam_detector import ScamDetector

def test_detect_travel_reimbursement_scam():
    detector = ScamDetector()
    sample_text = """
    Panggilan Tes Wawancara PT Pertamina Persero.
    Peserta wajib melakukan reservasi tiket pesawat dan hotel melalui biro perjalanan Travel Tourindo.
    Seluruh biaya akomodasi akan diganti (reimburse) setibanya di lokasi tes.
    """
    is_scam, reason = detector.is_suspicious_lead("PT Pertamina", "Staff IT", "pertamina.recruitment@gmail.com", sample_text)
    assert is_scam is True
    assert "travel" in reason.lower() or "biaya" in reason.lower()

def test_detect_bumn_free_email_spoof():
    detector = ScamDetector()
    is_scam, reason = detector.is_suspicious_lead("PT Telkom Indonesia", "Software Engineer", "recruitment.telkom@gmail.com", "Lowongan kerja resmi")
    assert is_scam is True
    assert "email" in reason.lower() or "bumn" in reason.lower()

def test_detect_like_and_share_commission_scam():
    detector = ScamDetector()
    text = "Kerja paruh waktu online, cukup like video tiktok dan pesanan shopee, komisi 500rb per hari tanpa pengalaman."
    is_scam, reason = detector.is_suspicious_lead("Online Freelance", "Part Time Reviewer", "recruiter@gmail.com", text)
    assert is_scam is True
    assert "komisi" in reason.lower() or "paruh waktu" in reason.lower() or "scam" in reason.lower()

def test_valid_legitimate_job():
    detector = ScamDetector()
    text = "PT Solusi Teknologi Nusantara membuka lowongan Backend Developer. Kirim CV dan portofolio ke career@solusitekno.co.id. Tidak dipungut biaya apapun."
    is_scam, reason = detector.is_suspicious_lead("PT Solusi Teknologi Nusantara", "Backend Developer", "career@solusitekno.co.id", text)
    assert is_scam is False
