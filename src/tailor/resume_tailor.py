import os
import re
import json
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from src.ai_assistant import AIAssistant, CANDIDATE_SUMMARY

class ResumeTailor:
    def __init__(self, output_dir: str = "tailored_resumes", api_key: Optional[str] = None):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.ai = AIAssistant(api_key=api_key)

    def extract_keywords_and_summary(self, company: str, position: str, job_description: str, lang: str = "id") -> Dict[str, Any]:
        """Ekstrak exact keywords ATS dan buat ringkasan profil yang disesuaikan via Gemini."""
        if not self.ai.api_key or not job_description:
            return {
                "keywords": ["Python", "REST API", "Full-Stack Development", "LLM Integration", "Git"],
                "summary": "Full-Stack Developer dengan spesialisasi pengembangan web modern, arsitektur REST API, dan integrasi Artificial Intelligence (LLM). Terbiasa membangun solusi perangkat lunak modular dan berkinerja tinggi."
            }

        lang_instruction = "Gunakan Bahasa Indonesia formal." if lang == "id" else "Write in professional English."
        prompt = f"""
Profil Kandidat:
{CANDIDATE_SUMMARY}

Target Perusahaan: {company}
Posisi: {position}
Deskripsi Lowongan:
{job_description}

Instruksi:
1. Ekstrak 5-8 kata kunci teknis (exact ATS keywords) dari deskripsi lowongan yang sesuai dengan keahlian kandidat.
2. Buat 1 paragraf 'Profile Summary' (3-4 kalimat) yang secara natural menyisipkan kata kunci tersebut agar lulus ATS scan untuk posisi ini.
3. {lang_instruction}

Kembalikan HANYA format JSON valid tanpa format markdown:
{{"keywords": ["keyword1", "keyword2", "..."], "summary": "teks ringkasan profil..."}}
"""
        system_prompt = "Kamu adalah spesialis optimasi resume ATS kelas dunia. Kembalikan HANYA valid JSON."
        try:
            raw = self.ai._call_gemini(prompt, system_instruction=system_prompt)
            clean = re.sub(r"^```json\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
            return json.loads(clean)
        except Exception:
            return {
                "keywords": ["Python", "Full-Stack Development", "REST API", "AI Systems", "CI/CD"],
                "summary": f"Software Engineer dengan rekam jejak pengembangan sistem AI dan web full-stack, siap berkontribusi untuk posisi {position} di {company}."
            }

    def build_tailored_resume(self, company: str, position: str, job_description: str = "", lang: str = "id") -> str:
        data = self.extract_keywords_and_summary(company, position, job_description, lang=lang)
        keywords = data.get("keywords", [])
        summary_text = data.get("summary", "")

        safe_comp = re.sub(r"[^a-zA-Z0-9_-]", "_", company.title())[:20].strip("_")
        safe_pos = re.sub(r"[^a-zA-Z0-9_-]", "_", position.title())[:20].strip("_")
        if safe_pos.lower() == "it":
            safe_pos = "IT"

        doc_prefix = "Resume" if lang == "en" else "CV"
        filename = f"{doc_prefix}_Muhammad_Bagja_Satrio_{safe_comp}_{safe_pos}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#111827"),
            alignment=1
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#4b5563"),
            alignment=1
        )
        section_style = ParagraphStyle(
            "Section",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#1e3a8a"),
            spaceBefore=6,
            spaceAfter=3
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1f2937")
        )
        bold_body = ParagraphStyle(
            "BoldBody",
            parent=body_style,
            fontName="Helvetica-Bold"
        )

        story = []

        # Header
        story.append(Paragraph("MUHAMMAD BAGJA SATRIO", title_style))
        story.append(Spacer(1, 2))
        contact_line = "Losari, Cirebon, Jawa Barat | muhammad.bagjasatrio28@gmail.com | +62 812-2068-4832 | linkedin.com/in/muhammadbagjasatrio | bagjasatrio.vercel.app"
        story.append(Paragraph(contact_line, subtitle_style))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1d5db"), spaceAfter=6))

        # Profile Summary (Tailored)
        summary_title = "RINGKASAN PROFIL" if lang == "id" else "PROFILE SUMMARY"
        story.append(Paragraph(summary_title, section_style))
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 4))

        # Technical Skills Section (Professional, Clean, No AI Slop)
        skills_title = "KEAHLIAN TEKNIS" if lang == "id" else "TECHNICAL SKILLS"
        story.append(Paragraph(skills_title, section_style))

        # Deduplicate and clean keywords
        dedup_kw = []
        seen = set()
        for k in keywords:
            clean_k = k.strip()
            if clean_k and clean_k.lower() not in seen and clean_k.lower() not in ["skills", "ats", "keywords"]:
                seen.add(clean_k.lower())
                dedup_kw.append(clean_k)

        if lang == "en":
            story.append(Paragraph("<b>Programming Languages & Frameworks:</b> Python (Flask, FastAPI), PHP (Laravel), Dart (Flutter), JavaScript, SQL", body_style))
            story.append(Paragraph("<b>AI Engineering & Multimodal:</b> LLM Integration, Whisper.cpp, MediaPipe Face Tracking, Computer Vision, FFmpeg NVENC", body_style))
            story.append(Paragraph("<b>Tools & Cloud Architecture:</b> Git, GitHub Actions, Docker, CI/CD, Pytest, Playwright, RESTful APIs", body_style))
            if dedup_kw:
                custom_str = ", ".join(dedup_kw[:6])
                story.append(Paragraph(f"<b>Key Proficiencies:</b> {custom_str}", body_style))
        else:
            story.append(Paragraph("<b>Bahasa Pemrograman & Framework:</b> Python (Flask, FastAPI), PHP (Laravel), Dart (Flutter), JavaScript, SQL", body_style))
            story.append(Paragraph("<b>Teknologi AI & Multimedia:</b> Integrasi LLM, Whisper.cpp, MediaPipe Face Tracking, Computer Vision, FFmpeg NVENC", body_style))
            story.append(Paragraph("<b>Tools & Arsitektur:</b> Git, GitHub Actions, Docker, CI/CD, Pytest, Playwright, RESTful APIs", body_style))
            if dedup_kw:
                custom_str = ", ".join(dedup_kw[:6])
                story.append(Paragraph(f"<b>Keahlian Terkait:</b> {custom_str}", body_style))
        story.append(Spacer(1, 4))

        # Work Experience
        exp_title = "PENGALAMAN KERJA" if lang == "id" else "WORK EXPERIENCE"
        story.append(Paragraph(exp_title, section_style))
        if lang == "en":
            exp_role = "Frontend Web Developer — Department of Communication, Informatics, Statistics & Cryptography of Semarang City (Remote) | Jul 2025 – Aug 2025"
            story.append(Paragraph(f"<b>{exp_role}</b>", body_style))
            story.append(Paragraph("• Developed modular, responsive, and accessible web interfaces for the Semarang City Fire Department.", body_style))
            story.append(Paragraph("• Ensured 100% cross-platform responsiveness across citizen mobile devices and command center desktop dashboards.", body_style))
        else:
            exp_role = "Frontend Website Developer — Dinas Komunikasi, Informatika, Statistik dan Persandian Kota Semarang (Remote) | Jul 2025 – Agu 2025"
            story.append(Paragraph(f"<b>{exp_role}</b>", body_style))
            story.append(Paragraph("• Mengembangkan antarmuka website Dinas Pemadam Kebakaran Kota Semarang secara modular, responsif, dan standar UI ramah akses.", body_style))
            story.append(Paragraph("• Menjamin responsivitas antarmuka 100% pada perangkat mobile warga dan desktop ruang komando.", body_style))
        story.append(Spacer(1, 4))

        # Key Projects
        proj_title = "PROYEK UNGGULAN & PORTOFOLIO" if lang == "id" else "FEATURED PROJECTS"
        story.append(Paragraph(proj_title, section_style))

        if lang == "en":
            story.append(Paragraph("<b>ClipMax — Autonomous Desktop AI Video Clipper (Python, CUDA, Whisper, FFmpeg NVENC)</b>", body_style))
            story.append(Paragraph("• Automated 9:16 vertical video conversion desktop application with Universal LLM Gateway (OpenRouter, Groq, Gemini), face tracking MediaPipe, and 85 automated unit tests.", body_style))

            story.append(Paragraph("<b>ClipMax Mobile — On-Device AI Video Studio (Flutter, Dart FFI, Whisper.cpp)</b>", body_style))
            story.append(Paragraph("• Native on-device mobile video studio with C++ Whisper.cpp transcription, 120 FPS multi-layer timeline editor, and multi-provider AI Router.", body_style))

            story.append(Paragraph("<b>CVKita — AI Career Profile & Resume ATS Optimization Platform</b>", body_style))
            story.append(Paragraph("• Intelligent career profiling and resume optimization platform utilizing automated ATS scoring algorithms.", body_style))
        else:
            story.append(Paragraph("<b>ClipMax — Autonomous Desktop AI Video Clipper (Python, CUDA, Whisper, FFmpeg NVENC)</b>", body_style))
            story.append(Paragraph("• Aplikasi desktop AI konversi video vertikal 9:16 otomatis dengan Universal LLM Gateway (OpenRouter, Groq, Gemini), face tracking MediaPipe, dan 85 automated unit tests.", body_style))

            story.append(Paragraph("<b>ClipMax Mobile — On-Device AI Video Studio (Flutter, Dart FFI, Whisper.cpp)</b>", body_style))
            story.append(Paragraph("• Aplikasi mobile on-device video studio dengan transkripsi native Whisper.cpp C++, multi-layer editor 120 FPS, dan AI Router multi-provider.", body_style))

            story.append(Paragraph("<b>CVKita — AI Career Profile & Resume ATS Optimization Platform</b>", body_style))
            story.append(Paragraph("• Platform cerdas penyesuaian kualifikasi profil karier dan optimasi resume berbasis skor kecocokan ATS.", body_style))
        story.append(Spacer(1, 4))

        # Education & Certifications
        edu_title = "PENDIDIKAN & SERTIFIKASI" if lang == "id" else "EDUCATION & CERTIFICATIONS"
        story.append(Paragraph(edu_title, section_style))
        if lang == "en":
            story.append(Paragraph("<b>Bachelor of Computer Science (Informatics Engineering) — Universitas Dian Nuswantoro</b> (GPA: 3.29) | 2022 – 2026", body_style))
            cert_text = "<b>IBM Professional Certifications (2026):</b> Developing AI Applications with Python & Flask • Python for Data Science & AI • CI/CD • DevOps Capstone Project • Software Engineering Fundamentals"
            story.append(Paragraph(cert_text, body_style))
        else:
            story.append(Paragraph("<b>S1 Teknik Informatika — Universitas Dian Nuswantoro</b> (IPK: 3.29) | 2022 – 2026", body_style))
            cert_text = "<b>Sertifikasi Profesional IBM (2026):</b> Developing AI Applications with Python & Flask • Python for Data Science & AI • CI/CD • DevOps Capstone Project • Software Engineering Fundamentals"
            story.append(Paragraph(cert_text, body_style))

        doc.build(story)
        return filepath
