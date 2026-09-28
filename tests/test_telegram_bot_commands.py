from unittest.mock import patch, MagicMock
from src.notifier.telegram_bot import TelegramBotListener

def test_handle_command_status():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")

    with patch.object(listener.notifier, "send_message") as mock_send, \
         patch.object(listener.tracker, "get_tracked_companies", return_value=[
             {"Company": "Shopee", "Position": "Backend", "Channel": "Email", "Status": "On Progress"}
         ]):

        handled = listener.handle_command(chat_id="123456789", text="/status")
        assert handled is True
        assert mock_send.called
        msg = mock_send.call_args[0][0]
        assert "Shopee" in msg or "ANALYTICS" in msg or "Total" in msg

def test_handle_unauthorized_chat():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")
    handled = listener.handle_command(chat_id="999999", text="/status")
    assert handled is False

def test_handle_command_autohunt():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")

    with patch.object(listener.notifier, "send_message") as mock_send:
        # 1. Status
        assert listener.handle_command("123456789", "/autohunt") is True
        assert "AUTONOMOUS 24/7" in mock_send.call_args[0][0]

        # 2. Toggle off
        assert listener.handle_command("123456789", "/autohunt off") is True
        assert listener.scheduler.auto_hunt_enabled is False

        # 3. Toggle on
        assert listener.handle_command("123456789", "/autohunt on") is True
        assert listener.scheduler.auto_hunt_enabled is True

        # 4. Change interval
        assert listener.handle_command("123456789", "/autohunt interval 45") is True
        assert listener.scheduler.hunt_interval_seconds == 45 * 60
