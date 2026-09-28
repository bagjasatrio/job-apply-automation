from src.sheets import CSVTracker
from src.models import ApplicationRecord, JobStatus

def test_anti_duplicate_check(tmp_path):
    csv_file = tmp_path / "test_dup.csv"
    tracker = CSVTracker(str(csv_file))

    rec = ApplicationRecord(
        company="Shopee Indonesia",
        position="Backend Engineer",
        channel="Email",
        status=JobStatus.APPLIED,
        contact="recruitment@shopee.com"
    )
    tracker.append_record(rec)

    # Sama nama perusahaan (case-insensitive)
    assert tracker.is_already_applied("shopee indonesia") is True
    assert tracker.is_already_applied("Shopee Indonesia") is True

    # Sama kontak email
    assert tracker.is_already_applied("Other Company", contact_or_email="recruitment@shopee.com") is True

    # Belum pernah dilamar
    assert tracker.is_already_applied("Traveloka", contact_or_email="hr@traveloka.com") is False

def test_daily_apply_count(tmp_path):
    csv_file = tmp_path / "test_quota.csv"
    tracker = CSVTracker(str(csv_file))

    assert tracker.get_today_apply_count() == 0

    rec = ApplicationRecord(
        company="PT Alpha",
        position="Software Engineer",
        channel="LinkedIn",
        status=JobStatus.APPLIED
    )
    tracker.append_record(rec)

    assert tracker.get_today_apply_count() == 1
