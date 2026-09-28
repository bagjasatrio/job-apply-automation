import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def parse_date(date_str: str) -> Optional[datetime]:
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return None

def find_stale_applications(records: List[Dict[str, Any]], days_threshold: int = 5) -> List[Dict[str, Any]]:
    stale_list = []
    now = datetime.now()

    for r in records:
        status = str(r.get("Status", "")).strip()
        contact = str(r.get("Contact", "")).strip()
        notes = str(r.get("Notes", "")).strip()
        date_raw = str(r.get("Date Applied", "")).strip()

        # Hanya lamaran berstatus Applied, ada kontak email, dan belum pernah difollow-up
        if status != "Applied":
            continue
        if "@" not in contact:
            continue
        if "followed-up" in notes.lower() or "follow-up sent" in notes.lower():
            continue

        applied_dt = parse_date(date_raw)
        if not applied_dt:
            continue

        diff_days = (now - applied_dt).days
        if diff_days >= days_threshold:
            r["days_elapsed"] = diff_days
            stale_list.append(r)

    return stale_list

def generate_follow_up_prompt(company: str, position: str, lang: str = "id") -> str:
    lang_desc = "Bahasa Indonesia formal, sopan, dan hangat." if lang == "id" else "Professional and polite English."
    return f"""
Kamu adalah pelamar kerja profesional bernama Muhammad Bagja Satrio.
Tulis email Follow-up singkat (1-2 paragraf pendek) untuk menanyakan status lamaran posisi {position} di {company} yang telah dikirim beberapa hari lalu.

Panduan:
- Bahasa: {lang_desc}
- Nada: Sopan, menghargai waktu rekruter, menunjukkan antusiasme tinggi.
- Tanyakan apakah ada informasi tambahan atau portofolio/tugas yang dibutuhkan untuk proses rekrutmen.
- Tanpa salam berlebihan atau bahasa kaku.
"""

def generate_default_follow_up(company: str, position: str, lang: str = "id") -> str:
    if lang == "en":
        return f"""Dear Hiring Team at {company},

I hope this email finds you well.

I am writing to follow up on my recent application for the {position} position at {company}. I remain very enthusiastic about the opportunity to contribute my skills in full-stack engineering and AI solutions to your team.

Please let me know if you require any further information or work samples from my side. Thank you for your time and consideration.

Sincerely,
Muhammad Bagja Satrio
"""
    else:
        return f"""Kepada Yth. Tim HRD / Rekruter {company},

Semoga Bapak/Ibu dalam keadaan sehat.

Melalui email ini, saya ingin menanyakan kabar dan kelanjutan proses lamaran saya untuk posisi {position} di {company} yang telah saya kirimkan sebelumnya. Saya sangat antusias untuk dapat berdiskusi lebih lanjut dan berkontribusi di {company}.

Apabila diperlukan informasi atau dokumen tambahan, mohon jangan ragu untuk mengabari saya. Terima kasih banyak atas waktu dan perhatian Bapak/Ibu.

Hormat saya,
Muhammad Bagja Satrio
"""
