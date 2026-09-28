import os
import re
from datetime import datetime
from typing import Optional
from src.ai_assistant import AIAssistant, CANDIDATE_SUMMARY

class InterviewPrepKit:
    def __init__(self, output_dir: str = "interviews", api_key: Optional[str] = None):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.ai = AIAssistant(api_key=api_key)

    def generate_prep_kit(
        self,
        company: str,
        position: str,
        email_snippet: str = "",
        job_description: str = ""
    ) -> str:
        """Membuat lembar panduan latihan wawancara komprehensif berbasis profil kandidat & tech stack lowongan."""
        safe_comp = re.sub(r"[^a-zA-Z0-9_-]", "_", company)[:25]
        safe_pos = re.sub(r"[^a-zA-Z0-9_-]", "_", position)[:25]
        filename = f"Interview_Prep_{safe_comp}_{safe_pos}.md"
        filepath = os.path.join(self.output_dir, filename)

        system_prompt = (
            "Kamu adalah Senior Technical Hiring Manager dan Career Coach spesialis rekrutmen teknologi. "
            "Tugasmu adalah menyusun lembar panduan persiapan wawancara kerja yang sangat tajam, taktis, dan aplikatif. "
            "Fokuskan jawaban kandidat pada proyek nyata yang sudah ia bangun: ClipMax (Python CUDA, Faster-Whisper, MediaPipe, FFmpeg NVENC), "
            "ClipMax Mobile (Flutter Dart FFI Whisper.cpp), CVKita (ATS scoring & LLM Gateway), dan pengalaman di Diskominfo Semarang."
        )

        user_prompt = f"""
PROFIL LENGKAP KANDIDAT:
{CANDIDATE_SUMMARY}

TARGET PERUSAHAAN & POSISI:
Perusahaan: {company}
Posisi: {position}
Deskripsi Pekerjaan / Kualifikasi:
{job_description or 'Teknologi Software Engineering / Web Fullstack / AI Development'}
Konteks Undangan HRD:
{email_snippet or 'Undangan User Interview / Technical Assessment'}

Susun dokumen persiapan interview lengkap dalam format Markdown dengan struktur:
# PANDUAN PERSIAPAN WAWANCARA: {company} — {position}
*Dihasilkan otomatis pada {datetime.now().strftime("%d %B %Y")}*

## 1. Ringkasan Kualifikasi Kunci yang Dicari
- 3-4 poin kemampuan utama yang menjadi fokus evaluasi pewawancara.

## 2. Riset Perusahaan & Analisis Nilai Tambah
- Estimasi domain bisnis perusahaan dan bagaimana keahlian kandidat (Fullstack / AI / Automasi) dapat memberi dampak langsung.

## 3. Top 8 Prediksi Pertanyaan Wawancara & Strategi Jawaban
Sertakan 4 Pertanyaan Teknis & 4 Pertanyaan Perilaku/Situasional (STAR method).
Untuk setiap pertanyaan berikan:
- **Pertanyaan**:
- **Tujuan Pewawancara**: Mengapa mereka menanyakan hal ini?
- **Strategi & Contoh Jawaban Ideal**: Hubungkan langsung dengan portofolio kandidat (ClipMax / Diskominfo / Flutter / LLM).

## 4. Reverse Interview: 5 Pertanyaan Balik Berkualitas Tinggi
- Pertanyaan cerdas yang bisa diajukan kandidat kepada pewawancara untuk menunjukkan inisiatif dan wawasan engineering yang matang.

## 5. Tips Negosiasi & Penutup
- Strategi menjawab ekspektasi gaji dan langkah konfirmasi tindak lanjut (follow-up).
"""
        try:
            content = self.ai._call_gemini(user_prompt, system_instruction=system_prompt)
        except Exception:
            content = f"""# PANDUAN PERSIAPAN WAWANCARA: {company} — {position}
*Dihasilkan pada {datetime.now().strftime("%d %B %Y")}*

## 1. Fokus Kompetensi
- Fullstack Web Development & REST APIs
- Integrasi Multi-Provider LLM & Prompt Engineering
- Media Processing (Whisper, MediaPipe, FFmpeg)
- Mobile On-Device AI (Flutter/Dart)

## 2. Proyek yang Wajib Diceritakan
1. **ClipMax**: Tekankan optimalisasi hardware acceleration (CUDA NVENC) dan 85 automated test suite.
2. **ClipMax Mobile**: Tekankan integrasi low-level C++ native via Dart FFI.
3. **Diskominfo Kota Semarang**: Tekankan standar responsivitas 100% dan kerja sama tim.

## 3. Pertanyaan Kunci untuk HRD
1. Bagaimana siklus deployment dan arsitektur backend yang saat ini digunakan di {company}?
2. Apa tantangan teknis terbesar yang sedang dihadapi tim engineering dalam 6 bulan ke depan?
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
