import os
import sys
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
load_dotenv()

from src.notifier.telegram import TelegramNotifier
from src.sheets import get_tracker
from src.analytics import compute_application_metrics
from src.follow_up import find_stale_applications
from src.mailer import EmailHandler
from src.models import ApplicationRecord, JobStatus
from src.scheduler import JobAutomationScheduler
from src.interview.prep_kit import InterviewPrepKit
from src.cv_selector import CVManager, detect_language
from src.ai_assistant import AIAssistant
from src.templates.email_styler import render_html_cover_letter
from src.tailor.cover_letter_pdf import build_cover_letter_pdf
from src.tailor.resume_tailor import ResumeTailor
from src.security.rate_limiter import SmartRateLimiter
from src.scraper.hr_leads_scraper import HRLeadsScraper
from src.security.scam_detector import ScamDetector
from src.portals.linkedin import LinkedInBot
from src.portals.glints import GlintsBot
from src.portals.jobstreet import JobstreetBot
from src.backup import create_backup

class TelegramBotListener:
    def __init__(self, bot_token: Optional[str] = None, allowed_chat_id: Optional[str] = None):
        self.bot_token = bot_token if bot_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.allowed_chat_id = str(allowed_chat_id if allowed_chat_id is not None else os.getenv("TELEGRAM_CHAT_ID", "")).strip()
        self.notifier = TelegramNotifier(self.bot_token, self.allowed_chat_id)
        self.tracker = get_tracker()
        self.mailer = EmailHandler(
            os.getenv("EMAIL_USER", ""),
            os.getenv("EMAIL_PASSWORD", ""),
            os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            os.getenv("IMAP_SERVER", "imap.gmail.com")
        )
        self.cv_mgr = CVManager()
        self.ai = AIAssistant()
        self.rate_limiter = SmartRateLimiter()
        self.scam_detector = ScamDetector()
        self.pending_actions: Dict[str, Any] = {}
        self.last_update_id = 0
        self.scheduler = JobAutomationScheduler(
            tracker=self.tracker,
            mailer=self.mailer,
            notifier=self.notifier,
            scan_interval_seconds=int(os.getenv("AUTO_SCAN_INTERVAL_SECONDS", 7200)),
            hunt_interval_seconds=int(os.getenv("AUTO_HUNT_INTERVAL_SECONDS", 3600)),
            auto_hunt_enabled=True,
            pending_actions_ref=self.pending_actions
        )

    def handle_command(self, chat_id: str, text: str) -> bool:
        if str(chat_id).strip() != self.allowed_chat_id:
            print(f"[Security] Mengabaikan pesan dari chat_id tidak dikenal: {chat_id}")
            return False

        clean_text = text.strip()
        cmd = clean_text.lower()

        if cmd in ["/start", "/help", "help", "halo", "hi", "hai"]:
            help_msg = (
                "🤖 <b>JOB AUTOMATION MOBILE DASHBOARD</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Kontrol seluruh sistem langsung dari Telegram HP:\n\n"
                "📊 <b>/status</b> - Ringkasan analytics & konversi\n"
                "📋 <b>/recent</b> - 5 lamaran kerja terbaru\n"
                "🔍 <b>/scan</b> - Pindai inbox email balasan HRD\n"
                "⏰ <b>/followup</b> - Cek lamaran lewat 5 hari\n"
                "🎯 <b>/prep &lt;perusahaan&gt;</b> - Buat panduan interview\n"
                "🤖 <b>/autohunt [on/off/status/now]</b> - Mode autopilot 24/7 cari loker otomatis\n"
                "🌐 <b>/hunt [posisi opsional]</b> - Cari loker manual sekarang (35 peran IT)\n"
                "💼 <b>/portal</b> - Auto-apply LinkedIn, Glints, Jobstreet dari HP\n"
                "✉️ <b>/apply &lt;email&gt; | &lt;pt&gt; | &lt;posisi&gt;</b> - Kirim lamaran via tombol interaktif\n"
                "💾 <b>/backup</b> - Download file arsip database lamaran ke HP\n\n"
                "⚙️ <i>Filter Aktif: Skor AI &gt;= 50%, Usia Loker &lt;= 60 hari real-time, Pulau Jawa (Bebas), Luar Jawa &amp; Global (Hanya Remote/WFH), Anti-Scam.</i>"
            )
            self.notifier.send_message(help_msg)
            return True

        elif cmd == "/status":
            rows = self.tracker.get_tracked_companies()
            if not rows:
                self.notifier.send_message("ℹ️ Belum ada data pelamaran di database.")
                return True

            metrics = compute_application_metrics(rows)
            c = metrics["counts"]
            msg = (
                "📊 <b>RINGKASAN STATUS PELAMARAN</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"📤 Total Lamaran: <b>{metrics['total']}</b>\n"
                f"⏳ Sedang Diproses: <b>{c['Applied']}</b>\n"
                f"🎯 Wawancara / Tes: <b>{c['On Progress']}</b>\n"
                f"❌ Ditolak: <b>{c['Rejected']}</b>\n"
                f"🏆 Offering Letter: <b>{c['Offering']}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"📈 <b>Apply-to-Interview Rate:</b> {metrics['interview_rate']}%\n"
                f"📬 <b>HR Response Rate:</b> {metrics['response_rate']}%\n"
                f"🌟 <b>Offer Rate:</b> {metrics['offer_rate']}%"
            )
            self.notifier.send_message(msg)
            return True

        elif cmd == "/recent":
            rows = self.tracker.get_tracked_companies()
            if not rows:
                self.notifier.send_message("ℹ️ Belum ada data pelamaran.")
                return True

            recent = rows[-5:]
            msg = "📋 <b>5 PELAMARAN TERBARU:</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            for idx, r in enumerate(reversed(recent), 1):
                comp = r.get("Company", "-")
                pos = r.get("Position", "-")
                st = r.get("Status", "Applied")
                ch = r.get("Channel", "-")
                date = r.get("Date Applied", "")[:10]
                msg += f"<b>{idx}. {comp}</b> ({ch})\n💼 {pos}\n📌 Status: <code>{st}</code> | 📅 {date}\n\n"
            self.notifier.send_message(msg)
            return True

        elif cmd == "/scan":
            self.notifier.send_message("🔄 <b>Sedang memindai inbox email...</b>")
            rows = self.tracker.get_tracked_companies()
            companies = list({r.get("Company", "") for r in rows if r.get("Company") and r.get("Status") in ["Applied", "On Progress"]})
            if not companies:
                self.notifier.send_message("ℹ️ Tidak ada perusahaan aktif berstatus Applied/On Progress.")
                return True

            try:
                updates = self.mailer.check_inbox_updates(companies)
                if not updates:
                    self.notifier.send_message("✅ Pemindaian selesai. Belum ada email respon baru dari rekruter.")
                    return True

                for item in updates:
                    st = item["detected_status"]
                    comp = item["company"]
                    self.tracker.update_status(comp, st, note=f"Email: {item['subject']}")
                    if st == JobStatus.ON_PROGRESS:
                        btn = [[{"text": f"🎯 Buat Prep Kit: {comp}", "callback_data": f"prep:{comp}"}]]
                        self.notifier.send_inline_keyboard(
                            f"🎉 <b>UNDANGAN INTERVIEW: {comp}</b>\n\nSubject: {item['subject']}\nCuplikan: {item.get('snippet', '')[:150]}...\n\nKlik tombol di bawah untuk membuat Interview Prep Kit otomatis:",
                            btn
                        )
                    elif st == JobStatus.OFFERING:
                        self.notifier.notify_offering_detected(comp, item["subject"], item.get("snippet", ""))
                    elif st == JobStatus.REJECTED:
                        self.notifier.notify_rejection_detected(comp, item["subject"])
            except Exception as e:
                self.notifier.send_message(f"⚠️ Gagal memindai email: {e}")
            return True

        elif cmd == "/followup":
            rows = self.tracker.get_tracked_companies()
            stale = find_stale_applications(rows, days_threshold=5)
            if not stale:
                self.notifier.send_message("✅ Tidak ada lamaran yang menggantung lebih dari 5 hari.")
                return True

            msg = f"⏰ <b>DITEMUKAN {len(stale)} LAMARAN PERLU FOLLOW-UP:</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            for idx, r in enumerate(stale, 1):
                msg += f"<b>{idx}. {r.get('Company')}</b>\n💼 {r.get('Position')}\n📧 {r.get('Contact')}\n⏳ Lewat {r.get('days_elapsed')} hari\n\n"
            self.notifier.send_message(msg)
            return True

        elif cmd.startswith("/prep"):
            parts = clean_text.split(maxsplit=1)
            target_company = parts[1].strip() if len(parts) > 1 else ""
            if not target_company:
                self.notifier.send_message("ℹ️ Silakan tentukan nama perusahaan. Contoh: <code>/prep Shopee</code>")
                return True

            self.notifier.send_message(f"🧠 <b>Sedang menyusun Interview Preparation Kit untuk {target_company}...</b>")
            try:
                prep = InterviewPrepKit()
                guide_path = prep.generate_prep_kit(target_company, "Software Engineer")
                msg = (
                    f"✅ <b>INTERVIEW PREP KIT SIAP!</b>\n"
                    f"🏢 <b>Perusahaan:</b> {target_company}\n"
                    f"📁 <b>File:</b> <code>{guide_path}</code>\n\n"
                    f"Panduan 8 pertanyaan teknis/STAR, strategi jawaban berbasis ClipMax & Diskominfo berhasil dibuat."
                )
                self.notifier.send_message(msg)
            except Exception as e:
                self.notifier.send_message(f"⚠️ Gagal membuat prep kit: {e}")
            return True

        elif cmd.startswith("/autohunt"):
            parts = clean_text.split()
            sub = parts[1].lower() if len(parts) > 1 else "status"

            if sub == "on":
                self.scheduler.set_auto_hunt(True)
                self.notifier.send_message("🟢 <b>AUTO-HUNT 24/7 DIAKTIFKAN!</b>\nBot akan otomatis menjelajahi web mencari lowongan baru secara berkala dan mengirimkan kartu notifikasi langsung ke chat ini.")
            elif sub == "off":
                self.scheduler.set_auto_hunt(False)
                self.notifier.send_message("🔴 <b>AUTO-HUNT 24/7 DINONAKTIFKAN.</b>\nScraping otomatis dijeda. Anda tetap bisa menggunakan perintah manual /hunt kapan saja.")
            elif sub == "now":
                self.notifier.send_message("⚡ <b>Memulai siklus auto-hunt sekarang di background...</b>")
                import threading
                threading.Thread(target=self.scheduler.execute_autonomous_hunt, daemon=True).start()
            elif sub == "interval" and len(parts) > 2 and parts[2].isdigit():
                minutes = int(parts[2])
                self.scheduler.set_hunt_interval(minutes)
                self.notifier.send_message(f"⏱️ <b>Interval Auto-Hunt diubah menjadi:</b> Setiap {minutes} menit.")
            else:
                st = self.scheduler.get_auto_hunt_status()
                status_icon = "🟢 AKTIF (24/7)" if st["enabled"] else "🔴 NONAKTIF"
                msg = (
                    "🤖 <b>STATUS AUTONOMOUS 24/7 JOB HUNTER</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Status: <b>{status_icon}</b>\n"
                    f"⏱️ Interval Scraping: <b>Setiap {st['interval_minutes']} menit</b>\n"
                    f"⏳ Penelusuran Berikutnya: <b>dalam ~{st['next_run_minutes']} menit</b>\n"
                    f"🎯 Prospek Terjaring Hari Ini: <b>{st['hunted_today']} lowongan</b>\n"
                    f"💾 Database Cache Loker: <b>{st['total_seen']} postingan</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "Perintah Kontrol:\n"
                    "• <code>/autohunt on</code> - Mengaktifkan 24/7\n"
                    "• <code>/autohunt off</code> - Menjeda penelusuran\n"
                    "• <code>/autohunt now</code> - Picu penelusuran detik ini\n"
                    "• <code>/autohunt interval 60</code> - Ubah interval menit"
                )
                self.notifier.send_message(msg)
            return True

        elif cmd.startswith("/hunt"):
            parts = clean_text.split(maxsplit=1)
            keyword = parts[1].strip() if len(parts) > 1 else None
            scope_desc = keyword if keyword else "35 Posisi Target IT (Junior/Entry Level/Fresh Grad)"
            self.notifier.send_message(
                f"🌐 <b>Menjelajahi web mencari loker HRD...</b>\n"
                f"🎯 Cakupan: <i>{scope_desc}</i>\n"
                f"⚖️ Alokasi: <b>50% Indonesia 🇮🇩 + 50% Global Remote 🌍</b>\n"
                f"📍 Aturan Lokasi: <b>Pulau Jawa (Bebas), Luar Jawa/Luar Negeri (Hanya Remote/WFH)</b>\n"
                f"🕒 Filter Waktu: <b>Real-time maks. 1-2 bulan (&lt;= 60 hari)</b>\n"
                f"🤖 Ambang AI: <b>Skor &gt;= 50%</b>\n\n"
                f"<i>Sedang memproses...</i>"
            )
            try:
                scraper = HRLeadsScraper(headless=True)
                leads = scraper.search_balanced_leads(custom_position=keyword, total_limit=4)
                qualified_leads = [
                    item for item in leads
                    if item.get("match_score", 0) >= 50 and item.get("decision") == "APPLY"
                ]

                if not qualified_leads:
                    self.notifier.send_message("ℹ️ Penelusuran selesai. Tidak ada lowongan baru yang mencapai ambang batas kualifikasi (Skor >= 50%) atau loker telah lewat dari batas 1-2 bulan.")
                    return True

                for item in qualified_leads:
                    lead_id = f"lead_{uuid.uuid4().hex[:8]}"
                    self.pending_actions[lead_id] = item
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
                        f"💼 <b>PROSPEK LOKER DITEMUKAN</b>\n"
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
            except Exception as e:
                self.notifier.send_message(f"⚠️ Gagal scraping loker: {e}")
            return True

        elif cmd.startswith("/portal"):
            parts = clean_text.split()
            if len(parts) == 1:
                buttons = [
                    [{"text": "🚀 SEMUA PORTAL (LinkedIn + Glints + Jobstreet - 35 Posisi IT)", "callback_data": "run_portal:all_portals:all:6"}],
                    [{"text": "🔗 LinkedIn (Semua 35 Posisi IT - 50% ID + 50% Remote)", "callback_data": "run_portal:linkedin:all:4"}],
                    [{"text": "⚡ Glints (Semua 35 Posisi IT)", "callback_data": "run_portal:glints:all:4"}],
                    [{"text": "💼 Jobstreet (Semua 35 Posisi IT)", "callback_data": "run_portal:jobstreet:all:4"}]
                ]
                self.notifier.send_inline_keyboard(
                    "🌐 <b>PILIH TARGET AUTO-APPLY JOB PORTAL:</b>\n"
                    "Bot akan mencari dan melamar lowongan di portal kerja mencakup <b>seluruh 35 posisi IT</b> yang telah Anda tentukan (Skor AI >= 50%).\n\n"
                    "Pilih portal di bawah (mencakup semua posisi IT):\n"
                    "• <code>/portal all 6</code> (Semua portal sekaligus)\n"
                    "• <code>/portal linkedin all 4</code> (LinkedIn semua posisi)\n"
                    "• <code>/portal glints all 4</code> (Glints semua posisi)\n"
                    "• <code>/portal jobstreet all 4</code> (Jobstreet semua posisi)\n"
                    "<i>Atau sebut posisi spesifik jika ingin: <code>/portal linkedin Flutter Developer 3</code></i>",
                    buttons
                )
                return True

            portal_target = parts[1].lower()
            keyword = "all"
            limit = 4
            if len(parts) > 2:
                if parts[-1].isdigit():
                    limit = int(parts[-1])
                    keyword = " ".join(parts[2:-1]) if len(parts) > 3 else "all"
                else:
                    keyword = " ".join(parts[2:])

            self._execute_portal_apply(portal_target, keyword, limit)
            return True

        elif cmd == "/backup":
            self.notifier.send_message("📦 <b>Mengekspor arsip database pelamaran kerja...</b>")
            try:
                backup_path = create_backup(self.tracker)
                caption = f"📦 <b>Arsip Database Pelamaran</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nFile CSV siap diimpor ke Excel / Google Sheets."
                sent = self.notifier.send_document(backup_path, caption=caption)
                if not sent:
                    self.notifier.send_message(f"⚠️ Berhasil membuat file di <code>{backup_path}</code> namun gagal mengirim file ke chat Telegram.")
            except Exception as e:
                self.notifier.send_message(f"⚠️ Gagal membuat backup: {e}")
            return True

        elif cmd.startswith("/apply"):
            raw_args = clean_text[6:].strip()
            parts = [p.strip() for p in raw_args.split("|")]
            if len(parts) < 3:
                self.notifier.send_message(
                    "ℹ️ Format perintah:\n"
                    "<code>/apply hrd@company.com | Nama Perusahaan | Posisi | (Opsional deskripsi)</code>\n\n"
                    "Contoh:\n"
                    "<code>/apply hr@tech.co.id | PT Tech Indo | Backend Developer</code>"
                )
                return True

            to_email, company, position = parts[0], parts[1], parts[2]
            job_desc = parts[3] if len(parts) > 3 else ""

            # 1. Pengecekan Scam
            is_scam, scam_reason = self.scam_detector.is_suspicious_lead(company, position, to_email, job_desc)
            if is_scam:
                self.notifier.send_message(f"⚠️ <b>PERINGATAN SCAM!</b>\n{scam_reason}\nPengiriman otomatis dibatalkan demi keamanan.")
                return True

            # 2. Pengecekan Duplikat
            if self.tracker.is_already_applied(company, contact_or_email=to_email):
                self.notifier.send_message(f"⚠️ <b>DUPLIKAT:</b> Perusahaan '{company}' atau email '{to_email}' sudah ada di database pelamaran Anda.")
                return True

            self.notifier.send_message(f"✍️ <b>Menyusun Cover Letter via AI untuk {company}...</b>")

            lang = detect_language(f"{position} {company} {job_desc}", default_lang="id", email_or_domain=to_email)
            cv_path = self.cv_mgr.get_cv(lang=lang)

            try:
                cover_letter = self.ai.generate_cover_letter(company, position, job_desc, lang=lang)
            except Exception:
                cover_letter = "Saya mengajukan lamaran untuk posisi ini. Terlampir CV saya."

            app_id = f"app_{uuid.uuid4().hex[:8]}"
            self.pending_actions[app_id] = {
                "to_email": to_email,
                "company": company,
                "position": position,
                "body": cover_letter,
                "cv_path": cv_path,
                "lang": lang,
                "job_desc": job_desc
            }

            buttons = [
                [{"text": "🚀 Kirim Sekarang", "callback_data": f"send:{app_id}"}],
                [{"text": "📄 Tailor CV ATS & Kirim", "callback_data": f"tailor_send:{app_id}"}],
                [{"text": "❌ Batal", "callback_data": f"cancel:{app_id}"}]
            ]

            preview_msg = (
                f"📝 <b>DRAFT LAMARAN SIAP: {company}</b>\n"
                f"💼 Posisi: {position}\n"
                f"📧 Tujuan: {to_email}\n"
                f"📄 CV: {os.path.basename(cv_path)} ({lang.upper()})\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Preview Surat:</b>\n"
                f"<i>{cover_letter[:350]}...</i>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"Pilih aksi pengiriman:"
            )
            self.notifier.send_inline_keyboard(preview_msg, buttons)
            return True

        else:
            self.notifier.send_message("❓ Perintah tidak dikenali. Ketik <b>/help</b> untuk melihat menu perintah.")
            return True

    def handle_callback_query(self, query_id: str, chat_id: str, data: str, message_id: Optional[int] = None) -> bool:
        if str(chat_id).strip() != self.allowed_chat_id:
            return False

        if data.startswith("send:") or data.startswith("tailor_send:"):
            is_tailor = data.startswith("tailor_send:")
            app_id = data.split(":", 1)[1]
            app_data = self.pending_actions.pop(app_id, None)

            if not app_data:
                self.notifier.answer_callback_query(query_id, "Lamaran sudah diproses atau kedaluwarsa.")
                return True

            self.notifier.answer_callback_query(query_id, "Memproses pengiriman...")
            if message_id:
                self.notifier.edit_message_text(
                    chat_id,
                    message_id,
                    f"⏳ <b>SEDANG MENGIRIM LAMARAN...</b>\n🏢 Perusahaan: <b>{app_data['company']}</b>\n💼 Posisi: <b>{app_data['position']}</b>\n📧 Email: <code>{app_data['to_email']}</code>",
                    buttons=[]
                )
            else:
                self.notifier.send_message(f"⏳ <b>Mengirim email lamaran ke {app_data['company']}...</b>")

            cv_path = app_data["cv_path"]
            if is_tailor and app_data.get("job_desc"):
                try:
                    tailor = ResumeTailor()
                    cv_path = tailor.build_tailored_resume(app_data["company"], app_data["position"], app_data["job_desc"], lang=app_data.get("lang", "id"))
                except Exception:
                    pass

            # Generate Cover Letter PDF
            cover_pdf = None
            try:
                cover_pdf = build_cover_letter_pdf(app_data["company"], app_data["position"], app_data["body"], lang=app_data.get("lang", "id"))
            except Exception:
                pass

            # Render HTML body
            html_body = render_html_cover_letter(app_data["body"], position=app_data["position"], company=app_data["company"], lang=app_data.get("lang", "id"))
            subject = f"Application for {app_data['position']} - Muhammad Bagja Satrio" if app_data.get("lang") == "en" else f"Lamaran Pekerjaan - {app_data['position']} - Muhammad Bagja Satrio"

            try:
                self.mailer.send_application(
                    to_email=app_data["to_email"],
                    subject=subject,
                    body_text=app_data["body"],
                    cv_path=cv_path,
                    extra_attachment_path=cover_pdf,
                    html_body=html_body
                )
                self.rate_limiter.record_sent()

                rec = ApplicationRecord(
                    company=app_data["company"],
                    position=app_data["position"],
                    channel="Email (Telegram)",
                    status=JobStatus.APPLIED,
                    contact=app_data["to_email"],
                    notes=f"Sent via Telegram Bot | CV: {os.path.basename(cv_path)}"
                )
                self.tracker.append_record(rec)
                final_msg = f"✅ <b>BERHASIL TERKIRIM!</b>\nLamaran ke <b>{app_data['company']}</b> telah terkirim dan dicatat di Google Sheets."
                if message_id:
                    self.notifier.edit_message_text(chat_id, message_id, final_msg, buttons=[])
                else:
                    self.notifier.send_message(final_msg)
            except Exception as e:
                self.notifier.send_message(f"❌ Gagal mengirim email: {e}")
            return True

        elif data.startswith("cancel:"):
            app_id = data.split(":", 1)[1]
            self.pending_actions.pop(app_id, None)
            self.notifier.answer_callback_query(query_id, "Dibatalkan.")
            if message_id:
                self.notifier.edit_message_text(chat_id, message_id, "❌ <i>Draf lamaran ini telah dibatalkan.</i>", buttons=[])
            else:
                self.notifier.send_message("❌ Lamaran dibatalkan.")
            return True

        elif data.startswith("prep:"):
            comp = data.split(":", 1)[1]
            self.notifier.answer_callback_query(query_id, f"Menyiapkan prep kit {comp}...")
            prep = InterviewPrepKit()
            path = prep.generate_prep_kit(comp, "Software Engineer")
            self.notifier.send_message(f"🎯 <b>Interview Prep Kit Siap:</b>\n<code>{path}</code>")
            return True

        elif data.startswith("apply_lead:"):
            lead_id = data.split(":", 1)[1]
            lead = self.pending_actions.pop(lead_id, None)
            if not lead:
                self.notifier.answer_callback_query(query_id, "Lead kedaluwarsa.")
                return True

            self.notifier.answer_callback_query(query_id, "Mengirim lamaran...")
            if message_id:
                self.notifier.edit_message_text(
                    chat_id,
                    message_id,
                    f"⏳ <b>SEDANG MEMPROSES LAMARAN...</b>\n🏢 Perusahaan: <b>{lead['company']}</b>\n💼 Posisi: <b>{lead['position']}</b>\n📧 Email: <code>{lead['email']}</code>",
                    buttons=[]
                )

            zone = lead.get("zone", "Indonesia")
            if zone == "Global Remote":
                lang = "en"
            else:
                # Periksa teks lengkap loker (posisi + perusahaan + snippet) & domain email
                full_job_context = f"{lead['position']} {lead['company']} {lead.get('snippet', '')}"
                lang = detect_language(
                    full_job_context,
                    default_lang="id",
                    email_or_domain=lead.get("email", "")
                )

            # 1. Generate Cover Letter AI
            cover = self.ai.generate_cover_letter(lead["company"], lead["position"], lead.get("snippet", ""), lang=lang)

            # 2. Generate CV Tailored PDF (Exact ATS keywords & Ringkasan Profil Khusus)
            try:
                tailor = ResumeTailor()
                cv_path = tailor.build_tailored_resume(lead["company"], lead["position"], lead.get("snippet", ""), lang=lang)
            except Exception:
                cv_path = self.cv_mgr.get_cv(lang=lang)

            # 3. Generate Surat Lamaran PDF Dokumen Resmi
            cover_pdf = None
            try:
                cover_pdf = build_cover_letter_pdf(lead["company"], lead["position"], cover, lang=lang)
            except Exception:
                pass

            # Format subject dan posisi yang rapi (hindari lowercase 'it')
            clean_pos = lead["position"]
            if clean_pos.lower() == "it":
                clean_pos = "IT Specialist"
            elif clean_pos.lower().startswith("it "):
                clean_pos = "IT " + clean_pos[3:]
            elif clean_pos.lower().endswith(" it"):
                clean_pos = clean_pos[:-3] + " IT"

            html_body = render_html_cover_letter(cover, position=clean_pos, company=lead["company"], lang=lang)
            subject = f"Application for {clean_pos} - Muhammad Bagja Satrio" if lang == "en" else f"Lamaran Pekerjaan - {clean_pos} - Muhammad Bagja Satrio"

            try:
                self.mailer.send_application(
                    to_email=lead["email"],
                    subject=subject,
                    body_text=cover,
                    cv_path=cv_path,
                    extra_attachment_path=cover_pdf,
                    html_body=html_body
                )
                self.rate_limiter.record_sent()
                rec = ApplicationRecord(
                    company=lead["company"],
                    position=lead["position"],
                    channel=f"Web Scraping ({zone})",
                    status=JobStatus.APPLIED,
                    contact=lead["email"],
                    notes=f"Skor AI: {lead.get('match_score')}% | CV Tailored ATS"
                )
                self.tracker.append_record(rec)
                success_text = f"✅ <b>LAMARAN TERKIRIM</b>\n🏢 Perusahaan: <b>{lead['company']}</b>\n💼 Posisi: <b>{lead['position']}</b>\n📧 Email: <code>{lead['email']}</code>\nStatus: <i>Terkirim via email & tercatat di Google Sheets.</i>"
                if message_id:
                    self.notifier.edit_message_text(chat_id, message_id, success_text, buttons=[])
                else:
                    self.notifier.send_message(success_text)
            except Exception as e:
                self.notifier.send_message(f"❌ Gagal mengirim: {e}")
            return True

        elif data.startswith("save_lead:"):
            lead_id = data.split(":", 1)[1]
            lead = self.pending_actions.pop(lead_id, None)
            if lead:
                self.notifier.answer_callback_query(query_id, "Tersimpan ke Sheets.")
                rec = ApplicationRecord(
                    company=lead["company"],
                    position=lead["position"],
                    channel="Web Scraping",
                    status=JobStatus.APPLIED,
                    contact=lead["email"],
                    notes=f"Lead Baru (Skor AI: {lead.get('match_score')}%)"
                )
                self.tracker.append_record(rec)
                save_text = f"💾 <b>PROSPEK DISIMPAN</b>\n🏢 Perusahaan: <b>{lead['company']}</b>\n💼 Posisi: <b>{lead['position']}</b>\nStatus: <i>Tersimpan di Google Sheets sebagai prospek baru.</i>"
                if message_id:
                    self.notifier.edit_message_text(chat_id, message_id, save_text, buttons=[])
                else:
                    self.notifier.send_message(save_text)
            return True

        elif data.startswith("skip_lead:"):
            lead_id = data.split(":", 1)[1]
            lead = self.pending_actions.pop(lead_id, None)
            self.notifier.answer_callback_query(query_id, "Dilewati.")
            comp_name = lead.get('company', '') if lead else ""
            skip_text = f"⏭️ <i>Prospek {comp_name} telah dilewati.</i>"
            if message_id:
                self.notifier.edit_message_text(chat_id, message_id, skip_text, buttons=[])
            else:
                self.notifier.send_message(skip_text)
            return True

        elif data.startswith("run_portal:"):
            parts = data.split(":")
            p_name = parts[1]
            kw = parts[2] if len(parts) > 2 else "Software Engineer"
            lim = int(parts[3]) if len(parts) > 3 else 3
            self.notifier.answer_callback_query(query_id, f"Menjalankan bot {p_name}...")
            self._execute_portal_apply(p_name, kw, lim)
            return True

        return False

    def _execute_portal_apply(self, portal_name: str, keyword: str, limit: int):
        from src.target_roles import get_sample_keywords, JOB_CLUSTERS

        portal = portal_name.lower().strip()
        display_kw = keyword
        search_kw = keyword

        if keyword in JOB_CLUSTERS or keyword.lower() in ["all", "semua", "it", "any"]:
            search_kw = "all"
            display_kw = "Semua 35 Target Posisi IT"

        self.notifier.send_message(
            f"🚀 <b>MEMULAI AUTO-APPLY PORTAL: {portal.upper()}</b>\n"
            f"🎯 Target Posisi: <b>{display_kw}</b>\n"
            f"📊 Target Sesi: <b>{limit} lamaran</b> (Batas aman harian: 15)\n"
            f"🌐 Browser automation sedang berjalan..."
        )

        applied_records = []
        try:
            if portal in ["all_portals", "all", "semua"]:
                each_lim = max(1, limit // 3)
                try:
                    li_bot = LinkedInBot()
                    applied_records += li_bot.apply_balanced_jobs(keyword=search_kw, total_apply=each_lim, headless=True)
                except Exception as e:
                    print(f"[Portal All] LinkedIn error: {e}")
                try:
                    gl_bot = GlintsBot()
                    applied_records += gl_bot.apply_glints_jobs(keyword=search_kw, max_apply=each_lim, headless=True)
                except Exception as e:
                    print(f"[Portal All] Glints error: {e}")
                try:
                    js_bot = JobstreetBot()
                    applied_records += js_bot.apply_jobstreet_jobs(keyword=search_kw, max_apply=each_lim, headless=True)
                except Exception as e:
                    print(f"[Portal All] Jobstreet error: {e}")
            elif portal in ["linkedin", "li", "linkedin_balanced"]:
                bot = LinkedInBot()
                applied_records = bot.apply_balanced_jobs(keyword=search_kw, total_apply=limit, headless=True)
            elif portal in ["linkedin_id", "li_id"]:
                bot = LinkedInBot()
                applied_records = bot.apply_easy_jobs(keyword=search_kw, location="Indonesia", max_apply=limit, headless=True, remote_only=False)
            elif portal in ["linkedin_global", "li_global"]:
                bot = LinkedInBot()
                applied_records = bot.apply_easy_jobs(keyword=search_kw, location="Worldwide", max_apply=limit, headless=True, remote_only=True)
            elif portal in ["glints", "gl"]:
                bot = GlintsBot()
                applied_records = bot.apply_glints_jobs(keyword=search_kw, max_apply=limit, headless=True)
            elif portal in ["jobstreet", "js"]:
                bot = JobstreetBot()
                applied_records = bot.apply_jobstreet_jobs(keyword=search_kw, max_apply=limit, headless=True)
            else:
                self.notifier.send_message(f"❌ Portal '{portal_name}' tidak dikenal. Pilih: all, linkedin, glints, atau jobstreet.")
                return

            if applied_records:
                for rec in applied_records:
                    self.tracker.append_record(rec)
                    self.notifier.notify_application_sent(rec.company, rec.position, rec.channel, notes=rec.notes)

                self.notifier.send_message(
                    f"🎉 <b>SELESAI!</b>\n"
                    f"Berhasil melamar ke <b>{len(applied_records)} lowongan</b> di {portal.upper()} dan tercatat di Google Sheets."
                )
            else:
                self.notifier.send_message(f"ℹ️ Selesai. Tidak ada lowongan baru yang lolos batas AI (>= 50%) atau kuota harian telah tercapai.")
        except Exception as e:
            self.notifier.send_message(f"⚠️ Terjadi kesalahan pada bot portal: {e}")

    def poll_once(self):
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        params = {"timeout": 5}
        if self.last_update_id > 0:
            params["offset"] = self.last_update_id + 1

        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for update in data.get("result", []):
                    self.last_update_id = update["update_id"]

                    # 1. Pesan Teks
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    if text and chat_id:
                        self.handle_command(chat_id, text)

                    # 2. Tombol Klik Interaktif (Inline Keyboard Callback)
                    cb = update.get("callback_query")
                    if cb:
                        query_id = cb.get("id")
                        chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
                        message_id = cb.get("message", {}).get("message_id")
                        data = cb.get("data", "")
                        if query_id and data:
                            self.handle_callback_query(query_id, chat_id, data, message_id=message_id)
        except Exception:
            pass

    def run_polling_loop(self):
        print("=" * 60)
        print("  TELEGRAM BOT FULL INTERACTIVE DASHBOARD (HP REMOTE CONTROL)  ")
        print("=" * 60)
        print(f"Bot aktif mendengarkan perintah dari Telegram ID: {self.allowed_chat_id}")
        print("Ketik /help di Telegram HP Anda untuk melihat menu.")
        print("Tekan Ctrl + C di terminal untuk menghentikan listener.\n")

        self.scheduler.start_background()

        # Skip historical updates to only process new incoming commands
        init_res = requests.get(f"https://api.telegram.org/bot{self.bot_token}/getUpdates?offset=-1")
        if init_res.status_code == 200:
            res_json = init_res.json().get("result", [])
            if res_json:
                self.last_update_id = res_json[-1]["update_id"]

        while True:
            try:
                self.poll_once()
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nListener dihentikan.")
                self.scheduler.stop()
                break
            except Exception as e:
                time.sleep(2)

if __name__ == "__main__":
    listener = TelegramBotListener()
    listener.run_polling_loop()
