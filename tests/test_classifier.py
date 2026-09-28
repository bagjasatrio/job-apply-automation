from src.classifier import classify_email_body
from src.models import JobStatus

def test_classifier_rejected():
    body = "Terima kasih atas minat Anda di PT Maju Mundur. Sayangnya saat ini kami memutuskan untuk tidak melanjutkan proses rekrutmen."
    status, confidence = classify_email_body(body)
    assert status == JobStatus.REJECTED
    assert confidence > 0.8

def test_classifier_interview():
    body = "Dear Candidate, we would like to invite you for a Technical Interview via Google Meet on Friday."
    status, confidence = classify_email_body(body)
    assert status == JobStatus.ON_PROGRESS
    assert confidence > 0.8

def test_classifier_offering():
    body = "Selamat! Kami ingin memberikan Surat Penawaran Kerja (Offering Letter) untuk posisi Software Engineer."
    status, confidence = classify_email_body(body)
    assert status == JobStatus.OFFERING
    assert confidence > 0.8
