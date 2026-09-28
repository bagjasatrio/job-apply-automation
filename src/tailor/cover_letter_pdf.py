import os
import re
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

MONTHS_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

def format_date_id(dt: datetime) -> str:
    return f"{dt.day} {MONTHS_ID[dt.month]} {dt.year}"

def build_cover_letter_pdf(
    company: str,
    position: str,
    body_text: str,
    output_path: Optional[str] = None,
    lang: str = "id"
) -> str:
    """Membuat dokumen PDF Surat Lamaran Kerja (Cover Letter) resmi berstandar profesional."""
    if not output_path:
        out_dir = os.path.abspath("tailored_resumes")
        os.makedirs(out_dir, exist_ok=True)
        safe_comp = re.sub(r"[^a-zA-Z0-9_-]", "_", company.title())[:20].strip("_")
        safe_pos = re.sub(r"[^a-zA-Z0-9_-]", "_", position.title())[:20].strip("_")
        if safe_pos.lower() == "it":
            safe_pos = "IT"

        doc_prefix = "Cover_Letter" if lang == "en" else "Surat_Lamaran"
        output_path = os.path.join(out_dir, f"{doc_prefix}_Muhammad_Bagja_Satrio_{safe_comp}_{safe_pos}.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    header_name_style = ParagraphStyle(
        "HeaderName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1
    )
    header_contact_style = ParagraphStyle(
        "HeaderContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor("#4b5563"),
        alignment=1
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=15,
        textColor=colors.HexColor("#1f2937")
    )
    body_style = ParagraphStyle(
        "LetterBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=10
    )

    story = []

    # 1. KOP SURAT (Letterhead)
    story.append(Paragraph("MUHAMMAD BAGJA SATRIO", header_name_style))
    story.append(Spacer(1, 3))
    contacts = "Losari, Cirebon, Jawa Barat, 45192 | +62 812-2068-4832 | muhammad.bagjasatrio28@gmail.com | bagjasatrio.vercel.app"
    story.append(Paragraph(contacts, header_contact_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=14))

    # 2. TANGGAL & PERIHAL
    now = datetime.now()
    date_str = f"Cirebon, {format_date_id(now)}" if lang == "id" else f"Cirebon, {now.strftime('%B %d, %Y')}"
    subject_str = f"<b>Perihal:</b> Lamaran Pekerjaan — {position}" if lang == "id" else f"<b>Subject:</b> Job Application for {position}"

    story.append(Paragraph(f"<div align='right'>{date_str}</div>", meta_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(subject_str, meta_style))
    story.append(Spacer(1, 8))

    # 3. TUJUAN SURAT
    if lang == "id":
        recipient_html = f"Kepada Yth.<br/><b>Tim HRD / Rekruter</b><br/>{company}<br/>Di Tempat"
    else:
        recipient_html = f"To:<br/><b>Hiring Manager / Recruitment Team</b><br/>{company}"
    story.append(Paragraph(recipient_html, meta_style))
    story.append(Spacer(1, 14))

    # 4. SALAM PEMBUKA
    salutation = "Dengan hormat," if lang == "id" else "Dear Hiring Team,"
    story.append(Paragraph(f"<b>{salutation}</b>", meta_style))
    story.append(Spacer(1, 6))

    # 5. ISI BADAN SURAT
    paragraphs = [p.strip() for p in body_text.split("\n\n") if p.strip()]
    for p in paragraphs:
        # Bersihkan format salam pembuka/penutup ganda jika ada di body text
        if any(p.lower().startswith(s) for s in ["kepada yth", "dear hiring", "hormat saya", "sincerely", "dengan hormat"]):
            continue
        story.append(Paragraph(p, body_style))

    story.append(Spacer(1, 14))

    # 6. PENUTUP & TANDA TANGAN
    closing_title = "Hormat saya," if lang == "id" else "Sincerely,"
    story.append(Paragraph(closing_title, meta_style))
    story.append(Spacer(1, 28))  # Ruang tanda tangan
    story.append(Paragraph("<b>Muhammad Bagja Satrio</b>", meta_style))

    doc.build(story)
    return output_path
