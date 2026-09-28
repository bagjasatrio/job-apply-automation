import html
from src.templates.text_sanitizer import clean_markdown_slop

def render_html_cover_letter(body_text: str, position: str, company: str, lang: str = "id") -> str:
    """Merender surat lamaran ke dalam format email HTML modern, elegan, dan responsif."""
    clean_body = clean_markdown_slop(body_text)
    paragraphs = [p.strip() for p in clean_body.split("\n\n") if p.strip()]
    formatted_paragraphs = "".join([f"<p style='margin: 0 0 16px 0; line-height: 1.65; color: #374151;'>{html.escape(p).replace(chr(10), '<br/>')}</p>" for p in paragraphs])

    is_en = (lang == "en")

    badge_text = "Curriculum Vitae & Job Application" if is_en else "Berkas Lamaran Kerja & CV"
    highlights_title = "Candidate Highlights & Portfolio" if is_en else "Ringkasan Kualifikasi & Portofolio"
    sub_title = f"Target Position: <strong style='color: #ffffff;'>{html.escape(position)}</strong> at {html.escape(company)}" if is_en else f"Target Posisi: <strong style='color: #ffffff;'>{html.escape(position)}</strong> di {html.escape(company)}"

    # Credentials Box Items
    if is_en:
        edu_label = "Education:"
        edu_val = "Bachelor of Computer Science (Universitas Dian Nuswantoro), GPA 3.29"
        skills_label = "Core Competencies:"
        skills_val = "Python, Full-Stack Web Development, REST APIs, Multi-Provider AI/LLM Gateway"
        proj_label = "Featured Portfolio:"
        proj_val = "ClipMax (Desktop AI Video Clipper), ClipMax Mobile (Flutter On-Device AI)"
        cert_label = "Certifications:"
        cert_val = "5 IBM Professional Certifications in AI & Software Engineering"
        btn_portfolio = "View Portfolio Website"
        btn_linkedin = "LinkedIn Profile"
    else:
        edu_label = "Pendidikan:"
        edu_val = "S1 Teknik Informatika (Universitas Dian Nuswantoro), IPK 3.29"
        skills_label = "Keahlian Utama:"
        skills_val = "Python, Pengembangan Web Full-Stack, REST API, Multi-Provider AI/LLM Gateway"
        proj_label = "Portofolio Unggulan:"
        proj_val = "ClipMax (Desktop AI Video Clipper), ClipMax Mobile (Flutter On-Device AI)"
        cert_label = "Sertifikasi:"
        cert_val = "5 Sertifikasi Profesional IBM Bidang AI & Software Engineering"
        btn_portfolio = "Buka Website Portofolio"
        btn_linkedin = "Profil LinkedIn"

    html_template = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Application for {html.escape(position)}</title>
</head>
<body style="margin: 0; padding: 24px 12px; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 620px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    <!-- Header -->
    <tr>
      <td style="padding: 28px 32px; background-color: #1e3a8a; color: #ffffff;">
        <span style="display: inline-block; padding: 4px 10px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background-color: rgba(255,255,255,0.15); border-radius: 4px; margin-bottom: 8px;">{badge_text}</span>
        <h1 style="margin: 0; font-size: 20px; font-weight: 700; line-height: 1.3;">Muhammad Bagja Satrio</h1>
        <p style="margin: 4px 0 0 0; font-size: 13px; color: #cbd5e1;">{sub_title}</p>
      </td>
    </tr>

    <!-- Body Content -->
    <tr>
      <td style="padding: 32px 32px 20px 32px; font-size: 14.5px;">
        {formatted_paragraphs}

        <!-- Highlight Credentials Box -->
        <div style="margin: 24px 0; padding: 18px 20px; background-color: #f8fafc; border-left: 4px solid #2563eb; border-radius: 0 6px 6px 0;">
          <h3 style="margin: 0 0 8px 0; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #1e3a8a;">{highlights_title}</h3>
          <ul style="margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.6; color: #4b5563;">
            <li><strong>{edu_label}</strong> {edu_val}</li>
            <li><strong>{skills_label}</strong> {skills_val}</li>
            <li><strong>{proj_label}</strong> {proj_val}</li>
            <li><strong>{cert_label}</strong> {cert_val}</li>
          </ul>
        </div>

        <!-- Action Links -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
          <tr>
            <td style="padding-right: 12px;">
              <a href="https://bagjasatrio.vercel.app" target="_blank" style="display: inline-block; padding: 10px 18px; background-color: #2563eb; color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 600; border-radius: 6px;">{btn_portfolio}</a>
            </td>
            <td>
              <a href="https://linkedin.com/in/muhammadbagjasatrio" target="_blank" style="display: inline-block; padding: 9px 16px; background-color: #ffffff; color: #2563eb; border: 1px solid #2563eb; text-decoration: none; font-size: 13px; font-weight: 600; border-radius: 6px;">{btn_linkedin}</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- Footer -->
    <tr>
      <td style="padding: 20px 32px; background-color: #f9fafb; border-top: 1px solid #f3f4f6; font-size: 12px; color: #6b7280; text-align: center;">
        <p style="margin: 0 0 4px 0;">Email: <a href="mailto:muhammad.bagjasatrio28@gmail.com" style="color: #2563eb; text-decoration: none;">muhammad.bagjasatrio28@gmail.com</a> | WhatsApp/Telp: +62 812-2068-4832</p>
        <p style="margin: 0; color: #9ca3af;">Losari, Cirebon, Jawa Barat, 45192, Indonesia</p>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return html_template
