Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\project\automation job"
WshShell.Run """C:\project\automation job\.venv\Scripts\python.exe"" ""C:\project\automation job\src\notifier\telegram_bot.py""", 0, False
