import os
import re
from typing import Optional

INDONESIAN_WORDS = {
    "kami", "yang", "dan", "untuk", "dengan", "lowongan", "posisi", "perusahaan",
    "pekerjaan", "pengalaman", "kualifikasi", "lamaran", "surat", "gaji", "tanggung",
    "jawab", "persyaratan", "kemampuan", "pelamar", "hormat", "yth", "membutuhkan",
    "kirim", "cv", "loker", "dibutuhkan", "pria", "wanita", "maksimal", "minimal",
    "lulusan", "pendidikan", "jurusan", "dapat", "menguasai", "lokasi", "penempatan",
    "di", "ke", "dari", "atau", "pada", "oleh", "sebagai", "dalam", "bisa", "adalah",
    "terbuka", "tentang", "kontak", "hubungi", "kantor", "bidang", "kerja", "rekrutmen"
}

ENGLISH_WORDS = {
    "we", "are", "looking", "for", "seeking", "requirements", "skills", "experience",
    "responsibilities", "qualifications", "developer", "engineer", "job", "position",
    "apply", "hiring", "team", "remote", "fulltime", "salary", "benefits", "role",
    "software", "junior", "senior", "entry", "level", "with", "and", "in", "to", "at",
    "the", "of", "candidate", "must", "have", "degree", "computer", "science"
}

def detect_language(text: str, default_lang: str = "id", email_or_domain: str = "") -> str:
    """
    Mendeteksi apakah teks lowongan menggunakan Bahasa Indonesia ('id') atau Bahasa Inggris ('en').
    Jika domain/email berakhiran .id atau zona Indonesia dan tidak dominan Inggris -> pilih 'id'.
    """
    text_lower = text.lower()

    # Cek sinyal domain .id (Indonesia)
    if email_or_domain:
        ed_lower = email_or_domain.lower()
        if ed_lower.endswith(".id") or ".id/" in ed_lower or ".co.id" in ed_lower:
            default_lang = "id"

    words = re.findall(r"\b[a-zA-Z]{2,}\b", text_lower)
    id_score = sum(1 for w in words if w in INDONESIAN_WORDS)
    en_score = sum(1 for w in words if w in ENGLISH_WORDS)

    if id_score > 0 and id_score >= en_score:
        return "id"

    # Istilah teknis (developer, engineer) sering tercampur di loker Indonesia
    if id_score > 0 and (id_score * 1.5) >= en_score:
        return "id"

    if en_score > id_score:
        return "en"

    return default_lang

class CVManager:
    LOCAL_CV_ID = os.path.join(os.getcwd(), "CV_Kandidat.pdf")
    LOCAL_CV_EN = os.path.join(os.getcwd(), "CV_Candidate_EN.pdf")

    def __init__(self, cv_id_path: Optional[str] = None, cv_en_path: Optional[str] = None):
        self.cv_id_path = cv_id_path or os.getenv("CV_ID_PATH") or self._find_local_cv("id")
        self.cv_en_path = cv_en_path or os.getenv("CV_EN_PATH") or self._find_local_cv("en")

    def _find_local_cv(self, lang: str) -> str:
        try:
            for f in os.listdir(os.getcwd()):
                if f.lower().endswith(".pdf") and "cv" in f.lower():
                    if lang == "en" and ("_en" in f.lower() or "english" in f.lower()):
                        return os.path.join(os.getcwd(), f)
                    elif lang == "id" and ("_en" not in f.lower() and "english" not in f.lower()):
                        return os.path.join(os.getcwd(), f)
        except Exception:
            pass
        return self.LOCAL_CV_ID if lang == "id" else self.LOCAL_CV_EN

    def get_cv(self, lang: str = "id") -> str:
        lang = lang.lower().strip()
        if lang in ["id", "indonesia", "indonesian"]:
            if os.path.exists(self.cv_id_path):
                return self.cv_id_path
            return self.cv_en_path
        else:
            if os.path.exists(self.cv_en_path):
                return self.cv_en_path
            return self.cv_id_path

    def get_cv_for_text(self, text: str) -> str:
        lang = detect_language(text)
        return self.get_cv(lang)
