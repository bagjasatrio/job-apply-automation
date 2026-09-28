import imaplib
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Dict, Any, Optional
from src.classifier import classify_email_body
from src.models import JobStatus

class EmailHandler:
    def __init__(self, user: str, password: str, smtp_host: str = "smtp.gmail.com", imap_host: str = "imap.gmail.com"):
        self.user = user
        self.password = password
        self.smtp_host = smtp_host
        self.imap_host = imap_host

    def send_application(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        cv_path: str,
        extra_attachment_path: Optional[str] = None,
        html_body: Optional[str] = None
    ):
        if not os.path.exists(cv_path):
            raise FileNotFoundError(f"File CV tidak ditemukan di: {cv_path}")

        msg = MIMEMultipart("mixed")
        msg["From"] = self.user
        msg["To"] = to_email
        msg["Subject"] = subject

        # Bagian Teks & HTML Alternatif
        alt_part = MIMEMultipart("alternative")
        alt_part.attach(MIMEText(body_text, "plain", "utf-8"))
        if html_body:
            alt_part.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alt_part)

        # Lampiran 1: CV
        with open(cv_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(cv_path)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

        # Lampiran 2: Cover Letter PDF jika ada
        if extra_attachment_path and os.path.exists(extra_attachment_path):
            with open(extra_attachment_path, "rb") as f:
                part2 = MIMEBase("application", "pdf")
                part2.set_payload(f.read())
            encoders.encode_base64(part2)
            fname2 = os.path.basename(extra_attachment_path)
            part2.add_header("Content-Disposition", f'attachment; filename="{fname2}"')
            msg.attach(part2)

        with smtplib.SMTP_SSL(self.smtp_host, 465) as server:
            server.login(self.user, self.password)
            server.send_message(msg)

    def send_follow_up(self, to_email: str, subject: str, body_text: str):
        msg = MIMEMultipart()
        msg["From"] = self.user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain"))

        with smtplib.SMTP_SSL(self.smtp_host, 465) as server:
            server.login(self.user, self.password)
            server.send_message(msg)

    def check_inbox_updates(self, applied_companies: List[str]) -> List[Dict[str, Any]]:
        results = []
        if not self.user or not self.password:
            return results

        mail = imaplib.IMAP4_SSL(self.imap_host)
        mail.login(self.user, self.password)
        mail.select("inbox")

        status, message_numbers = mail.search(None, "ALL")
        if status != "OK" or not message_numbers or not message_numbers[0]:
            mail.logout()
            return results

        # Ambil pesan-pesan terbaru (maksimal 50 email terakhir)
        id_list = message_numbers[0].split()
        recent_ids = id_list[-50:] if len(id_list) > 50 else id_list

        for num in reversed(recent_ids):
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK" or not msg_data:
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = str(msg.get("Subject", "") or "")
                    sender = str(msg.get("From", "") or "")
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode(errors="ignore")
                                break
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors="ignore")

                    # Cocokkan nama perusahaan pada subject, sender, atau isi email
                    matched_comp = None
                    for comp in applied_companies:
                        if not comp.strip():
                            continue
                        c_lower = comp.strip().lower()
                        if c_lower in subject.lower() or c_lower in sender.lower() or c_lower in body.lower():
                            matched_comp = comp
                            break

                    if matched_comp:
                        detected_status, conf = classify_email_body(body or subject)
                        results.append({
                            "company": matched_comp,
                            "detected_status": detected_status,
                            "confidence": conf,
                            "subject": subject,
                            "sender": sender,
                            "snippet": (body[:150] + "...") if len(body) > 150 else body
                        })

        mail.logout()
        return results
