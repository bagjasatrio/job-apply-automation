from unittest.mock import MagicMock, patch
from src.mailer import EmailHandler
from src.models import JobStatus

def test_check_inbox_updates_match():
    handler = EmailHandler("test@gmail.com", "pass", "smtp.gmail.com", "imap.gmail.com")
    
    mock_mail = MagicMock()
    mock_mail.search.return_value = ("OK", [b"1"])
    
    # Mock raw RFC822 email message
    raw_email = (
        b"From: recruiter@shopee.com\r\n"
        b"Subject: Invitation to Technical Interview - Shopee\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Dear Candidate, please join Google Meet for technical test."
    )
    mock_mail.fetch.return_value = ("OK", [(b"1", raw_email)])
    
    with patch("imaplib.IMAP4_SSL", return_value=mock_mail):
        updates = handler.check_inbox_updates(applied_companies=["Shopee"])
        
        assert len(updates) == 1
        assert updates[0]["company"] == "Shopee"
        assert updates[0]["detected_status"] == JobStatus.ON_PROGRESS
        assert "Interview" in updates[0]["subject"]
