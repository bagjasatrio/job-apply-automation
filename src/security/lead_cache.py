import os
import json
import time
from typing import Dict, Any, Optional

DEFAULT_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seen_leads.json")

class LeadCache:
    """Menyimpan riwayat loker yang telah di-screening/dinotifikasi agar tidak muncul ganda."""
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or DEFAULT_CACHE_FILE
        self.data: Dict[str, Any] = {"emails": {}, "urls": {}}
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    if "emails" not in self.data:
                        self.data["emails"] = {}
                    if "urls" not in self.data:
                        self.data["urls"] = {}
            except Exception:
                self.data = {"emails": {}, "urls": {}}
        else:
            self._save()

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def is_lead_seen(self, email: str = "", url: str = "") -> bool:
        if email and email.lower().strip() in self.data.get("emails", {}):
            return True
        if url and url.strip() in self.data.get("urls", {}):
            return True
        return False

    def mark_lead_seen(self, email: str = "", url: str = "", company: str = "", position: str = ""):
        now_ts = time.time()
        record = {
            "company": company,
            "position": position,
            "timestamp": now_ts
        }
        if email:
            self.data.setdefault("emails", {})[email.lower().strip()] = record
        if url:
            self.data.setdefault("urls", {})[url.strip()] = record
        self._save()

    def total_seen_count(self) -> int:
        return len(self.data.get("emails", {}))
