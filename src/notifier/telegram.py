import os
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token if bot_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = chat_id if chat_id is not None else os.getenv("TELEGRAM_CHAT_ID", "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.is_configured:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            return res.status_code == 200 and res.json().get("ok", False)
        except Exception:
            return False

    def send_inline_keyboard(self, text: str, buttons: list) -> bool:
        if not self.is_configured:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": buttons
            }
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            return res.status_code == 200 and res.json().get("ok", False)
        except Exception:
            return False

    def answer_callback_query(self, callback_query_id: str, text: str = "") -> bool:
        if not self.is_configured:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            return res.status_code == 200 and res.json().get("ok", False)
        except Exception:
            return False

    def edit_message_text(self, chat_id: str, message_id: int, text: str, buttons: Optional[list] = None) -> bool:
        if not self.is_configured:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if buttons is not None:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        try:
            res = requests.post(url, json=payload, timeout=10)
            return res.status_code == 200 and res.json().get("ok", False)
        except Exception:
            return False

    def send_document(self, file_path: str, caption: str = "") -> bool:
        if not self.is_configured or not os.path.exists(file_path):
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        data = {
            "chat_id": self.chat_id,
            "caption": caption,
            "parse_mode": "HTML"
        }
        try:
            with open(file_path, "rb") as f:
                files = {"document": (os.path.basename(file_path), f)}
                res = requests.post(url, data=data, files=files, timeout=20)
                return res.status_code == 200 and res.json().get("ok", False)
        except Exception:
            return False

    def notify_application_sent(self, company: str, position: str, channel: str, notes: str = ""):
        msg = (
            f"🚀 <b>LAMARAN TERKIRIM</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏢 <b>Perusahaan:</b> {company}\n"
            f"💼 <b>Posisi:</b> {position}\n"
            f"📡 <b>Channel:</b> {channel}\n"
        )
        if notes:
            msg += f"📝 <b>Catatan:</b> {notes}\n"
        msg += f"📊 Tercatat otomatis di Google Sheets."
        self.send_message(msg)

    def notify_interview_detected(self, company: str, subject: str, snippet: str = ""):
        msg = (
            f"🎉 <b>UNDANGAN INTERVIEW / TES TEKNIS!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏢 <b>Perusahaan:</b> {company}\n"
            f"📬 <b>Subject:</b> {subject}\n"
        )
        if snippet:
            msg += f"💬 <b>Cuplikan:</b> {snippet[:200]}...\n"
        msg += f"\n👉 <i>Segera periksa email inbox Anda untuk konfirmasi jadwal!</i>"
        self.send_message(msg)

    def notify_offering_detected(self, company: str, subject: str, snippet: str = ""):
        msg = (
            f"🏆 <b>OFFERING LETTER DITERIMA!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏢 <b>Perusahaan:</b> {company}\n"
            f"📬 <b>Subject:</b> {subject}\n"
        )
        if snippet:
            msg += f"💬 <b>Cuplikan:</b> {snippet[:200]}...\n"
        msg += f"\n🎉 <i>Selamat! Surat penawaran kerja telah masuk.</i>"
        self.send_message(msg)

    def notify_rejection_detected(self, company: str, subject: str):
        msg = (
            f"ℹ️ <b>UPDATE STATUS LAMARAN</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏢 <b>Perusahaan:</b> {company}\n"
            f"📬 <b>Status:</b> Ditolak (Rejected)\n"
            f"Subject: {subject}\n"
            f"Tetap semangat, sistem terus mencari peluang lain."
        )
        self.send_message(msg)
