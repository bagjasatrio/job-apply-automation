import os
from src.security.lead_cache import LeadCache

def test_lead_cache_persistence(tmp_path):
    cache_file = tmp_path / "seen_leads.json"
    cache = LeadCache(file_path=str(cache_file))

    assert cache.is_lead_seen(email="hrd@tech.com") is False
    assert cache.is_lead_seen(url="https://tech.com/job/1") is False

    cache.mark_lead_seen(email="hrd@tech.com", url="https://tech.com/job/1", company="Tech Corp", position="Dev")

    assert cache.is_lead_seen(email="hrd@tech.com") is True
    assert cache.is_lead_seen(email="HRD@TECH.COM") is True
    assert cache.is_lead_seen(url="https://tech.com/job/1") is True

    # Reload from disk
    new_cache = LeadCache(file_path=str(cache_file))
    assert new_cache.is_lead_seen(email="hrd@tech.com") is True
