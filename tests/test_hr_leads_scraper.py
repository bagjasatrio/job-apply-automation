from unittest.mock import patch, MagicMock
from src.scraper.hr_leads_scraper import HRLeadsScraper

def test_hr_leads_scraper_mock():
    scraper = HRLeadsScraper(headless=True)
    with patch("src.scraper.hr_leads_scraper.sync_playwright") as mock_playwright, \
         patch.object(scraper.matcher, "match") as mock_match:

        mock_page = MagicMock()
        mock_page.inner_text.return_value = "Hubungi recruitment@digitaltech.com untuk melamar posisi Fullstack Python Engineer."
        mock_page.query_selector_all.return_value = []

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_p = MagicMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_p

        mock_match.return_value = {
            "score": 85,
            "decision": "APPLY",
            "matched_skills": ["Python", "Fullstack"],
            "missing_skills": [],
            "reason": "Kandidat memiliki skill python dan web."
        }

        results = scraper.search_and_scrape(custom_query="hiring python", max_results=1)

        assert len(results) == 1
        assert results[0]["email"] == "recruitment@digitaltech.com"
        assert results[0]["match_score"] == 85
        assert results[0]["decision"] == "APPLY"
