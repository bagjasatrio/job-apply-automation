import os
import re
from typing import Tuple, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

SCAM_PATTERNS = [
    # Modus travel / tiket pesawat / hotel reimburse
    (r"(reservasi|booking|biaya)\s+(tiket|pesawat|hotel|akomodasi|travel)", "Indikasi modus penipuan tiket travel / akomodasi fiktif"),
    (r"(biro\s+perjalanan|agen\s+travel|travel\s+tour|pihak\s+ketiga\s+travel)", "Mewajibkan agen travel tertentu"),
    (r"(reimburse|diganti)\s+(setibanya|di\s+lokasi|setelah\s+tes)", "Janji palsu reimbursement biaya tiket"),

    # Modus bayar biaya registrasi / seragam / jaminan
    (r"(biaya\s+pendaftaran|biaya\s+administrasi|biaya\s+seragam|uang\s+jaminan|biaya\s+pelatihan)", "Memungut biaya pendaftaran / seragam / pelatihan"),
    (r"(transfer\s+ke\s+rekening|membayar\s+sejumlah|biaya\s+meterai\s+wajib)", "Meminta transfer dana ke rekening pribadi"),

    # Modus tugas paruh waktu like & follow / e-commerce click scam
    (r"(like\s+video|follow\s+akun|pesanan\s+shopee|pesanan\s+e-commerce|pesanan\s+lazada|tugas\s+harian|komisi\s+\d+)", "Modus tugas paruh waktu / komisi like palsu"),
    (r"(penghasilan\s+\d+\s*(?:rb|ribu|jt|juta)\s*per\s*hari|gaji\s+harian\s+tanpa\s+pengalaman)", "Janji komisi harian tidak wajar")
]

MAJOR_ENTERPRISES = [
    "pertamina", "telkom", "pln", "bca", "bank central asia", "mandiri", "bank mandiri",
    "bri", "bank rakyat indonesia", "bni", "kai", "kereta api indonesia",
    "garuda indonesia", "astra", "indofood", "unilever", "shopee", "tokopedia", "gojek", "grab"
]

FREE_EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "yahoo.co.id", "hotmail.com", "outlook.com", "ymail.com"
]

class ScamDetector:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def is_suspicious_lead(self, company: str, position: str, email: str, job_text: str) -> Tuple[bool, str]:
        """Memeriksa apakah lowongan memiliki karakteristik penipuan/loker bodong."""
        comp_lower = company.lower()
        email_lower = email.lower()
        full_text = f"{company} {position} {email} {job_text}".lower()

        # 1. Cek pola kata kunci modus penipuan terkenal
        for pattern, reason in SCAM_PATTERNS:
            if re.search(pattern, full_text):
                return True, reason

        # 2. Cek domain spoofing (BUMN / Perusahaan Raksasa pakai email gratisan)
        email_domain = email_lower.split("@")[-1] if "@" in email_lower else ""
        if email_domain in FREE_EMAIL_DOMAINS:
            for enterprise in MAJOR_ENTERPRISES:
                if enterprise in comp_lower or enterprise in email_lower.split("@")[0]:
                    return True, f"Pencatutan nama BUMN/Korporat ({company}) menggunakan domain email gratisan (@{email_domain}). BUMN resmi tidak pernah memakai Gmail/Yahoo."

        return False, "Lowongan terverifikasi aman"
