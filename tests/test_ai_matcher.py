from unittest.mock import patch
from src.matcher.ai_matcher import AIMatcher

def test_ai_matcher_evaluate_job():
    matcher = AIMatcher(api_key="mock_key")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"score": 88, "decision": "APPLY", "matched_skills": ["Python", "REST API", "AI"], "missing_skills": ["Kubernetes"], "reason": "Kandidat sangat cocok dengan kebutuhan backend AI."}'
                    }]
                }
            }]
        }
        result = matcher.match(
            company="Fintech ID",
            position="Python AI Engineer",
            job_description="Butuh engineer Python dengan pengalaman integrasi AI."
        )
        assert result["score"] == 88
        assert result["decision"] == "APPLY"
        assert "Python" in result["matched_skills"]
