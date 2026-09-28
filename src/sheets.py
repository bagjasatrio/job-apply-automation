import os
import csv
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests
from src.models import ApplicationRecord, JobStatus

HEADERS = ["Company", "Position", "Channel", "Contact", "Date Applied", "Status", "Notes"]

class BaseTracker:
    def get_tracked_companies(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def is_already_applied(self, company: str, contact_or_email: str = "") -> bool:
        records = self.get_tracked_companies()
        target_comp = company.strip().lower()
        target_contact = contact_or_email.strip().lower() if contact_or_email else ""

        for r in records:
            comp = str(r.get("Company", "")).strip().lower()
            contact = str(r.get("Contact", "")).strip().lower()

            if target_comp and comp == target_comp:
                return True
            if target_contact and contact and (target_contact in contact or contact in target_contact):
                return True
        return False

    def get_today_apply_count(self) -> int:
        records = self.get_tracked_companies()
        today_str = datetime.now().strftime("%Y-%m-%d")
        count = 0
        for r in records:
            date_val = str(r.get("Date Applied", ""))
            if date_val.startswith(today_str):
                count += 1
        return count

class CSVTracker(BaseTracker):
    """Local CSV Tracker: tanpa kredensial, tanpa akun Google, file bisa dibuka di Excel / Google Sheets."""
    def __init__(self, file_path: str = "applications.csv"):
        self.file_path = os.path.abspath(file_path)
        self.init_headers()

    def init_headers(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(HEADERS)

    def append_record(self, record: ApplicationRecord):
        self.init_headers()
        row = [
            record.company,
            record.position,
            record.channel,
            record.contact or "",
            record.date_applied.strftime("%Y-%m-%d %H:%M:%S"),
            record.status.value,
            record.notes
        ]
        with open(self.file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def get_tracked_companies(self) -> List[Dict[str, Any]]:
        self.init_headers()
        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def update_status(self, company: str, new_status: JobStatus, note: str = "") -> bool:
        records = self.get_tracked_companies()
        updated = False
        for row in records:
            if row.get("Company", "").strip().lower() == company.strip().lower():
                row["Status"] = new_status.value
                if note:
                    curr = row.get("Notes", "")
                    row["Notes"] = f"{curr} | {note}".strip(" |")
                updated = True
                break

        if updated:
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=HEADERS)
                writer.writeheader()
                writer.writerows(records)
        return updated

class WebhookTracker(BaseTracker):
    """Google Apps Script Webhook: update Google Sheet via HTTP URL tanpa credential/service account JSON."""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def append_record(self, record: ApplicationRecord):
        payload = {
            "action": "append",
            "company": record.company,
            "position": record.position,
            "channel": record.channel,
            "contact": record.contact or "",
            "date_applied": record.date_applied.strftime("%Y-%m-%d %H:%M:%S"),
            "status": record.status.value,
            "notes": record.notes
        }
        res = requests.post(self.webhook_url, json=payload, timeout=15)
        res.raise_for_status()

    def get_tracked_companies(self) -> List[Dict[str, Any]]:
        try:
            res = requests.get(self.webhook_url, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def update_status(self, company: str, new_status: JobStatus, note: str = "") -> bool:
        payload = {
            "action": "update",
            "company": company,
            "status": new_status.value,
            "notes": note
        }
        try:
            res = requests.post(self.webhook_url, json=payload, timeout=15)
            if res.status_code == 200:
                body = res.json()
                return body.get("status") == "success"
        except Exception:
            pass
        return False

class SheetsTracker(BaseTracker):
    """Google Sheets API resmi via Google Service Account (gspread)."""
    def __init__(self, client=None, sheet_id: str = ""):
        self.sheet_id = sheet_id
        self.client = client
        self.worksheet = None
        if client and sheet_id:
            self.worksheet = client.open_by_key(sheet_id).sheet1

    @classmethod
    def from_service_account(cls, creds_path: str, sheet_id: str):
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        return cls(client=client, sheet_id=sheet_id)

    def init_headers_if_empty(self):
        if not self.worksheet:
            return
        rows = self.worksheet.get_all_values()
        if not rows:
            self.worksheet.append_row(HEADERS)

    def append_record(self, record: ApplicationRecord):
        if not self.worksheet:
            raise RuntimeError("Worksheet not connected")
        row = [
            record.company,
            record.position,
            record.channel,
            record.contact or "",
            record.date_applied.strftime("%Y-%m-%d %H:%M:%S"),
            record.status.value,
            record.notes
        ]
        self.worksheet.append_row(row)

    def get_tracked_companies(self) -> List[Dict[str, Any]]:
        if not self.worksheet:
            return []
        return self.worksheet.get_all_records()

    def update_status(self, company: str, new_status: JobStatus, note: str = "") -> bool:
        if not self.worksheet:
            raise RuntimeError("Worksheet not connected")
        records = self.worksheet.get_all_records()
        for idx, row in enumerate(records, start=2):
            if row.get("Company", "").strip().lower() == company.strip().lower():
                self.worksheet.update_cell(idx, 6, new_status.value)
                if note:
                    curr_notes = str(row.get("Notes", "")).strip()
                    combined_notes = f"{curr_notes} | {note}" if curr_notes else note
                    self.worksheet.update_cell(idx, 7, combined_notes)
                return True
        return False

def get_tracker():
    """Factory otomatis: pilih Webhook -> Service Account -> Local CSV."""
    webhook_url = os.getenv("GOOGLE_WEBHOOK_URL", "").strip()
    if webhook_url:
        return WebhookTracker(webhook_url)

    service_file = os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json").strip()
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if os.path.exists(service_file) and sheet_id:
        try:
            tracker = SheetsTracker.from_service_account(service_file, sheet_id)
            tracker.init_headers_if_empty()
            return tracker
        except Exception as e:
            print(f"[Warning] Gagal inisialisasi gspread: {e}. Mengalihkan ke CSV lokal.")

    # Default fallback: CSV lokal tanpa perlu kredensial sama sekali
    return CSVTracker()
