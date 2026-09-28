import re
from datetime import datetime, timedelta
from typing import Tuple, Optional

# Batas maksimal usia posting lowongan: 60 hari (1-2 bulan)
MAX_POST_AGE_DAYS = 60

ID_MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "agt": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12, "dec": 12, "may": 5, "oct": 10
}

EN_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

def extract_post_date(text: str) -> Optional[datetime]:
    """Mendeteksi tanggal absolut dalam teks cuplikan."""
    now = datetime.now()

    # Format: YYYY-MM-DD
    iso_match = re.search(r'\b(202\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b', text)
    if iso_match:
        try:
            return datetime.strptime(iso_match.group(0), "%Y-%m-%d")
        except Exception:
            pass

    # Format: DD Month YYYY (e.g. 15 Agustus 2026 atau 15 August 2026)
    d_m_y = re.search(r'\b([0-2]?\d|3[01])\s+([A-Za-z]+)\s+(202\d)\b', text)
    if d_m_y:
        day = int(d_m_y.group(1))
        month_name = d_m_y.group(2).lower()
        year = int(d_m_y.group(3))
        month_num = ID_MONTHS.get(month_name) or EN_MONTHS.get(month_name)
        if month_num:
            try:
                return datetime(year, month_num, day)
            except Exception:
                pass

    # Format: Month DD, YYYY (e.g. Aug 15, 2026)
    m_d_y = re.search(r'\b([A-Za-z]+)\s+([0-2]?\d|3[01]),?\s+(202\d)\b', text)
    if m_d_y:
        month_name = m_d_y.group(1).lower()
        day = int(m_d_y.group(2))
        year = int(m_d_y.group(3))
        month_num = ID_MONTHS.get(month_name) or EN_MONTHS.get(month_name)
        if month_num:
            try:
                return datetime(year, month_num, day)
            except Exception:
                pass

    return None

def is_within_recency(text: str, max_days: int = MAX_POST_AGE_DAYS) -> Tuple[bool, str]:
    """
    Mengecek apakah lowongan diposting dalam kurun waktu 1-2 bulan kebelakang (default: <= 60 hari).
    Mengembalikan (True, "") jika lolos, atau (False, "alasan") jika kedaluwarsa.
    """
    t_lower = text.lower()
    now = datetime.now()

    # 1. Cek tahun-tahun lama yang sudah lewat jauh (< tahun sekarang)
    current_year = now.year
    for old_year in range(2018, current_year):
        pattern = rf'\b(?:tahun|year|di|in|posting|posted|date)?\s*{old_year}\b'
        if re.search(pattern, t_lower):
            # Pastikan bukan sekadar nomor telepon/kode unik
            if re.search(rf'\b{old_year}\b', t_lower):
                return False, f"Tahun lowongan sudah kedaluwarsa ({old_year} < {current_year})"

    # 2. Cek waktu relatif (Indonesian & English)
    # Relative: bulan / months
    m_match = re.search(r'(\d+)\s*(?:month|months|bulan)\s*(?:ago|yang lalu|lalu)', t_lower)
    if m_match:
        months = int(m_match.group(1))
        approx_days = months * 30
        if approx_days > max_days:
            return False, f"Lowongan kedaluwarsa ({months} bulan yang lalu > batas {max_days // 30} bulan)"
        return True, f"Diposting {months} bulan lalu (lolos)"

    # Relative: tahun / years
    y_match = re.search(r'(\d+)\s*(?:year|years|tahun)\s*(?:ago|yang lalu|lalu)', t_lower)
    if y_match:
        years = int(y_match.group(1))
        return False, f"Lowongan kedaluwarsa ({years} tahun yang lalu)"

    # Relative: minggu / weeks
    w_match = re.search(r'(\d+)\s*(?:week|weeks|minggu)\s*(?:ago|yang lalu|lalu)', t_lower)
    if w_match:
        weeks = int(w_match.group(1))
        approx_days = weeks * 7
        if approx_days > max_days:
            return False, f"Lowongan kedaluwarsa ({weeks} minggu yang lalu > {max_days} hari)"
        return True, f"Diposting {weeks} minggu lalu (lolos)"

    # Relative: hari / days
    d_match = re.search(r'(\d+)\s*(?:day|days|hari)\s*(?:ago|yang lalu|lalu)', t_lower)
    if d_match:
        days = int(d_match.group(1))
        if days > max_days:
            return False, f"Lowongan kedaluwarsa ({days} hari yang lalu > {max_days} hari)"
        return True, f"Diposting {days} hari lalu (lolos)"

    # 3. Cek tanggal absolut
    abs_date = extract_post_date(text)
    if abs_date:
        age_days = (now - abs_date).days
        if age_days > max_days:
            return False, f"Tanggal posting {abs_date.strftime('%Y-%m-%d')} kedaluwarsa ({age_days} hari lalu > {max_days} hari)"
        elif age_days < -1:
            # Tanggal di masa depan (mungkin anomali/typo, tetap izinkan)
            return True, "Tanggal posting valid"
        else:
            return True, f"Tanggal posting valid ({age_days} hari lalu)"

    # Default lolos jika tidak ada tanda kedaluwarsa
    return True, "Tanggal posting dianggap baru"

def get_post_date_display(text: str) -> str:
    """Mengekstrak label tanggal/waktu postingan yang manusiawi untuk ditampilkan di Telegram."""
    t_lower = text.lower()
    now = datetime.now()

    # 1. Cek jam / hours
    h_match = re.search(r'(\d+)\s*(?:hour|hours|jam)\s*(?:ago|yang lalu|lalu)?', t_lower)
    if h_match:
        return f"{h_match.group(1)} jam yang lalu"

    # 2. Cek hari / days
    d_match = re.search(r'(\d+)\s*(?:day|days|hari)\s*(?:ago|yang lalu|lalu)', t_lower)
    if d_match:
        days = int(d_match.group(1))
        approx_date = (now - timedelta(days=days)).strftime("%d %b %Y")
        return f"{days} hari lalu ({approx_date})"

    # 3. Cek minggu / weeks
    w_match = re.search(r'(\d+)\s*(?:week|weeks|minggu)\s*(?:ago|yang lalu|lalu)', t_lower)
    if w_match:
        weeks = int(w_match.group(1))
        approx_date = (now - timedelta(days=weeks * 7)).strftime("%d %b %Y")
        return f"{weeks} minggu lalu (~{approx_date})"

    # 4. Cek bulan / months
    m_match = re.search(r'(\d+)\s*(?:month|months|bulan)\s*(?:ago|yang lalu|lalu)', t_lower)
    if m_match:
        months = int(m_match.group(1))
        approx_date = (now - timedelta(days=months * 30)).strftime("%d %b %Y")
        return f"{months} bulan lalu (~{approx_date})"

    # 5. Cek tanggal absolut
    abs_date = extract_post_date(text)
    if abs_date:
        age_days = (now - abs_date).days
        if age_days == 0:
            return f"Hari ini ({abs_date.strftime('%d %b %Y')})"
        elif age_days == 1:
            return f"Kemarin ({abs_date.strftime('%d %b %Y')})"
        else:
            return f"{abs_date.strftime('%d %b %Y')} ({age_days} hari lalu)"

    # 6. Default jika terdeteksi baru
    return f"Aktif / Baru terjaring ({now.strftime('%d %b %Y %H:%M WIB')})"
