from src.templates.email_styler import render_html_cover_letter

def test_render_html_cover_letter():
    body = (
        "Saya bermaksud melamar untuk posisi Fullstack Developer di PT Solusi Jaya.\n\n"
        "Saya memiliki pengalaman 2+ tahun dalam rekayasa perangkat lunak dan integrasi AI."
    )
    html = render_html_cover_letter(body, position="Fullstack Developer", company="PT Solusi Jaya", lang="id")

    assert "<!DOCTYPE html>" in html
    assert "PT Solusi Jaya" in html
    assert "Fullstack Developer" in html
    assert "bagjasatrio.vercel.app" in html
    assert "linkedin.com/in/muhammadbagjasatrio" in html
    assert "Muhammad Bagja Satrio" in html
