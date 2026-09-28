import re

PUBLIC_EMAIL_PROVIDERS = {
    "gmail.com", "yahoo.com", "yahoo.co.id", "hotmail.com", "outlook.com",
    "ymail.com", "icloud.com", "proton.me", "protonmail.com"
}

def extract_company_from_email(email_str: str, fallback: str = "Perusahaan Target") -> str:
    """Mengekstrak nama perusahaan yang bersih dari domain email (misal: career@game-consign.com -> Game Consign)."""
    if not email_str or "@" not in email_str:
        return fallback

    user_part, _, domain_part = email_str.lower().partition("@")
    domain_part = domain_part.strip()

    if domain_part in PUBLIC_EMAIL_PROVIDERS:
        # Jika gmail/yahoo, coba tebak dari nama depan jika ada kata company
        cleaned_user = re.sub(r"^(recruitment|hr|hrd|career|careers|talent|jobs|loker|hiring)[._-]?", "", user_part)
        cleaned_user = re.sub(r"[0-9_-]+$", "", cleaned_user).strip(" ._-")
        if len(cleaned_user) >= 3:
            return cleaned_user.replace(".", " ").replace("-", " ").title()
        return fallback

    # Buang TLD (.com, .co.id, .id, .io, .net, dll)
    domain_name = re.sub(r"\.(co\.id|co|com\.sg|com|id|io|org|net|tech|app|ai|dev)$", "", domain_part)
    # Bersihkan subdomain jika ada (misal: jobs.tokopedia -> tokopedia)
    parts = domain_name.split(".")
    core_name = parts[-1] if len(parts) > 1 else domain_name

    # Format rapi (game-consign -> Game Consign, genesysindonesia -> Genesys Indonesia)
    formatted = core_name.replace("-", " ").replace("_", " ")

    # Pisahkan kata gabungan umum jika ada (misal: genesysindonesia -> Genesys Indonesia)
    formatted = re.sub(r"(indonesia|tech|teknologi|digital|asia|solusi)", r" \1", formatted, flags=re.IGNORECASE)
    formatted = " ".join([w.capitalize() for w in formatted.split() if w])

    return formatted or fallback

def clean_markdown_slop(text: str) -> str:
    """Membersihkan format markdown asterisks (**), strip AI cliches, dan mengganti placeholder generic."""
    # 1. Hilangkan asterisks bold & italic markdown (**teks** -> teks, *teks* -> teks)
    cleaned = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)

    # 2. Ganti placeholder generic dengan kontak kandidat yang sebenarnya
    replacements = [
        (r"\[Your Phone Number\]|\[Phone Number\]|\[Nomor Telepon\]|\[No\. HP\]", "+62 812-2068-4832"),
        (r"\[Your Email(?: Address)?\]|\[Email Address\]|\[Alamat Email\]", "muhammad.bagjasatrio28@gmail.com"),
        (r"\[Your LinkedIn(?:/GitHub)?(?: URL)?\]|\[LinkedIn URL\]|\[Profil LinkedIn\]", "linkedin.com/in/muhammadbagjasatrio | bagjasatrio.vercel.app"),
        (r"\[Portfolio(?: URL)?\]|\[Website Portfolio\]", "bagjasatrio.vercel.app"),
        (r"\[Your Name\]|\[Nama Anda\]|\[Nama Pelamar\]", "Muhammad Bagja Satrio")
    ]
    for pattern, repl in replacements:
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)

    # 3. Hilangkan baris-baris placeholder yang tersisa dalam kurung siku
    cleaned = re.sub(r"\[.*?\]", "", cleaned)

    # 4. Normalisasi spasi dan baris kosong
    lines = [line.strip() for line in cleaned.splitlines()]
    result = []
    prev_blank = False
    for line in lines:
        if line:
            result.append(line)
            prev_blank = False
        elif not prev_blank:
            result.append("")
            prev_blank = True

    return "\n".join(result).strip()
