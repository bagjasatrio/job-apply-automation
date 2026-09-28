import os
from unittest.mock import patch
from src.tailor.resume_tailor import ResumeTailor

def test_generate_tailored_pdf(tmp_path):
    tailor = ResumeTailor(output_dir=str(tmp_path))

    with patch.object(tailor, "extract_keywords_and_summary") as mock_tailor:
        mock_tailor.return_value = {
            "keywords": ["Python", "FastAPI", "Docker", "REST API"],
            "summary": "Fullstack Python Engineer with specialized experience in REST APIs and AI integration."
        }

        pdf_path = tailor.build_tailored_resume(
            company="Startup Inc",
            position="Backend Engineer",
            job_description="Seeking a Python Engineer skilled in FastAPI and Docker.",
            lang="en"
        )

        assert os.path.exists(pdf_path)
        assert pdf_path.endswith(".pdf")
        assert os.path.getsize(pdf_path) > 1000
