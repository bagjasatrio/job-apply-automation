from src.target_roles import (
    CORE_JOB_TITLES,
    EXPANDED_JOB_TITLES,
    get_indonesia_queries,
    get_global_remote_queries,
    is_target_role
)

def test_target_roles_count():
    assert len(CORE_JOB_TITLES) == 35
    # Expanded should include junior & entry level variants
    assert len(EXPANDED_JOB_TITLES) >= 70

    # Test key roles exist
    titles_lower = [t.lower() for t in EXPANDED_JOB_TITLES]
    assert any("ai engineer" in t for t in titles_lower)
    assert any("junior" in t and "devops" in t for t in titles_lower)
    assert any("entry level" in t and "software engineer" in t for t in titles_lower)
    assert any("laravel" in t for t in titles_lower)
    assert any("qa automation" in t for t in titles_lower)
    assert any("multimedia" in t for t in titles_lower)

    # Test newly added roles
    assert any("programmer" in t for t in titles_lower)
    assert any("system analyst" in t for t in titles_lower)
    assert any("data analyst" in t for t in titles_lower)
    assert any("technical writer" in t for t in titles_lower)
    assert any("database administrator" in t for t in titles_lower)
    assert any("it consultant" in t for t in titles_lower)
    assert any("software tester" in t for t in titles_lower)

def test_queries_generation():
    id_q = get_indonesia_queries()
    global_q = get_global_remote_queries()

    assert len(id_q) >= 35
    assert len(global_q) >= 35
    assert any("kirim cv" in q for q in id_q)
    assert any("remote" in q or "worldwide" in q for q in global_q)

def test_is_target_role():
    assert is_target_role("Junior Python Developer") is True
    assert is_target_role("Entry Level AI Engineer") is True
    assert is_target_role("Laravel Backend Developer") is True
    assert is_target_role("Junior System Analyst") is True
    assert is_target_role("Database Administrator") is True
    assert is_target_role("Technical Writer") is True
    assert is_target_role("Sales Manager") is False
