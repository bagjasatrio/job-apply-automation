from unittest.mock import MagicMock, patch
from src.scheduler import JobAutomationScheduler
from src.security.lead_cache import LeadCache

def test_autonomous_hunt_execution(tmp_path):
    mock_tracker = MagicMock()
    mock_tracker.is_already_applied.return_value = False
    mock_mailer = MagicMock()
    mock_notifier = MagicMock()
    mock_notifier.send_inline_keyboard.return_value = True

    test_cache = LeadCache(file_path=str(tmp_path / "test_seen.json"))

    scheduler = JobAutomationScheduler(
        tracker=mock_tracker,
        mailer=mock_mailer,
        notifier=mock_notifier,
        hunt_interval_seconds=3600,
        auto_hunt_enabled=True,
        lead_cache=test_cache
    )

    dummy_leads = [
        {
            "email": "career@barutech.id",
            "company": "Baru Tech",
            "position": "Python Developer",
            "snippet": "Dibutuhkan segera Python Dev di Jakarta WFO",
            "source_url": "https://barutech.id/jobs",
            "match_score": 85,
            "decision": "APPLY",
            "matched_skills": ["Python", "FastAPI"],
            "zone": "Indonesia"
        }
    ]

    with patch("src.scheduler.HRLeadsScraper") as mock_scraper_cls:
        mock_instance = MagicMock()
        mock_instance.search_balanced_leads.return_value = dummy_leads
        mock_scraper_cls.return_value = mock_instance

        count = scheduler.execute_autonomous_hunt()
        assert count == 1
        assert mock_notifier.send_inline_keyboard.called
        assert test_cache.is_lead_seen(email="career@barutech.id") is True

        # Running again should skip because it is now in cache
        second_count = scheduler.execute_autonomous_hunt()
        assert second_count == 0

def test_auto_hunt_toggle():
    mock_tracker = MagicMock()
    mock_mailer = MagicMock()
    mock_notifier = MagicMock()

    scheduler = JobAutomationScheduler(
        tracker=mock_tracker,
        mailer=mock_mailer,
        notifier=mock_notifier
    )
    assert scheduler.auto_hunt_enabled is True
    scheduler.set_auto_hunt(False)
    assert scheduler.auto_hunt_enabled is False
    assert scheduler.execute_autonomous_hunt() == 0
