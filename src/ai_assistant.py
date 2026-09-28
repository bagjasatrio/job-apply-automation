import os
import json
import re
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

load_dotenv()

CANDIDATE_SUMMARY = """
Nama: Muhammad Bagja Satrio
Latar Belakang: S1 Teknik Informatika (Universitas Dian Nuswantoro), GPA 3.29.
Karakter & Etos Kerja: Mampu bekerja sama dalam tim, mudah beradaptasi dengan lingkungan dan tantangan baru, serta berkomitmen untuk bekerja secara profesional dan bertanggung jawab dalam menjalankan setiap tugas dan kewajiban.
Keahlian Inti:
- Full-Stack Web Development: Python, Flask, REST APIs, modular responsive UI (Pengalaman di Diskominfo Semarang).
- AI & LLM Systems: Integrasi LLM multi-provider (OpenAI, OpenRouter, Groq, Gemini) via API Gateway/Proxy, Prompt Engineering, ATS Optimization (CVKita).
- Multimedia & Video AI Pipeline: Faster-Whisper (CUDA), MediaPipe face tracking, FFmpeg NVENC hardware-accelerated video rendering (ClipMax).
- Mobile & On-Device AI: Flutter/Dart, Dart FFI, Whisper.cpp on-device transcription (ClipMax Mobile).
- DevOps & Tools: CI/CD, Git, automated testing (Pytest), Playwright automation, 5 Sertifikasi IBM Software Engineering & AI.
"""

