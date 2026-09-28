from datetime import datetime, timedelta
from src.security.date_filter import is_within_recency, extract_post_date

def test_relative_time_within_two_months():
    # Pass cases (<= 60 days)
    assert is_within_recency("Dibutuhkan Python Dev. Diposting 3 hari yang lalu")[0] is True
    assert is_within_recency("Urgent: Flutter Developer. Posted 2 weeks ago")[0] is True
    assert is_within_recency("Backend engineer wanted. 1 month ago")[0] is True
    assert is_within_recency("Software Tester. 2 months ago")[0] is True
    assert is_within_recency("Junior AI Engineer. Posted 5 days ago")[0] is True

def test_relative_time_older_than_two_months():
    # Reject cases (> 60 days / > 2 months)
    assert is_within_recency("Dibutuhkan Web Dev. Diposting 3 bulan yang lalu")[0] is False
    assert is_within_recency("Software Engineer. Posted 4 months ago")[0] is False
    assert is_within_recency("QA Automation. 6 months ago")[0] is False
    assert is_within_recency("Laravel Developer. 1 tahun yang lalu")[0] is False
    assert is_within_recency("Data Analyst. 2 years ago")[0] is False

def test_absolute_date_within_two_months():
    now = datetime.now()
    # 20 days ago
    date_recent = (now - timedelta(days=20)).strftime("%d %B %Y")
    assert is_within_recency(f"Lowongan IT Staff. Tanggal posting: {date_recent}")[0] is True

def test_absolute_date_older_than_two_months():
    now = datetime.now()
    # 90 days ago
    date_old = (now - timedelta(days=90)).strftime("%d %B %Y")
    assert is_within_recency(f"Lowongan IT Staff. Tanggal posting: {date_old}")[0] is False

def test_old_years_rejected():
    assert is_within_recency("Lowongan Frontend Dev Tahun 2023 di PT Sukses")[0] is False
    assert is_within_recency("Lowongan Backend Dev Tahun 2024 di PT Maju")[0] is False
