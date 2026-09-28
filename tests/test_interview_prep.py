import os
from unittest.mock import patch
from src.interview.prep_kit import InterviewPrepKit

def test_generate_prep_kit_mock(tmp_path):
    prep = InterviewPrepKit(output_dir=str(tmp_path), api_key="mock_key")

    with patch.object(prep.ai, "_call_gemini") as mock_gemini:
        mock_gemini.return_value = (
            "# INTERVIEW PREPARATION KIT: Shopee\n\n"
            "## 1. Prediksi Pertanyaan Teknis\n"
            "- Jelaskan arsitektur API Gateway multi-provider.\n"
        )

        file_path = prep.generate_prep_kit(
            company="Shopee",
            position="Backend AI Engineer",
            job_description="Python, REST API, LLM integration"
        )

        assert os.path.exists(file_path)
        assert file_path.endswith(".md")
        content = open(file_path, "r", encoding="utf-8").read()
        assert "Shopee" in content
        assert "Prediksi Pertanyaan" in content
