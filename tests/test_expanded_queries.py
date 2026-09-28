from unittest.mock import patch
from src.scraper.hr_leads_scraper import HRLeadsScraper, EXPANDED_INDONESIA_QUERIES, EXPANDED_GLOBAL_REMOTE_QUERIES

def test_expanded_queries_coverage():
    # Make sure Indonesia queries cover various IT fields
    id_str = " ".join(EXPANDED_INDONESIA_QUERIES).lower()
    assert "teknik informatika" in id_str
    assert "fresh graduate" in id_str
    assert "web developer" in id_str
    assert "frontend" in id_str
    assert "backend" in id_str
    assert "qa" in id_str or "tester" in id_str
    assert "it staff" in id_str or "it programmer" in id_str

    # Make sure Global queries cover entry level, remote, and diversified tech roles
    global_str = " ".join(EXPANDED_GLOBAL_REMOTE_QUERIES).lower()
    assert "junior" in global_str or "entry level" in global_str
    assert "worldwide remote" in global_str or "work from anywhere" in global_str
    assert "frontend" in global_str
    assert "backend" in global_str
