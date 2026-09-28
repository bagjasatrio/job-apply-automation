from unittest.mock import patch, MagicMock
from src.target_roles import CORE_JOB_TITLES
from src.notifier.telegram_bot import TelegramBotListener

def test_portal_menu_unrestricted():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")
    with patch.object(listener.notifier, "send_inline_keyboard") as mock_keyboard:
        handled = listener.handle_command("123456789", "/portal")
        assert handled is True
        assert mock_keyboard.called
        buttons = mock_keyboard.call_args[0][1]
        button_texts = [b["text"] for row in buttons for b in row]

        # Verify NO separated clusters in the menu
        assert not any("Kluster" in t for t in button_texts)

        # Verify all portals target ALL 35 roles
        assert any("LinkedIn" in t and "35 Posisi" in t for t in button_texts)
        assert any("Glints" in t and "35 Posisi" in t for t in button_texts)
        assert any("Jobstreet" in t and "35 Posisi" in t for t in button_texts)
        assert any("SEMUA PORTAL" in t for t in button_texts)

def test_portal_execution_all_roles():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")
    with patch("src.portals.linkedin.LinkedInBot.apply_balanced_jobs") as mock_apply, \
         patch.object(listener.notifier, "send_message"):
        mock_apply.return_value = []
        handled = listener.handle_command("123456789", "/portal linkedin all 5")
        assert handled is True
        assert mock_apply.called
        assert mock_apply.call_args[1]["keyword"] == "all"
