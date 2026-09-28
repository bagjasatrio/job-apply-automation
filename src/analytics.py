from typing import List, Dict, Any

def compute_application_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    if total == 0:
        return {
            "total": 0,
            "counts": {"Applied": 0, "On Progress": 0, "Rejected": 0, "Offering": 0},
            "response_rate": 0.0,
            "interview_rate": 0.0,
            "offer_rate": 0.0,
            "channels": {}
        }

    counts = {"Applied": 0, "On Progress": 0, "Rejected": 0, "Offering": 0}
    channels: Dict[str, Dict[str, int]] = {}

    for r in records:
        st = str(r.get("Status", "Applied")).strip()
        ch = str(r.get("Channel", "Other")).strip() or "Other"

        if st in counts:
            counts[st] += 1
        else:
            counts["Applied"] += 1

        if ch not in channels:
            channels[ch] = {"total": 0, "interviews": 0, "offers": 0}
        channels[ch]["total"] += 1

        if st in ["On Progress", "Offering"]:
            channels[ch]["interviews"] += 1
        if st == "Offering":
            channels[ch]["offers"] += 1

    interviews = counts["On Progress"] + counts["Offering"]
    responses = interviews + counts["Rejected"]

    response_rate = round((responses / total) * 100, 1)
    interview_rate = round((interviews / total) * 100, 1)
    offer_rate = round((counts["Offering"] / total) * 100, 1)

    return {
        "total": total,
        "counts": counts,
        "response_rate": response_rate,
        "interview_rate": interview_rate,
        "offer_rate": offer_rate,
        "channels": channels
    }

def format_analytics_dashboard(metrics: Dict[str, Any]) -> str:
    total = metrics["total"]
    if total == 0:
        return "Belum ada data pelamaran untuk dianalisa."

    counts = metrics["counts"]
    channels = metrics["channels"]

    lines = [
        "=" * 60,
        "       ANALYTICS & CONVERSION RATE DASHBOARD",
        "=" * 60,
        f"Total Lamaran Dikirim  : {total}",
        f"Sedang Diproses        : {counts['Applied']}",
        f"Wawancara / Tes Teknis : {counts['On Progress']}",
        f"Ditolak (Rejected)     : {counts['Rejected']}",
        f"Diterima (Offering)    : {counts['Offering']}",
        "-" * 60,
        "KEY CONVERSION METRICS:",
        f"- HR Response Rate     : {metrics['response_rate']}%",
        f"- Apply-to-Interview   : {metrics['interview_rate']}%",
        f"- Final Offer Rate     : {metrics['offer_rate']}%",
        "-" * 60,
        "PERFORMA PER CHANNEL:",
        f"{'Channel':<15} | {'Total':<8} | {'Interviews':<12} | {'Win Rate':<10}",
        "-" * 60
    ]

    for ch, data in channels.items():
        win_rate = round((data["interviews"] / data["total"]) * 100, 1) if data["total"] > 0 else 0.0
        lines.append(f"{ch:<15} | {data['total']:<8} | {data['interviews']:<12} | {win_rate}%")

    lines.append("=" * 60)
    return "\n".join(lines)
