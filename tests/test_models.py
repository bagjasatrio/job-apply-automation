from src.models import ApplicationRecord, JobStatus

def test_application_record_creation():
    record = ApplicationRecord(
        company="PT Maju Jaya",
        position="Backend Engineer",
        channel="Email",
        status=JobStatus.APPLIED,
        contact="hrd@majujaya.com",
        notes="Sent initial email"
    )
    assert record.company == "PT Maju Jaya"
    assert record.position == "Backend Engineer"
    assert record.channel == "Email"
    assert record.status == JobStatus.APPLIED
    assert record.contact == "hrd@majujaya.com"
