import os
from unittest.mock import MagicMock, patch
from src.backup import create_backup
from src.notifier.telegram import TelegramNotifier

def test_create_backup(tmp_path):
    mock_tracker = MagicMock()
    mock_tracker.get_tracked_companies.return_value = [
        {"Company": "Shopee", "Position": "Dev", "Channel": "Email", "Status": "Applied"}
    ]

    backup_file = create_backup(mock_tracker, output_dir=str(tmp_path))

    assert os.path.exists(backup_file)
    assert backup_file.endswith(".csv")
    content = open(backup_file, "r", encoding="utf-8").read()
    assert "Shopee" in content

def test_telegram_send_document():
    notifier = TelegramNotifier(bot_token="test:token", chat_id="123456789")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}

        # create a dummy file
        dummy_file = "dummy_backup.csv"
        with open(dummy_file, "w") as f:
            f.write("test")

        try:
            res = notifier.send_document(dummy_file, caption="Test Backup")
            assert res is True
            assert mock_post.called
        finally:
            if os.path.exists(dummy_file):
                os.remove(dummy_file)
