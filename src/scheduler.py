import os
import time
import uuid
import threading
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any
from src.models import JobStatus
from src.follow_up import find_stale_applications
from src.security.lead_cache import LeadCache
from src.scraper.hr_leads_scraper import HRLeadsScraper

class PeriodicTaskRunner:
    def __init__(self, interval_seconds: int = 7200):
        self.interval_seconds = interval_seconds
        self.last_run_timestamp: float = 0.0

    def is_due(self) -> bool:
        if self.last_run_timestamp == 0.0:
            return True
        return (time.time() - self.last_run_timestamp) >= self.interval_seconds

    def mark_executed(self):
        self.last_run_timestamp = time.time()

    def execute_if_due(self, task_fn: Callable) -> bool:
        if self.is_due():
            try:
                task_fn()
            finally:
                self.mark_executed()
            return True
        return False

class JobAutomationScheduler:
    def __init__(
        self,
        tracker,
        mailer,
        notifier,
        scan_interval_seconds: int = 7200,
        hunt_interval_seconds: int = 3600,
        auto_hunt_enabled: bool = True,
        pending_actions_ref: Optional[Dict[str, Any]] = None,
        lead_cache: Optional[LeadCache] = None
    ):
        self.tracker = tracker
        self.mailer = mailer
        self.notifier = notifier
        self.scan_runner = PeriodicTaskRunner(interval_seconds=scan_interval_seconds)
        self.hunt_runner = PeriodicTaskRunner(interval_seconds=hunt_interval_seconds)
        self.hunt_interval_seconds = hunt_interval_seconds
        self.auto_hunt_enabled = auto_hunt_enabled
        self.pending_actions = pending_actions_ref if pending_actions_ref is not None else {}
        self.lead_cache = lead_cache or LeadCache()
        self.last_briefing_date: str = ""
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.total_leads_hunted_today: int = 0

    def execute_auto_scan(self) -> int:
        """Memindai inbox untuk perusahaan aktif secara otomatis dan kirim alert jika ada update."""
        rows = self.tracker.get_tracked_companies()
        companies = list({r.get("Company", "") for r in rows if r.get("Company") and r.get("Status") in ["Applied", "On Progress"]})
        if not companies:
            return 0

        updates = self.mailer.check_inbox_updates(companies)
        for item in updates:
            st = item["detected_status"]
            self.tracker.update_status(item["company"], st, note=f"Auto-scan Email: {item['subject']}")
            if st == JobStatus.ON_PROGRESS:
                self.notifier.notify_interview_detected(item["company"], item["subject"], item.get("snippet", ""))
            elif st == JobStatus.OFFERING:
                self.notifier.notify_offering_detected(item["company"], item["subject"], item.get("snippet", ""))
            elif st == JobStatus.REJECTED:
                self.notifier.notify_rejection_detected(item["company"], item["subject"])

        return len(updates)

    def execute_autonomous_hunt(self) -> int:
        """Menjelajahi web mencari loker secara otonom 24/7 dan kirim kartu prospek ke Telegram."""
        if not self.auto_hunt_enabled:
            return 0

        print(f"\n[Scheduler 24/7] Memulai penelusuran lowongan otonom...")
        try:
            scraper = HRLeadsScraper(headless=True)
            leads = scraper.search_balanced_leads(custom_position=None, total_limit=4)
        except Exception as e:
            print(f"[Scheduler 24/7] Gagal menjalankan scraper: {e}")
            return 0

        qualified_leads = []
        for lead in leads:
            email = lead.get("email", "")
            source_url = lead.get("source_url", "")
            company = lead.get("company", "")

            # 1. Cek cache loker sudah pernah dinotifikasi
            if self.lead_cache.is_lead_seen(email=email, url=source_url):
                continue

            # 2. Cek apakah sudah pernah dilamar di sheets
            if self.tracker.is_already_applied(company):
                continue

            # 3. Kualifikasi AI & skor >= 50%
            if lead.get("match_score", 0) >= 50 and lead.get("decision") == "APPLY":
                qualified_leads.append(lead)

        if not qualified_leads:
            print("[Scheduler 24/7] Penelusuran selesai. Tidak ada prospek baru yang belum dilihat.")
            return 0

        print(f"[Scheduler 24/7] Ditemukan {len(qualified_leads)} lowongan baru! Mengirim ke Telegram...")
        for item in qualified_leads:
            lead_id = f"lead_{uuid.uuid4().hex[:8]}"
            self.pending_actions[lead_id] = item
            self.lead_cache.mark_lead_seen(
                email=item.get("email", ""),
                url=item.get("source_url", ""),
                company=item.get("company", ""),
                position=item.get("position", "")
            )
            self.total_leads_hunted_today += 1

            score = item.get("match_score", 0)
            zone = item.get("zone", "Indonesia")
            zone_label = "🇮🇩 Indonesia" if zone == "Indonesia" else "🌍 Global Remote"

            link_url = item.get("source_url") or item.get("source") or ""
            is_http = str(link_url).startswith("http")
            link_html = f"<a href='{link_url}'>Klik Buka Lowongan</a>" if is_http else "Hasil Scraping Mesin Pencari"

            matched_skills = item.get("matched_skills", [])
            matched_str = ", ".join(matched_skills) if matched_skills else "Sesuai Kualifikasi IT"

            snippet_text = item.get("snippet", "Deskripsi persyaratan tidak tersedia").strip()
            if len(snippet_text) > 300:
                snippet_text = snippet_text[:300] + "..."

            buttons = [
                [{"text": "🚀 Kirim Lamaran", "callback_data": f"apply_lead:{lead_id}"}],
                [{"text": "💾 Simpan Sheets", "callback_data": f"save_lead:{lead_id}"}],
                [{"text": "⏭️ Lewati", "callback_data": f"skip_lead:{lead_id}"}]
            ]
            if is_http:
                buttons.insert(0, [{"text": "🔗 Kunjungi Link Lowongan", "url": link_url}])

            post_time = item.get("post_date_display") or "Aktif / Baru (&lt;= 60 hari)"

            lead_card = (
                f"🔔 <b>[AUTO-HUNT 24/7] LOWONGAN BARU DITEMUKAN</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏢 <b>Perusahaan:</b> {item['company']}\n"
                f"📌 <b>Posisi:</b> {item['position']}\n"
                f"🌏 <b>Wilayah:</b> {zone_label}\n"
                f"📧 <b>Email HRD:</b> <code>{item['email']}</code>\n"
                f"🕒 <b>Waktu Postingan:</b> <i>{post_time}</i>\n"
                f"🔗 <b>Link Sumber:</b> {link_html}\n"
                f"🎯 <b>Skor Cocok:</b> {score}%\n"
                f"✅ <b>Skill Terdeteksi:</b> {matched_str}\n"
                f"💡 <b>Analisis AI:</b> {item.get('match_reason', '')}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 <b>Deskripsi / Syarat Loker:</b>\n"
                f"<i>\"{snippet_text}\"</i>\n\n"
                f"Pilih tindakan untuk prospek ini:"
            )
            self.notifier.send_inline_keyboard(lead_card, buttons)

        return len(qualified_leads)

    def execute_daily_briefing(self):
        """Mengirim ringkasan pagi ke Telegram seputar lamaran aktif & follow-up."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        if self.last_briefing_date == today_str:
            return

        now = datetime.now()
        # Jalankan briefing di pagi hari (jam 08:00 - 11:00)
        if 8 <= now.hour <= 11:
            rows = self.tracker.get_tracked_companies()
            stale = find_stale_applications(rows, days_threshold=5)
            active_count = sum(1 for r in rows if r.get("Status") in ["Applied", "On Progress"])

            msg = (
                f"🌅 <b>RINGKASAN PAGI JOB AUTOMATION</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 {today_str}\n"
                f"💼 Lamaran Aktif: <b>{active_count}</b>\n"
            )
            if stale:
                msg += f"⏰ <b>{len(stale)} lamaran</b> lewat 5 hari kerja tanpa kabar dan siap difollow-up.\n"
            else:
                msg += "✅ Semua proses lamaran berjalan lancar.\n"
            msg += "\n<i>Ketik /status atau /recent untuk pantau progres.</i>"

            self.notifier.send_message(msg)
            self.last_briefing_date = today_str

    def set_auto_hunt(self, enabled: bool):
        self.auto_hunt_enabled = enabled

    def set_hunt_interval(self, minutes: int):
        self.hunt_interval_seconds = max(15, minutes) * 60
        self.hunt_runner.interval_seconds = self.hunt_interval_seconds

    def get_auto_hunt_status(self) -> Dict[str, Any]:
        elapsed = (time.time() - self.hunt_runner.last_run_timestamp) if self.hunt_runner.last_run_timestamp else 0
        rem_sec = max(0, int(self.hunt_runner.interval_seconds - elapsed)) if self.hunt_runner.last_run_timestamp else 0
        return {
            "enabled": self.auto_hunt_enabled,
            "interval_minutes": self.hunt_interval_seconds // 60,
            "next_run_minutes": rem_sec // 60,
            "total_seen": self.lead_cache.total_seen_count(),
            "hunted_today": self.total_leads_hunted_today
        }

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                self.scan_runner.execute_if_due(self.execute_auto_scan)
                if self.auto_hunt_enabled:
                    self.hunt_runner.execute_if_due(self.execute_autonomous_hunt)
                self.execute_daily_briefing()
            except Exception as e:
                print(f"[Scheduler Warning] Error di siklus scheduler: {e}")
            time.sleep(30)

    def start_background(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="JobAutoSchedulerThread")
        self._thread.start()
        print("[Scheduler] Autonomous background scheduler 24/7 aktif (auto-hunt loker, inbox scan & briefing).")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
