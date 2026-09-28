import re
from typing import Tuple
from src.models import JobStatus

OFFERING_KEYWORDS = [
    r"offering\s+letter",
    r"penawaran\s+kerja",
    r"job\s+offer",
    r"surat\s+penawaran",
    r"penawaran\s+gaji",
    r"offer\s+of\s+employment",
    r"kontrak\s+kerja"
]

REJECTION_KEYWORDS = [
    r"tidak\s+melanjutkan",
    r"belum\s+dapat\s+melanjutkan",
    r"belum\s+bisa\s+melanjutkan",
    r"belum\s+sesuai\s+dengan\s+kriteria",
    r"keep\s+your\s+resume\s+on\s+file",
    r"unfortunately",
    r"regret\s+to\s+inform",
    r"decided\s+to\s+pursue\s+other\s+candidates",
    r"not\s+moving\s+forward",
    r"terima\s+kasih\s+atas\s+minat\s+anda.*namun"
]

INTERVIEW_KEYWORDS = [
    r"interview",
    r"wawancara",
    r"undangan",
    r"technical\s+test",
    r"user\s+interview",
    r"screening\s+call",
    r"assessment",
    r"google\s+meet",
    r"zoom",
    r"jadwal\s+tes"
]

def classify_email_body(text: str) -> Tuple[JobStatus, float]:
    lower = text.lower()

    for pattern in OFFERING_KEYWORDS:
        if re.search(pattern, lower):
            return JobStatus.OFFERING, 0.95

    for pattern in REJECTION_KEYWORDS:
        if re.search(pattern, lower):
            return JobStatus.REJECTED, 0.90

    for pattern in INTERVIEW_KEYWORDS:
        if re.search(pattern, lower):
            return JobStatus.ON_PROGRESS, 0.85

    # Default fallback
    return JobStatus.ON_PROGRESS, 0.50
