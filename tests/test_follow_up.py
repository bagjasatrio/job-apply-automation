from datetime import datetime, timedelta
from src.follow_up import find_stale_applications, generate_follow_up_prompt

def test_find_stale_applications():
    seven_days_ago = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

    records = [
        {
            "Company": "Stale Corp",
            "Position": "Python Dev",
            "Channel": "Email",
            "Contact": "hr@stalecorp.com",
            "Date Applied": seven_days_ago,
            "Status": "Applied",
            "Notes": "Initial email sent"
        },
        {
            "Company": "Recent Corp",
            "Position": "Fullstack",
            "Channel": "Email",
            "Contact": "hr@recentcorp.com",
            "Date Applied": two_days_ago,
            "Status": "Applied",
            "Notes": "Just applied"
        },
        {
            "Company": "Already Followed Corp",
            "Position": "Dev",
            "Channel": "Email",
            "Contact": "hr@followed.com",
            "Date Applied": seven_days_ago,
            "Status": "Applied",
            "Notes": "Followed-up on 2026-09-20"
        },
        {
            "Company": "Interviewing Corp",
            "Position": "Dev",
            "Channel": "Email",
            "Contact": "hr@interview.com",
            "Date Applied": seven_days_ago,
            "Status": "On Progress",
            "Notes": "Interview"
        }
    ]

    stale = find_stale_applications(records, days_threshold=5)
    assert len(stale) == 1
    assert stale[0]["Company"] == "Stale Corp"

def test_generate_follow_up_prompt():
    prompt = generate_follow_up_prompt("Tech Corp", "Software Engineer", lang="id")
    assert "Tech Corp" in prompt
    assert "Software Engineer" in prompt
    assert "Bahasa Indonesia" in prompt
