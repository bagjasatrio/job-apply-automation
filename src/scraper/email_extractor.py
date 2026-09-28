import re
from typing import List, Dict, Any
from src.templates.text_sanitizer import extract_company_from_email
from src.security.date_filter import get_post_date_display

IGNORE_EMAIL_PREFIXES = {
    "support", "help", "info", "contact", "admin", "sales", "billing",
    "service", "marketing", "abuse", "privacy", "security", "noreply",
    "no-reply", "donotreply", "feedback", "press", "media", "notification"
}

IGNORE_DOMAINS = {
    "example.com", "schema.org", "w3.org", "github.com", "google.com",
    "sentry.io", "wixpress.com", "wordpress.org", "gravatar.com"
}

HR_KEYWORDS = [
    "hr", "hrd", "recruitment", "recruit", "career", "careers", "talent",
    "hiring", "job", "jobs", "people", "karir", "loker", "apply"
]

CONTEXT_HIRING_KEYWORDS = [
    "kirim cv", "kirim lamaran", "send resume", "send cv", "email your", "apply to",
    "recruitment", "hiring", "lowongan", "job vacancy", "career"
]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def is_probable_hr_email(email_str: str, surrounding_text: str = "") -> bool:
    email_clean = email_str.lower().strip(" .,;:()[]{}<>\"'")
    user_part, _, domain_part = email_clean.partition("@")

    # Filter out image/extension false positives
    if any(domain_part.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js"]):
        return False

    if domain_part in IGNORE_DOMAINS:
        return False

    if any(user_part == ignored or user_part.startswith(ignored + ".") for ignored in IGNORE_EMAIL_PREFIXES):
        return False

    # Positive signal check from email itself
    has_hr_keyword = any(kw in user_part for kw in HR_KEYWORDS) or any(kw in domain_part for kw in ["career", "talent", "recruitment", "job"])

    # Positive signal check from surrounding text
    has_context_signal = any(kw in surrounding_text.lower() for kw in CONTEXT_HIRING_KEYWORDS) if surrounding_text else False

    is_common_provider = any(p in domain_part for p in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"])

    if is_common_provider:
        return has_hr_keyword or has_context_signal

    return True

def extract_hr_emails_and_leads(text: str, default_company: str = "", default_position: str = "", source_url: str = "") -> List[Dict[str, Any]]:
    found = EMAIL_REGEX.findall(text)
    unique_emails = set()
    leads = []

    for raw_email in found:
        cleaned = raw_email.strip(" .,;:()[]{}<>\"'")
        if cleaned.lower() in unique_emails:
            continue
        if is_probable_hr_email(cleaned, surrounding_text=text):
            unique_emails.add(cleaned.lower())
            resolved_company = default_company
            if not resolved_company or resolved_company in ["Tech Company", "Unknown Company", "Perusahaan Target"]:
                resolved_company = extract_company_from_email(cleaned, fallback="Perusahaan Target")

            # Ambil konteks kalimat deskripsi di sekitar posisi email/loker
            email_idx = text.lower().find(cleaned.lower())
            if email_idx != -1:
                start = max(0, email_idx - 160)
                end = min(len(text), email_idx + 240)
                snippet_text = text[start:end].strip()
            else:
                snippet_text = text[:350].strip()

            snippet_clean = " ".join(snippet_text.split())
            if len(snippet_clean) > 350:
                snippet_clean = snippet_clean[:350] + "..."

            leads.append({
                "email": cleaned,
                "company": resolved_company,
                "position": default_position or "Software / Tech Role",
                "source_url": source_url,
                "snippet": snippet_clean,
                "post_date_display": get_post_date_display(f"{snippet_clean} {text[:1000]}")
            })

    return leads
