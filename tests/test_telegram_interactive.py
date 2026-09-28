from unittest.mock import patch, MagicMock
from src.notifier.telegram import TelegramNotifier
from src.notifier.telegram_bot import TelegramBotListener

def test_telegram_send_inline_keyboard():
    notifier = TelegramNotifier(bot_token="test:token", chat_id="123456789")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}

        buttons = [
            [{"text": "🚀 Kirim", "callback_data": "confirm_apply"}],
            [{"text": "❌ Batal", "callback_data": "cancel_apply"}]
        ]
        res = notifier.send_inline_keyboard("Konfirmasi pengiriman?", buttons)
        assert res is True
        assert mock_post.called

def test_handle_callback_query_confirm():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")
    listener.pending_actions["app_1"] = {
        "to_email": "hrd@tech.com",
        "company": "Tech Corp",
        "position": "Dev",
        "body": "Cover letter text",
        "cv_path": "cv.pdf",
        "cover_pdf": None
    }

    with patch.object(listener.mailer, "send_application") as mock_send, \
         patch.object(listener.tracker, "append_record"), \
         patch.object(listener.notifier, "send_message"), \
         patch.object(listener.notifier, "answer_callback_query"):

        handled = listener.handle_callback_query(
            query_id="query_123",
            chat_id="123456789",
            data="send:app_1"
        )
        assert handled is True
        assert mock_send.called
        assert "app_1" not in listener.pending_actions

def test_handle_callback_query_edits_message():
    listener = TelegramBotListener(bot_token="test:token", allowed_chat_id="123456789")
    listener.pending_actions["app_2"] = {
        "to_email": "hrd@tech2.com",
        "company": "Tech Corp 2",
        "position": "Dev",
        "body": "Cover letter text",
        "cv_path": "cv.pdf",
        "cover_pdf": None
    }
    with patch.object(listener.mailer, "send_application"), \
         patch.object(listener.tracker, "append_record"), \
         patch.object(listener.notifier, "edit_message_text") as mock_edit, \
         patch.object(listener.notifier, "answer_callback_query"):

        listener.handle_callback_query(
            query_id="q_123",
            chat_id="123456789",
            data="send:app_2",
            message_id=999
        )
        assert mock_edit.called
        assert mock_edit.call_args[0][1] == 999
