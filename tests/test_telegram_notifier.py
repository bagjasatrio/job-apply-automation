from unittest.mock import patch, MagicMock
from src.notifier.telegram import TelegramNotifier

def test_telegram_send_message_disabled():
    # If no token, should fail silently without crashing
    notifier = TelegramNotifier(bot_token="", chat_id="")
    assert notifier.send_message("Test message") is False

def test_telegram_send_message_success():
    notifier = TelegramNotifier(bot_token="12345:dummy_token", chat_id="987654")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}

        success = notifier.send_message("🚨 Test Alert")
        assert success is True
        assert mock_post.called

def test_notify_interview_detected():
    notifier = TelegramNotifier(bot_token="12345:dummy_token", chat_id="987654")
    with patch.object(notifier, "send_message") as mock_send:
        notifier.notify_interview_detected("Shopee", "Technical Interview Invite", "Join meet at 10 AM")
        assert mock_send.called
        call_arg = mock_send.call_args[0][0]
        assert "Shopee" in call_arg
        assert "INTERVIEW" in call_arg
