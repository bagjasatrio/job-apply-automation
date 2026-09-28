import re
from typing import Tuple

# Daftar wilayah luar Pulau Jawa (Provinsi & Kota Besar)
NON_JAVA_REGIONS = [
    # Sumatera
    "medan", "palembang", "padang", "pekanbaru", "batam", "lampung", "bandar lampung",
    "aceh", "banda aceh", "jambi", "bengkulu", "pangkal pinang", "riau", "kepri",
    "kepulauan riau", "sumatera", "sumatera utara", "sumatera barat", "sumatera selatan", "sumut", "sumbar", "sumsel",
    # Kalimantan
    "balikpapan", "samarinda", "banjarmasin", "pontianak", "palangkaraya", "tarakan",
    "bontang", "banjarbaru", "kalimantan", "kalimantan timur", "kalimantan barat", "kalimantan selatan", "kaltim", "kalbar", "kalsel",
    # Sulawesi
    "makassar", "manado", "palu", "kendari", "gorontalo", "mamuju", "sulawesi",
    "sulawesi selatan", "sulawesi utara", "sulsel", "sulut",
    # Bali & Nusa Tenggara
    "bali", "denpasar", "badung", "gianyar", "ubud", "lombok", "mataram", "kupang",
    "sumbawa", "flores", "ntt", "ntb", "nusa tenggara",
    # Maluku & Papua
    "ambon", "ternate", "jayapura", "sorong", "merauke", "timika", "manokwari", "papua", "maluku"
]

# Negara Luar Negeri umum
OVERSEAS_REGIONS = [
    "singapore", "singapura", "malaysia", "kuala lumpur", "thailand", "bangkok",
    "vietnam", "philippines", "united states", "usa", "us", "uk", "united kingdom",
    "london", "australia", "sydney", "melbourne", "germany", "jerman", "berlin",
    "japan", "jepang", "tokyo", "canada", "india", "netherlands", "belanda"
]

# Kata kunci mode kerja Remote / WFH
REMOTE_KEYWORDS = [
    "remote", "wfh", "work from home", "work from anywhere", "wfa",
    "telecommute", "kerjadarirumah", "kerja dari rumah", "100% remote", "fully remote",
    "remote work", "worldwide remote", "anywhere"
]

# Kata kunci mode kerja WFO / Onsite / Hybrid
ONSITE_HYBRID_KEYWORDS = [
    "wfo", "work from office", "onsite", "on-site", "hybrid",
    "penempatan di", "penempatan", "domisili", "kantor", "office based",
    "lokasi kantor", "relocation", "bersedia ditempatkan"
]

def is_location_acceptable(text: str, location_hint: str = "") -> Tuple[bool, str]:
    """
    Evaluasi kelayakan lokasi dan mode kerja loker:
    - Dalam Pulau Jawa: Bebas (WFO, Hybrid, Remote, WFH diterima).
    - Luar Pulau Jawa: WAJIB Remote / WFH. Jika WFO / Onsite / Hybrid -> OTOMATIS SKIP.
    - Luar Negeri: WAJIB Remote / WFH. Jika Onsite / WFO -> OTOMATIS SKIP.
    """
    combined = f"{text} {location_hint}".lower()

    # 1. Cek apakah ada sinyal Remote / WFH yang jelas
    has_remote_signal = any(re.search(rf'\b{re.escape(kw)}\b', combined) for kw in REMOTE_KEYWORDS)

    # 2. Cek apakah ada sinyal Luar Negeri
    is_overseas = any(re.search(rf'\b{re.escape(reg)}\b', combined) for reg in OVERSEAS_REGIONS)
    if is_overseas:
        if has_remote_signal:
            return True, "Luar Negeri (Remote / WFH diizinkan)"
        else:
            return False, "Loker Luar Negeri non-remote (WFO/Onsite tidak diizinkan)"

    # 3. Cek apakah lokasi berada di Luar Pulau Jawa
    detected_non_java = None
    for reg in NON_JAVA_REGIONS:
        if re.search(rf'\b{re.escape(reg)}\b', combined):
            detected_non_java = reg.title()
            break

    if detected_non_java:
        # Jika luar Jawa dan dinyatakan Remote / WFH tanpa keharusan WFO/kantor
        if has_remote_signal and not any(kw in combined for kw in ["wfo", "work from office", "hybrid", "onsite", "on-site"]):
            return True, f"Luar Jawa ({detected_non_java}) tetapi 100% Remote / WFH (Diizinkan)"
        else:
            # Jika WFO, Onsite, Hybrid, atau penempatan di lokasi luar Jawa
            return False, f"Luar Pulau Jawa ({detected_non_java}) dengan mode WFO/Hybrid/Onsite (Ditolak, hanya terima remote)"

    # 4. Dalam Pulau Jawa atau Lokasi Umum Indonesia
    return True, "Pulau Jawa / Nasional (WFO, Hybrid, atau Remote diterima)"
