import os
import json
import re
from typing import Dict, Any, Optional
import requests

CANDIDATE_PROFILE = """
Nama: Muhammad Bagja Satrio
Pendidikan: S1 Teknik Informatika (Universitas Dian Nuswantoro), GPA 3.29.
Keahlian & Pengalaman:
- Full-Stack Web Development: Python, Flask, Laravel/PHP, REST API, modular UI, PostgreSQL/MySQL, responsive UI (Diskominfo Kota Semarang).
- AI & LLM Engineering: Multi-provider Universal LLM Gateway (OpenAI, OpenRouter, Groq, Gemini), prompt engineering, ATS matching (CVKita).
- Multimedia AI & GPU Acceleration: Faster-Whisper (CUDA), MediaPipe face tracking, FFmpeg NVENC hardware video rendering (ClipMax Desktop, 85 automated tests).
- Mobile & On-Device AI: Flutter/Dart, native Dart FFI, Whisper.cpp on-device audio transcription, 120 FPS video editor (ClipMax Mobile).
- DevOps & Tools: Git, GitHub, Pytest, Playwright automation, Docker basics, CI/CD, 5 sertifikasi IBM.

Target 35 Job Titles (Sangat Cocok untuk Level Junior & Entry-Level):
1. AI Engineer (Junior)
2. LLM Application Developer
3. Generative AI Developer
4. AI Integration Engineer
5. AI Automation Engineer
6. Prompt Engineer
7. Data Analyst
8. Video / Multimedia Software Developer
9. Programmer
10. Software Engineer
11. Junior Software Engineer
12. Full-Stack Web Developer
13. Web Developer
14. Frontend Developer
15. Backend Developer
16. Python Developer
17. Laravel Developer (PHP)
18. Application Developer
19. Flutter Developer
20. Mobile App Developer
21. API Integration Engineer
22. API Support Engineer
23. Software Implementation Engineer
24. System Analyst
25. IT Business Analyst
26. IT Consultant
27. QA Automation Engineer
28. Software Tester
29. DevOps Engineer (Junior)
30. Release Engineer
31. Application Support Developer
32. Technical Support Engineer
33. IT Support
34. Web Administrator
35. Database Administrator
36. Technical Writer
"""

class AIMatcher:
    MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash"]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def match(self, company: str, position: str, job_description: str) -> Dict[str, Any]:
        """Menganalisa kecocokan CV dengan deskripsi lowongan secara mendalam."""
        if not self.api_key:
            return {
                "score": 75,
                "decision": "APPLY",
                "matched_skills": ["Python", "Web Development", "AI"],
                "missing_skills": [],
                "reason": "Evaluasi default tanpa API key"
            }

        system_instruction = (
            "Kamu adalah Senior Technical Recruiter & ATS Evaluator. "
            "Evaluasi kesesuaian antara profil kandidat dan deskripsi pekerjaan secara ketat dan obyektif. "
            "ATURAN LOKASI: Kandidat berbasis di Pulau Jawa (Cirebon, Jabar). "
            "Lowongan di Pulau Jawa (Jakarta, Bandung, Semarang, Surabaya, Cirebon, dll.) boleh WFO, Hybrid, atau Remote. "
            "Lowongan di Luar Pulau Jawa (Sumatera, Kalimantan, Sulawesi, Bali, dll.) atau Luar Negeri WAJIB Remote / WFH. "
            "Jika lowongan di luar Jawa atau luar negeri berformat WFO / Hybrid / Onsite, berikan skor 0 dan decision 'SKIP' dengan alasan lokasi luar Jawa non-remote. "
            "Output WAJIB berupa JSON murni tanpa markdown/backticks dengan schema berikut: "
            '{"score": <0-100>, "decision": "<APPLY/SKIP>", "matched_skills": ["skill1", "skill2"], "missing_skills": ["skillA"], "reason": "<ringkasan 1-2 kalimat>"}'
        )

        user_prompt = f"""
PROFIL KANDIDAT:
{CANDIDATE_PROFILE}

TARGET LOWONGAN:
Perusahaan: {company}
Posisi: {position}
Deskripsi Lowongan / Kualifikasi:
{job_description}

ATURAN PENILAIAN:
- Jika score >= 50, set decision 'APPLY'.
- Jika score < 50, set decision 'SKIP'.
- Tulis matched_skills dan missing_skills yang relevan.
"""
        headers = {"Content-Type": "application/json"}
        for model in self.MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": user_prompt}]}],
                "systemInstruction": {"parts": [{"text": system_instruction}]}
            }
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=25)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        clean_json = re.sub(r"^```json\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
                        parsed = json.loads(clean_json)
                        # Pastikan format standar
                        parsed["score"] = int(parsed.get("score", 70))
                        parsed["decision"] = "APPLY" if parsed["score"] >= 50 else "SKIP"
                        return parsed
            except Exception:
                continue

        # Fallback jika jaringan bermasalah
        return {
            "score": 75,
            "decision": "APPLY",
            "matched_skills": ["Fullstack", "Python", "AI"],
            "missing_skills": [],
            "reason": "Gagal parse dari LLM, fallback ke nilai default"
        }
