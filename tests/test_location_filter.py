from src.security.location_filter import is_location_acceptable

def test_java_wfo_hybrid_remote_allowed():
    # Di pulau Jawa bebas: WFO, Hybrid, Remote boleh semua
    assert is_location_acceptable("Backend Developer WFO di Jakarta Selatan")[0] is True
    assert is_location_acceptable("Frontend Engineer Hybrid di Bandung")[0] is True
    assert is_location_acceptable("Python Developer penempatan Semarang")[0] is True
    assert is_location_acceptable("Fullstack Dev WFO Cirebon")[0] is True
    assert is_location_acceptable("Web Developer Surabaya Onsite")[0] is True

def test_non_java_wfo_hybrid_rejected():
    # Luar Jawa jika WFO / Onsite / Hybrid WAJIB SKIP
    assert is_location_acceptable("Mobile Developer WFO di Medan Sumatera Utara")[0] is False
    assert is_location_acceptable("IT Support penempatan Balikpapan Kalimantan Timur onsite")[0] is False
    assert is_location_acceptable("Software Engineer Hybrid di Denpasar Bali")[0] is False
    assert is_location_acceptable("QA Tester penempatan Makassar Sulawesi WFO")[0] is False
    assert is_location_acceptable("System Analyst penempatan Batam Kepri")[0] is False

def test_non_java_remote_allowed():
    # Luar Jawa HANYA jika Remote / WFH
    assert is_location_acceptable("Software Engineer PT Bali Tech. Remote / WFH dari mana saja")[0] is True
    assert is_location_acceptable("Backend Dev perusahaan di Medan. 100% Remote")[0] is True
    assert is_location_acceptable("Data Analyst Batam Startup. Work From Home")[0] is True

def test_overseas_remote_allowed_onsite_rejected():
    # Luar negeri hanya remote
    assert is_location_acceptable("Python Engineer Singapore Remote")[0] is True
    assert is_location_acceptable("Fullstack Dev US Startup Worldwide Remote")[0] is True
    assert is_location_acceptable("Software Engineer Onsite Singapore Relocation")[0] is False
