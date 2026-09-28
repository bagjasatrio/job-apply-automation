from unittest.mock import patch
from src.scraper.hr_leads_scraper import HRLeadsScraper

def test_filter_and_score_drops_under_50():
    scraper = HRLeadsScraper(headless=True)
    raw_leads = [
        {"email": "good@tech.com", "company": "Good Tech", "position": "Python Dev", "snippet": "Need python dev"},
        {"email": "bad@tech.com", "company": "Bad Match", "position": "Janitor", "snippet": "Cleaning service"}
    ]

    with patch.object(scraper.scam_detector, "is_suspicious_lead", return_value=(False, "")), \
         patch.object(scraper.matcher, "match") as mock_match:

        def mock_match_fn(company, position, job_description):
            if "Good" in company:
                return {"score": 65, "decision": "APPLY", "matched_skills": ["Python"], "missing_skills": [], "reason": "Cocok"}
            else:
                return {"score": 20, "decision": "SKIP", "matched_skills": [], "missing_skills": ["Tech"], "reason": "Tidak cocok"}

        mock_match.side_effect = mock_match_fn

        results = scraper._filter_and_score(raw_leads, min_score=50)

        assert len(results) == 1
        assert results[0]["email"] == "good@tech.com"
        assert results[0]["match_score"] == 65
