import os
import csv
from datetime import datetime
from typing import Optional

HEADERS = ["Company", "Position", "Channel", "Contact", "Date Applied", "Status", "Notes"]

def create_backup(tracker, output_dir: str = "backups") -> str:
    """Mengekspor seluruh riwayat database lamaran kerja ke file CSV backup bertanda waktu."""
    abs_dir = os.path.abspath(output_dir)
    os.makedirs(abs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"job_applications_backup_{timestamp}.csv"
    filepath = os.path.join(abs_dir, filename)

    records = tracker.get_tracked_companies()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for r in records:
            # Pastikan hanya field di HEADERS yang ditulis
            row = {k: r.get(k, "") for k in HEADERS}
            writer.writerow(row)

    return filepath
