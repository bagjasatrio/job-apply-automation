import random
from typing import List

# 35 Core Job Titles Utama yang Ditargetkan
CORE_JOB_TITLES = [
    # 1. AI, Data & Automation
    "AI Engineer",
    "LLM Application Developer",
    "Generative AI Developer",
    "AI Integration Engineer",
    "AI Automation Engineer",
    "Prompt Engineer",
    "Data Analyst",
    "Video / Multimedia Software Developer",

    # 2. Software, Web & Backend Engineering
    "Programmer",
    "Software Engineer",
    "Full-Stack Web Developer",
    "Web Developer",
    "Frontend Developer",
    "Backend Developer",
    "Python Developer",
    "Laravel Developer",
    "Application Developer",

    # 3. Mobile Development
    "Flutter Developer",
    "Mobile App Developer",

    # 4. Systems, Integration & API
    "API Integration Engineer",
    "API Support Engineer",
    "Software Implementation Engineer",
    "System Analyst",
    "IT Business Analyst",
    "IT Consultant",

    # 5. QA, Testing & DevOps
    "QA Automation Engineer",
    "Software Tester",
    "DevOps Engineer",
    "Release Engineer",

    # 6. IT Support, Admin & Documentation
    "Application Support Developer",
    "Technical Support Engineer",
    "IT Support",
    "Web Administrator",
    "Database Administrator",
    "Technical Writer"
]

# Pastikan daftar unik dan berjumlah tepat 35
CORE_JOB_TITLES = list(dict.fromkeys(CORE_JOB_TITLES))

def generate_expanded_roles() -> List[str]:
    expanded = set()
    for title in CORE_JOB_TITLES:
        expanded.add(title)
        expanded.add(f"Junior {title}")
        expanded.add(f"Entry Level {title}")
        expanded.add(f"Associate {title}")
        expanded.add(f"Fresh Graduate {title}")
    return sorted(list(expanded))

EXPANDED_JOB_TITLES = generate_expanded_roles()

def get_indonesia_queries() -> List[str]:
    queries = []
    # Pola pencarian Indonesia
    for title in CORE_JOB_TITLES:
        queries.append(f'"{title}" "kirim cv" "@gmail.com"')
        queries.append(f'"{title}" "recruitment@" "indonesia"')
        queries.append(f'"junior {title}" "kirim cv"')
        queries.append(f'"fresh graduate" "{title}" "kirim cv"')
    return queries

def get_global_remote_queries() -> List[str]:
    queries = []
    # Pola pencarian Worldwide Remote
    for title in CORE_JOB_TITLES:
        queries.append(f'"{title}" "worldwide remote" "send resume to"')
        queries.append(f'"junior {title}" "remote" "send resume to"')
        queries.append(f'"entry level {title}" "work from anywhere" "apply"')
        queries.append(f'"{title}" "remote" "send cv to"')
    return queries

JOB_CLUSTERS = {
    "all": CORE_JOB_TITLES,
    "ai_data": [
        "AI Engineer", "LLM Application Developer", "Generative AI Developer",
        "Python Developer", "Data Analyst", "Prompt Engineer"
    ],
    "web_backend": [
        "Full-Stack Web Developer", "Laravel Developer", "Backend Developer",
        "Frontend Developer", "Programmer", "Web Developer", "Software Engineer"
    ],
    "mobile": [
        "Flutter Developer", "Mobile App Developer", "Application Developer"
    ],
    "qa_devops": [
        "QA Automation Engineer", "Software Tester", "DevOps Engineer", "Release Engineer"
    ],
    "systems_support": [
        "System Analyst", "IT Business Analyst", "IT Support",
        "Technical Support Engineer", "Database Administrator", "IT Consultant"
    ]
}

def get_sample_keywords(cluster_key: str = "all", count: int = 1) -> List[str]:
    pool = JOB_CLUSTERS.get(cluster_key, CORE_JOB_TITLES)
    sample_size = min(count, len(pool))
    return random.sample(pool, sample_size)

def is_target_role(role_name: str) -> bool:
    r_lower = role_name.lower()
    for title in CORE_JOB_TITLES:
        t_clean = title.lower().replace("developer", "").replace("engineer", "").strip()
        if t_clean and t_clean in r_lower:
            return True
        if title.lower() in r_lower:
            return True
    return False
