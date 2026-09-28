from unittest.mock import patch
from src.ai_assistant import AIAssistant

def test_answer_screening_question_years():
    ai = AIAssistant(api_key="mock_key")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "2"}]
                }
            }]
        }
        ans = ai.answer_screening_question("How many years of experience do you have with Python?", field_type="number")
        assert ans == "2"

def test_answer_screening_question_choice():
    ai = AIAssistant(api_key="mock_key")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Yes"}]
                }
            }]
        }
        ans = ai.answer_screening_question(
            "Are you willing to work in a hybrid setup?",
            field_type="choice",
            options=["Yes", "No"]
        )
        assert ans == "Yes"
