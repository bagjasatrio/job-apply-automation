import os
import sys
from typing import Optional

STARTUP_SCRIPT_NAME = "JobAutomationBot.vbs"

def get_startup_dir() -> str:
    appdata = os.getenv("APPDATA")
    if not appdata:
        appdata = os.path.expanduser(r"~\AppData\Roaming")
    return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")

def get_startup_file_path() -> str:
    return os.path.join(get_startup_dir(), STARTUP_SCRIPT_NAME)

def is_startup_installed() -> bool:
    return os.path.exists(get_startup_file_path())

def install_startup_script(project_dir: Optional[str] = None) -> str:
    """Memasang script silent launcher ke folder Windows Startup agar bot aktif otomatis saat PC/laptop menyala."""
    if not project_dir:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    python_exe = os.path.join(project_dir, r".venv\Scripts\python.exe")
    bot_script = os.path.join(project_dir, r"src\notifier\telegram_bot.py")

    vbs_content = f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{project_dir}"
WshShell.Run \"\""{python_exe}\"\" \"\"{bot_script}\"\"\", 0, False
"""
    dest_path = get_startup_file_path()
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    return dest_path

def remove_startup_script() -> bool:
    """Menghapus script dari folder Windows Startup."""
    path = get_startup_file_path()
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

if __name__ == "__main__":
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "install"
    if action == "install":
        p = install_startup_script()
        print(f"Berhasil dipasang di Windows Startup: {p}")
    elif action == "remove":
        removed = remove_startup_script()
        print("Berhasil dihapus dari Windows Startup." if removed else "File startup tidak ditemukan.")
    elif action == "status":
        print("Status Startup:", "Terpasang (Aktif)" if is_startup_installed() else "Belum Terpasang")
