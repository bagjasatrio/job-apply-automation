from unittest.mock import patch, MagicMock
from src.ai_assistant import AIAssistant

def test_generate_cover_letter_mock():
    assistant = AIAssistant(api_key="mock_key")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Yth. HRD PT Tech, ini cover letter saya..."}]
                }
            }]
        }
        text = assistant.generate_cover_letter(
            company="PT Tech",
            position="Backend Developer",
            job_description="Requirements: Python, REST API, Database",
            lang="id"
        )
        assert "PT Tech" in text
        assert mock_post.called

def test_screen_job_qualification_mock():
    assistant = AIAssistant(api_key="mock_key")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"score": 85, "is_match": true, "reason": "Kandidat menguasai Python dan API."}'}]
                }
            }]
        }
        res = assistant.screen_job_qualification(
            position="Python AI Developer",
            job_description="Mencari engineer dengan pengalaman Python dan integrasi LLM."
        )
        assert res["score"] == 85
        assert res["is_match"] is True
