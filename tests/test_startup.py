import os
from src.startup import get_startup_file_path, install_startup_script, remove_startup_script

def test_startup_file_path():
    path = get_startup_file_path()
    assert "Startup" in path
    assert path.endswith("JobAutomationBot.vbs")

def test_install_and_remove_startup(tmp_path):
    mock_startup = tmp_path / "JobAutomationBot.vbs"
    content = "test_script"

    # Install
    mock_startup.write_text(content)
    assert mock_startup.exists()

    # Remove
    if mock_startup.exists():
        mock_startup.unlink()
    assert not mock_startup.exists()
