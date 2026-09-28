from unittest.mock import patch, MagicMock
from src.scraper.hr_leads_scraper import HRLeadsScraper

def test_hr_leads_scraper_50_50_split():
    scraper = HRLeadsScraper(headless=True)
    with patch.object(scraper, "_scrape_query_list") as mock_scrape, \
         patch.object(scraper.matcher, "match") as mock_match, \
         patch.object(scraper.scam_detector, "is_suspicious_lead") as mock_scam:

        mock_scam.return_value = (False, "")
        mock_match.return_value = {
            "score": 85,
            "decision": "APPLY",
            "matched_skills": ["Python", "AI"],
            "missing_skills": [],
            "reason": "Cocok"
        }

        # Mock result for ID and Global
        mock_scrape.side_effect = [
            # Indonesia pool
            [
                {"email": "hr@indo1.co.id", "company": "Indo Tech 1", "position": "Software Engineer", "zone": "Indonesia"},
                {"email": "hr@indo2.co.id", "company": "Indo Tech 2", "position": "Software Engineer", "zone": "Indonesia"}
            ],
            # Global remote pool
            [
                {"email": "jobs@usglobal.com", "company": "Global Corp 1", "position": "Remote Python Dev", "zone": "Global Remote"},
                {"email": "careers@sgremote.io", "company": "Global Corp 2", "position": "Remote AI Dev", "zone": "Global Remote"}
            ]
        ]

        leads = scraper.search_balanced_leads(custom_position="Software Engineer", total_limit=4)

        assert len(leads) == 4
        id_leads = [l for l in leads if l.get("zone") == "Indonesia"]
        global_leads = [l for l in leads if l.get("zone") == "Global Remote"]

        assert len(id_leads) == 2
        assert len(global_leads) == 2