class AIAssistant:
    MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash"]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def _call_gemini(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY belum diset di .env")

        headers = {"Content-Type": "application/json"}
        for model in self.MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            try:
                res = requests.post(url, json=payload, headers=headers, timeout=25)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception:
                continue

        raise RuntimeError("Gagal menghubungi Google Gemini API setelah mencoba model yang tersedia.")

    def generate_cover_letter(self, company: str, position: str, job_description: str = "", lang: str = "id") -> str:
        from src.templates.text_sanitizer import clean_markdown_slop

        system_prompt = (
            "Kamu adalah Muhammad Bagja Satrio, seorang software engineer profesional lulusan S1 Teknik Informatika. "
            "Tulis surat lamaran kerja yang padat, wajar, natural, dan tidak terkesan dibuat-buat oleh AI (hindari AI slop/klise). "
            "ATURAN MUTLAK:\n"
            "1. DILARANG menggunakan format markdown seperti tanda bintang (** atau *). Tulis teks polos biasa.\n"
            "2. DILARANG menggunakan placeholder kurung siku seperti [Your Phone Number], [Your Email], [Link].\n"
            "3. Kontak resmi yang harus dipakai di penutup:\n"
            "   Muhammad Bagja Satrio\n"
            "   WhatsApp/Telp: +62 812-2068-4832\n"
            "   Email: muhammad.bagjasatrio28@gmail.com\n"
            "   Portofolio: bagjasatrio.vercel.app\n"
            f"4. Perusahaan tujuan lamaran HANYA '{company}'. Dilarang keras menyebut nama perusahaan lain!\n"
            "5. Hindari kalimat klise AI seperti 'I am writing to express my strong/enthusiastic interest', 'seamless experience', 'scalable engineering'. Langsung to the point."
        )

        lang_instruction = "Gunakan Bahasa Indonesia formal, lugas, dan santun." if lang == "id" else "Write in clean, natural professional English without corporate clichés."

        user_prompt = f"""
Profil Kandidat:
{CANDIDATE_SUMMARY}

Target Perusahaan: {company}
Posisi: {position}
Deskripsi Lowongan / Kualifikasi:
{job_description or 'Posisi Software Engineering / Web / Mobile / AI'}

Instruksi Bahasa: {lang_instruction}

Buat draft email lamaran (Cover Letter) yang siap kirim tanpa format markdown asterisks:
"""
        raw_output = self._call_gemini(user_prompt, system_instruction=system_prompt)
        return clean_markdown_slop(raw_output)

    def generate_follow_up(self, company: str, position: str, lang: str = "id") -> str:
        """Menghasilkan draf email follow-up lamaran yang sopan dan profesional."""
        from src.follow_up import generate_follow_up_prompt, generate_default_follow_up
        prompt = generate_follow_up_prompt(company, position, lang=lang)
        system_prompt = "Kamu adalah pelamar kerja profesional yang sopan dan percaya diri."
        try:
            return self._call_gemini(prompt, system_instruction=system_prompt)
        except Exception:
            return generate_default_follow_up(company, position, lang=lang)

    def screen_job_qualification(self, position: str, job_description: str) -> Dict[str, Any]:
        """Menganalisa apakah lowongan kerja ini cocok dengan kualifikasi CV kandidat."""
        system_prompt = (
            "Kamu adalah Senior Technical Recruiter. Evaluasi kecocokan antara profil kandidat dengan deskripsi pekerjaan. "
            "Kandidat cocok jika memiliki skill yang overlap dengan kebutuhan posisi (Frontend, Fullstack, Python, AI/LLM, Flutter, Media/API). "
            "Kembalikan HANYA format JSON valid tanpa markdown formatting: "
            '{"score": <0-100>, "is_match": <true/false>, "reason": "<alasan ringkas>"}'
        )

        user_prompt = f"""
Profil Kandidat:
{CANDIDATE_SUMMARY}

Posisi: {position}
Deskripsi Pekerjaan:
{job_description}

Berikan skor kecocokan 0-100. Jika score >= 50, set is_match true.
"""
        response_text = self._call_gemini(user_prompt, system_instruction=system_prompt)
        # Parse JSON
        try:
            cleaned = re.sub(r"^```json\s*|\s*```$", "", response_text.strip(), flags=re.MULTILINE)
            return json.loads(cleaned)
        except Exception:
            return {"score": 70, "is_match": True, "reason": "Evaluasi otomatis disetujui (fallback)"}

    def answer_screening_question(self, question_text: str, field_type: str = "text", options: Optional[List[str]] = None) -> str:
        """Menjawab pertanyaan screening lowongan kerja secara otomatis berdasarkan profil CV."""
        if not self.api_key:
            if field_type == "number":
                return "2"
            if options and len(options) > 0:
                return options[0]
            return "Yes"

        system_prompt = (
            "Kamu adalah asisten pengisi formulir lamaran kerja otomatis. "
            "Jawab pertanyaan screening dengan sangat ringkas dan akurat berdasarkan profil kandidat. "
            "Kandidat: Lulusan S1 Informatika, pengalaman 2+ tahun (Fullstack Web, Python, AI/LLM, Flutter, MediaPipe/CUDA). "
            "PENTING: Hanya berikan jawaban intinya saja tanpa penjelasan tambahan!"
        )

        user_prompt = f"""
Pertanyaan Form: {question_text}
Tipe Input: {field_type}
Opsi Pilihan (jika ada): {options or 'Tidak ada'}

Instruksi format output:
- Jika tipe 'number': Kembalikan HANYA angka (contoh: 2).
- Jika tipe 'choice': Kembalikan HANYA teks salah satu opsi yang paling tepat dari pilihan di atas.
- Jika pertanyaan terkait 'work authorization' atau 'legal right to work': Jawab Yes / Ya.
- Jika pertanyaan terkait 'notice period': Jawab Immediately / Segera / 1 month.
- Jika tipe teks bebas: Kembalikan jawaban 1 kalimat padat.
"""
        try:
            ans = self._call_gemini(user_prompt, system_instruction=system_prompt)
            clean_ans = ans.strip(" \n\"'*`")
            if options:
                # Match closest option
                for opt in options:
                    if opt.lower() in clean_ans.lower() or clean_ans.lower() in opt.lower():
                        return opt
            return clean_ans
        except Exception:
            if field_type == "number":
                return "2"
            if options and len(options) > 0:
                return options[0]
            return "Yes"
