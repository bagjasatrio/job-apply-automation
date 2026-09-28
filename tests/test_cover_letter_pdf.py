import os
from src.tailor.cover_letter_pdf import build_cover_letter_pdf

def test_build_cover_letter_pdf(tmp_path):
    output_pdf = str(tmp_path / "Cover_Letter_Test.pdf")
    body_text = (
        "Berdasarkan informasi lowongan yang saya peroleh, saya bermaksud mengajukan lamaran "
        "untuk posisi Software Engineer di PT Inovasi Digital.\n\n"
        "Saya memiliki latar belakang S1 Teknik Informatika dan pengalaman dalam pengembangan "
        "aplikasi web full-stack, integrasi LLM multi-provider, serta otomasi berbasis Python."
    )

    result_path = build_cover_letter_pdf(
        company="PT Inovasi Digital",
        position="Software Engineer",
        body_text=body_text,
        output_path=output_pdf,
        lang="id"
    )

    assert os.path.exists(result_path)
    assert result_path.endswith(".pdf")
    assert os.path.getsize(result_path) > 1000
