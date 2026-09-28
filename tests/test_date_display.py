from datetime import datetime, timedelta
from src.security.date_filter import get_post_date_display

def test_get_post_date_display_relative():
    assert "hari lalu" in get_post_date_display("Lowongan Python Dev. Diposting 3 hari yang lalu")
    assert "minggu lalu" in get_post_date_display("Hiring Flutter Engineer. Posted 2 weeks ago")
    assert "jam yang lalu" in get_post_date_display("Urgent: AI Specialist 5 hours ago")

def test_get_post_date_display_absolute():
    now = datetime.now()
    d_str = (now - timedelta(days=10)).strftime("%d %B %Y")
    display = get_post_date_display(f"Dibutuhkan Web Dev. Tanggal posting: {d_str}")
    assert "hari lalu" in display or d_str[:2] in display

def test_get_post_date_display_fallback():
    display = get_post_date_display("Lowongan Developer Startup")
    assert "WIB" in display or "Aktif" in display
