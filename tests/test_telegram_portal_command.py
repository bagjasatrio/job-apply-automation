from unittest.mock import patch, MagicMock
from src.notifier.telegram_bot import TelegramBotListener

def test_telegram_portal_menu_buttons():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")
    with patch.object(listener.notifier, "send_inline_keyboard") as mock_keyboard:
        handled = listener.handle_command("123456789", "/portal")
        assert handled is True
        assert mock_keyboard.called
        text = mock_keyboard.call_args[0][0]
        buttons = mock_keyboard.call_args[0][1]
        assert "PORTAL" in text
        assert any("LinkedIn" in b["text"] for row in buttons for b in row)
        assert any("35 Posisi" in b["text"] for row in buttons for b in row)

def test_telegram_run_portal_bot_custom_role():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")
    with patch("src.portals.linkedin.LinkedInBot.apply_easy_jobs") as mock_apply, \
         patch.object(listener.notifier, "send_message"):
        mock_apply.return_value = []
        handled = listener.handle_command("123456789", "/portal linkedin_id AI Engineer 2")
        assert handled is True
        assert mock_apply.called
        assert mock_apply.call_args[1]["keyword"] == "AI Engineer"

def test_telegram_run_portal_bot_cluster_rotation():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")
    with patch("src.portals.linkedin.LinkedInBot.apply_balanced_jobs") as mock_apply, \
         patch.object(listener.notifier, "send_message"):
        mock_apply.return_value = []
        handled = listener.handle_command("123456789", "/portal linkedin all 4")
        assert handled is True
        assert mock_apply.called
        # Keyword should be dynamically constructed from target roles
        kw = mock_apply.call_args[1]["keyword"]
        assert len(kw) > 0
