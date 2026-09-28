from unittest.mock import patch, MagicMock
from src.portals.linkedin import LinkedInBot

def test_linkedin_balanced_apply():
    bot = LinkedInBot()
    with patch.object(bot, "apply_easy_jobs") as mock_apply:
        # Mock 2 for ID, 2 for Global
        mock_apply.side_effect = [
            [MagicMock(company="Indo Corp 1"), MagicMock(company="Indo Corp 2")],
            [MagicMock(company="US Remote 1"), MagicMock(company="EU Remote 2")]
        ]

        results = bot.apply_balanced_jobs(keyword="Python Developer", total_apply=4, headless=True)

        assert len(results) == 4
        assert mock_apply.call_count == 2
        # Check first call: location='Indonesia'
        first_call_args = mock_apply.call_args_list[0]
        assert first_call_args.kwargs.get("location") == "Indonesia"
        assert first_call_args.kwargs.get("remote_only") is False

        # Check second call: location='Worldwide', remote_only=True
        second_call_args = mock_apply.call_args_list[1]
        assert second_call_args.kwargs.get("location") == "Worldwide"
        assert second_call_args.kwargs.get("remote_only") is True
