from src.target_roles import JOB_CLUSTERS, CORE_JOB_TITLES, get_sample_keywords

def test_job_clusters_exist():
    assert "ai_data" in JOB_CLUSTERS
    assert "web_backend" in JOB_CLUSTERS
    assert "mobile" in JOB_CLUSTERS
    assert "qa_devops" in JOB_CLUSTERS
    assert "systems_support" in JOB_CLUSTERS

def test_get_sample_keywords():
    kw_all = get_sample_keywords("all", count=3)
    assert len(kw_all) == 3
    assert all(k in CORE_JOB_TITLES for k in kw_all)

    kw_ai = get_sample_keywords("ai_data", count=2)
    assert len(kw_ai) == 2
    assert all(k in JOB_CLUSTERS["ai_data"] for k in kw_ai)
