import sys
import os
from datetime import datetime

# Ensure project root is in sys.path when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from src.models import ApplicationRecord, JobStatus
from src.sheets import SheetsTracker, get_tracker
from src.mailer import EmailHandler
from src.cv_selector import CVManager, detect_language
from src.ai_assistant import AIAssistant
from src.portals.linkedin import LinkedInBot
from src.portals.glints import GlintsBot
from src.portals.jobstreet import JobstreetBot
from src.scraper.hr_leads_scraper import HRLeadsScraper
from src.matcher.ai_matcher import AIMatcher
from src.follow_up import find_stale_applications
from src.analytics import compute_application_metrics, format_analytics_dashboard
from src.tailor.resume_tailor import ResumeTailor
from src.tailor.cover_letter_pdf import build_cover_letter_pdf
from src.notifier.telegram import TelegramNotifier
from src.security.scam_detector import ScamDetector
from src.security.rate_limiter import SmartRateLimiter
from src.interview.prep_kit import InterviewPrepKit
from src.templates.email_styler import render_html_cover_letter

load_dotenv()

def get_sheets_tracker():
    return get_tracker()

def get_email_handler() -> EmailHandler:
    user = os.getenv("EMAIL_USER", "")
    password = os.getenv("EMAIL_PASSWORD", "")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
    return EmailHandler(user, password, smtp_server, imap_server)

def menu_send_email():
    print("\n--- KIRIM COLD EMAIL LAMARAN ---")
    tracker = get_sheets_tracker()
    if tracker:
        today_applied = tracker.get_today_apply_count()
        if today_applied >= 15:
            print("[Quota Guard] Batas aman harian (15 lamaran) sudah tercapai untuk hari ini. Disarankan istirahat.")
            return

    to_email = input("Email Tujuan HRD: ").strip()
    company = input("Nama Perusahaan: ").strip()
    position = input("Posisi yang dilamar: ").strip()

    if tracker and tracker.is_already_applied(company, contact_or_email=to_email):
        print(f"\n[Peringatan Anti-Duplicate] Perusahaan '{company}' atau email '{to_email}' sudah ada di database pelamaran!")
        cont = input("Tetap lanjutkan kirim email? (y/n) [Default: n]: ").strip().lower()
        if cont != "y":
            print("Pengiriman dibatalkan demi menghindari spam.")
            return

    # Pengecekan Keamanan / Loker Bodong
    scam_check = ScamDetector()
    is_scam, scam_reason = scam_check.is_suspicious_lead(company, position, to_email, "")
    if is_scam:
        print(f"\n⚠️  [PERINGATAN KEAMANAN / POTENSI SCAM]")
        print(f"Perusahaan/Email ini memiliki indikasi loker bodong: {scam_reason}")
        proceed = input("Apakah Anda yakin ingin tetap mengirim email ini? (y/n) [Default: n]: ").strip().lower()
        if proceed != "y":
            print("Pengiriman dibatalkan demi keamanan Anda.")
            return

    cv_mgr = CVManager()
    detected_lang = detect_language(f"{position} {company}")
    lang_choice = input(f"Bahasa email & CV (id/en) [Default terdeteksi: {detected_lang}]: ").strip().lower()
    if lang_choice not in ["id", "en"]:
        lang_choice = detected_lang

    cv_path = cv_mgr.get_cv(lang=lang_choice)
    print(f"Menggunakan CV: {os.path.basename(cv_path)} ({lang_choice.upper()})")

    if not os.path.exists(cv_path):
        print(f"[Error] File CV tidak ditemukan di {cv_path}")
        return

    job_desc = input("Paste ringkasan/syarat lowongan (Opsional, tekan ENTER jika tidak ada): ").strip()

    # Opsi Dynamic ATS Resume Tailoring
    if job_desc:
        tailor_opt = input("Generate CV PDF baru yang di-tailor khusus kata kunci lowongan ini? (y/n) [Default: y]: ").strip().lower() or "y"
        if tailor_opt == "y":
            print(f"[ATS Tailor] Membuat CV PDF terpersonalisasi untuk {company} ({position})...")
            try:
                tailor = ResumeTailor()
                tailored_cv = tailor.build_tailored_resume(company, position, job_desc, lang=lang_choice)
                cv_path = tailored_cv
                print(f"[ATS Tailor] CV Tailored siap: {os.path.basename(cv_path)}")
            except Exception as e:
                print(f"[Warning] Gagal tailor CV: {e}. Tetap menggunakan CV standar.")

    gemini_key = os.getenv("GEMINI_API_KEY")
    body = ""
    if gemini_key:
        print("[AI] Menghubungi Google Gemini untuk menyusun Cover Letter yang dipersonalisasi...")
        try:
            ai = AIAssistant()
            body = ai.generate_cover_letter(company, position, job_desc, lang=lang_choice)
        except Exception as e:
            print(f"[Warning] Gagal generate via AI: {e}. Menggunakan template bawaan.")

    if not body:
        if lang_choice == "en":
            body = f"""Dear Hiring Team at {company},

I am writing to express my interest in the {position} position at {company}.
With hands-on experience in full-stack web development, AI/LLM integration (OpenAI-compatible gateways, prompt engineering), and scalable software engineering, I am confident in contributing effectively to your team.

Please find attached my Curriculum Vitae (CV) for your review. I look forward to the possibility of discussing my background with you.

Sincerely,
Muhammad Bagja Satrio
"""
        else:
            body = f"""Kepada Yth. Tim HRD / Rekruter {company},

Perkenalkan saya Muhammad Bagja Satrio, mengajukan lamaran untuk posisi {position} di {company}.
Saya memiliki pengalaman dalam rekayasa perangkat lunak full-stack, integrasi kecerdasan buatan (AI/LLM multi-provider), dan arsitektur web/mobile modern.

Terlampir Curriculum Vitae (CV) saya sebagai bahan pertimbangan kualifikasi dan pengalaman saya. Besar harapan saya untuk dapat berdiskusi lebih lanjut.

Hormat saya,
Muhammad Bagja Satrio
"""

    if lang_choice == "en":
        default_subject = f"Application for {position} - Muhammad Bagja Satrio"
    else:
        default_subject = f"Lamaran Pekerjaan - {position} - Muhammad Bagja Satrio"

    subject = input(f"Subject Email [Default: {default_subject}]: ").strip() or default_subject

    print("\n" + "=" * 50)
    print("PREVIEW EMAIL COVER LETTER:")
    print("=" * 50)
    print(body)
    print("=" * 50)

    attach_pdf_letter = input("Lampirkan juga Surat Lamaran versi dokumen PDF resmi? (y/n) [Default: y]: ").strip().lower() or "y"
    cover_pdf_path = None
    if attach_pdf_letter == "y":
        print(f"[PDF Generator] Membuat dokumen Surat Lamaran PDF resmi...")
        try:
            cover_pdf_path = build_cover_letter_pdf(company, position, body, lang=lang_choice)
            print(f"[PDF Generator] Dokumen siap: {os.path.basename(cover_pdf_path)}")
        except Exception as e:
            print(f"[Warning] Gagal buat PDF cover letter: {e}")

    confirm_send = input("Kirim email sekarang? (y/n) [Default: y]: ").strip().lower()
    if confirm_send == "n":
        print("Pengiriman dibatalkan.")
        return

    # Smart Rate Limiter Cooldown
    limiter = SmartRateLimiter()
    allowed = limiter.wait_cooldown(interactive=True)
    if not allowed:
        return

    mailer = get_email_handler()
    print(f"Mengirim email ke {to_email}...")
    try:
        html_body = render_html_cover_letter(body, position=position, company=company, lang=lang_choice)
        mailer.send_application(
            to_email,
            subject,
            body,
            cv_path,
            extra_attachment_path=cover_pdf_path,
            html_body=html_body
        )
        limiter.record_sent()
        print("Email lamaran berhasil terkirim!")

        # Update Google Sheets
        tracker = get_sheets_tracker()
        if tracker:
            rec = ApplicationRecord(
                company=company,
                position=position,
                channel="Email",
                status=JobStatus.APPLIED,
                contact=to_email,
                notes=f"Subject: {subject}"
            )
            tracker.append_record(rec)
            print("Data lamaran tercatat di Google Sheets.")

        tg = TelegramNotifier()
        tg.notify_application_sent(company, position, "Email", notes=f"Subject: {subject}")
    except Exception as e:
        print(f"Gagal mengirim email: {e}")

def menu_portal_apply():
    print("\n--- AUTO-APPLY JOB PORTAL ---")
    print("1. LinkedIn (50% Indonesia + 50% Global Remote)")
    print("2. LinkedIn (Indonesia Saja)")
    print("3. LinkedIn (Global Remote Saja)")
    print("4. Glints (Indonesia)")
    print("5. Jobstreet (Indonesia)")
    choice = input("Pilih portal (1-5) [Default: 1]: ").strip() or "1"

    keyword = input("Kata kunci posisi (cth: Software Engineer): ").strip()
    if not keyword:
        print("Kata kunci wajib diisi.")
        return

    max_apply_str = input("Batas maksimal apply sesi ini [Default: 4]: ").strip()
    max_apply = int(max_apply_str) if max_apply_str.isdigit() else 4

    tracker = get_sheets_tracker()
    applied_records = []

    if choice == "1":
        bot = LinkedInBot()
        applied_records = bot.apply_balanced_jobs(keyword=keyword, total_apply=max_apply)
    elif choice == "2":
        bot = LinkedInBot()
        applied_records = bot.apply_easy_jobs(keyword=keyword, location="Indonesia", max_apply=max_apply, remote_only=False)
    elif choice == "3":
        bot = LinkedInBot()
        applied_records = bot.apply_easy_jobs(keyword=keyword, location="Worldwide", max_apply=max_apply, remote_only=True)
    elif choice == "4":
        bot = GlintsBot()
        applied_records = bot.apply_glints_jobs(keyword=keyword, max_apply=max_apply)
    elif choice == "5":
        bot = JobstreetBot()
        applied_records = bot.apply_jobstreet_jobs(keyword=keyword, max_apply=max_apply)
    else:
        print("Pilihan portal tidak valid.")
        return

    if tracker and applied_records:
        for rec in applied_records:
            tracker.append_record(rec)
        print(f"Berhasil mencatat {len(applied_records)} lowongan ke Google Sheets!")

def menu_scan_inbox():
    print("\n--- SCAN INBOX & UPDATE STATUS GOOGLE SHEETS ---")
    tracker = get_sheets_tracker()
    if not tracker:
        print("Google Sheets belum terkonfigurasi. Tidak dapat mencocokkan riwayat perusahaan.")
        return

    rows = tracker.get_tracked_companies()
    companies = list({r.get("Company", "") for r in rows if r.get("Company") and r.get("Status") in ["Applied", "On Progress"]})

    if not companies:
        print("Tidak ada perusahaan aktif berstatus 'Applied' atau 'On Progress' di Google Sheets.")
        return

    print(f"Memeriksa respon email masuk untuk {len(companies)} perusahaan...")
    mailer = get_email_handler()
    try:
        updates = mailer.check_inbox_updates(companies)
    except Exception as e:
        print(f"Gagal membaca email: {e}")
        return

    if not updates:
        print("Belum ada email respon baru dari perusahaan yang dilamar.")
        return

    print(f"\nDitemukan {len(updates)} email terkait!")
    for item in updates:
        print("\n" + "=" * 50)
        print(f"Perusahaan : {item['company']}")
        print(f"Pengirim   : {item['sender']}")
        print(f"Subject    : {item['subject']}")
        print(f"Deteksi    : {item['detected_status'].value} (Confidence: {item['confidence']*100:.0f}%)")
        print(f"Cuplikan   : {item.get('snippet', '')}")
        print("=" * 50)

        confirm = input(f"Update status '{item['company']}' menjadi '{item['detected_status'].value}' di Sheets? (y/n): ").strip().lower()
        if confirm == "y":
            tracker.update_status(item["company"], item["detected_status"], note=f"Email: {item['subject']}")
            print("Status berhasil diupdate di Google Sheets!")

            tg = TelegramNotifier()
            if item["detected_status"] == JobStatus.ON_PROGRESS:
                tg.notify_interview_detected(item["company"], item["subject"], item.get("snippet", ""))

                # Tawarkan pembuatan Interview Preparation Kit
                prep_prompt = input(f"\nBuatkan dokumen Interview Preparation Kit untuk {item['company']}? (y/n) [Default: y]: ").strip().lower() or "y"
                if prep_prompt == "y":
                    print("[AI] Menyusun lembar panduan persiapan interview...")
                    try:
                        prep = InterviewPrepKit()
                        guide_path = prep.generate_prep_kit(item["company"], item.get("position", "Software Engineer"), email_snippet=item.get("snippet", ""))
                        print(f"✅ Dokumen persiapan wawancara siap: {os.path.basename(guide_path)}")
                        print(f"Lokasi: {guide_path}")
                    except Exception as e:
                        print(f"[Warning] Gagal generate prep kit: {e}")

            elif item["detected_status"] == JobStatus.OFFERING:
                tg.notify_offering_detected(item["company"], item["subject"], item.get("snippet", ""))
            elif item["detected_status"] == JobStatus.REJECTED:
                tg.notify_rejection_detected(item["company"], item["subject"])

def menu_view_status():
    print("\n--- REKAP STATUS & ANALYTICS PELAMARAN ---")
    tracker = get_sheets_tracker()
    if not tracker:
        return
    rows = tracker.get_tracked_companies()
    if not rows:
        print("Belum ada data pelamaran di database.")
        return

    # 1. Tampilkan Dashboard Analytics & Conversion Rates
    metrics = compute_application_metrics(rows)
    print("\n" + format_analytics_dashboard(metrics) + "\n")

    # 2. Tampilkan Tabel Riwayat Terperinci
    print(f"{'Company':<25} | {'Position':<20} | {'Channel':<12} | {'Status':<12}")
    print("-" * 77)
    for r in rows:
        comp = str(r.get("Company", ""))[:24]
        pos = str(r.get("Position", ""))[:19]
        ch = str(r.get("Channel", ""))[:11]
        st = str(r.get("Status", ""))[:11]
        print(f"{comp:<25} | {pos:<20} | {ch:<12} | {st:<12}")

def menu_scrape_hr_leads():
    print("\n--- WEB SCRAPER EMAIL HRD & AI MATCHER ---")
    print("Sistem akan menjelajahi internet untuk mencari posting lowongan dan email HRD aktif.")
    custom = input("Masukkan kata kunci khusus [Tekan ENTER untuk default Software/AI/Python]: ").strip()
    limit_str = input("Batas target leads yang dicari [Default: 5]: ").strip()
    max_leads = int(limit_str) if limit_str.isdigit() else 5

    scraper = HRLeadsScraper(headless=True)
    print("\nMemulai web scraping & AI matching (50% Indonesia 🇮🇩 + 50% Global Remote 🌍)...")
    leads = scraper.search_balanced_leads(custom_position=custom if custom else None, total_limit=max_leads)

    if not leads:
        print("Tidak menemukan email HRD baru pada penelusuran kali ini.")
        return

    print(f"\nBerhasil menemukan {len(leads)} prospek lowongan!")
    tracker = get_sheets_tracker()
    cv_mgr = CVManager()
    mailer = get_email_handler()
    ai = AIAssistant()

    for idx, item in enumerate(leads, 1):
        if tracker and tracker.is_already_applied(item["company"], contact_or_email=item["email"]):
            print(f"\n[Anti-Duplicate] Melewati {item['company']} ({item['email']}) karena sudah ada di riwayat pelamaran.")
            continue

        print("\n" + "=" * 60)
        print(f"[{idx}/{len(leads)}] Perusahaan : {item['company']}")
        print(f"Posisi       : {item['position']}")
        print(f"Email HRD    : {item['email']}")
        print(f"Skor AI      : {item.get('match_score', 0)}% ({item.get('decision', 'SKIP')})")
        print(f"Skill Cocok  : {', '.join(item.get('matched_skills', []))}")
        print(f"Alasan AI    : {item.get('match_reason', '')}")
        print(f"Sumber       : {item.get('source', '')}")
        print("=" * 60)

        if item.get("match_score", 0) < 50:
            print(">> Melewati lowongan ini karena skor AI di bawah 50%.")
            continue

        print("\nPilihan Aksi:")
        print("1. Kirim Lamaran Sekarang (AI Cover Letter + CV otomatis)")
        print("2. Simpan ke Google Sheets saja (sebagai Lead Baru)")
        print("3. Lewati (Skip)")
        act = input("Pilih aksi (1/2/3) [Default: 1]: ").strip() or "1"

        if act == "1":
            lang = detect_language(f"{item['position']} {item['company']} {item.get('snippet', '')}")
            cv_path = cv_mgr.get_cv(lang=lang)
            subject = f"Application for {item['position']} - Muhammad Bagja Satrio" if lang == "en" else f"Lamaran Pekerjaan - {item['position']} - Muhammad Bagja Satrio"

            print("[AI] Membuat cover letter khusus lowongan ini...")
            cover_letter = ai.generate_cover_letter(item["company"], item["position"], item.get("snippet", ""), lang=lang)

            print(f"Mengirim email ke {item['email']}...")
            try:
                mailer.send_application(item["email"], subject, cover_letter, cv_path)
                print("Email lamaran berhasil dikirim!")
                if tracker:
                    rec = ApplicationRecord(
                        company=item["company"],
                        position=item["position"],
                        channel="Web Scraping",
                        status=JobStatus.APPLIED,
                        contact=item["email"],
                        notes=f"Skor AI: {item['match_score']}% | {item.get('match_reason', '')}"
                    )
                    tracker.append_record(rec)
                    print("Tercatat di Google Sheets.")
            except Exception as e:
                print(f"Gagal mengirim email: {e}")

        elif act == "2":
            if tracker:
                rec = ApplicationRecord(
                    company=item["company"],
                    position=item["position"],
                    channel="Web Scraping",
                    status=JobStatus.APPLIED,
                    contact=item["email"],
                    notes=f"Lead Baru (Skor AI: {item['match_score']}%)"
                )
                tracker.append_record(rec)
                print("Data tersimpan ke Google Sheets.")

def menu_auto_follow_up():
    print("\n--- AUTO FOLLOW-UP EMAIL LAMARAN (> 5 HARI) ---")
    tracker = get_sheets_tracker()
    if not tracker:
        print("Tracker belum terhubung.")
        return

    records = tracker.get_tracked_companies()
    stale_jobs = find_stale_applications(records, days_threshold=5)

    if not stale_jobs:
        print("Tidak ada lamaran berstatus 'Applied' yang melewati batas 5 hari tanpa kabar.")
        return

    print(f"\nDitemukan {len(stale_jobs)} lamaran yang perlu difollow-up:")
    ai = AIAssistant()
    mailer = get_email_handler()

    for idx, item in enumerate(stale_jobs, 1):
        comp = item.get("Company", "Unknown")
        pos = item.get("Position", "Developer")
        email_addr = item.get("Contact", "")
        days = item.get("days_elapsed", 5)

        print("\n" + "=" * 60)
        print(f"[{idx}/{len(stale_jobs)}] Perusahaan : {comp}")
        print(f"Posisi       : {pos}")
        print(f"Email HRD    : {email_addr}")
        print(f"Hari Berlalu : {days} hari sejak diapply")
        print("=" * 60)

        lang = detect_language(f"{pos} {comp}")
        subject = f"Following up on my application for {pos} - Muhammad Bagja Satrio" if lang == "en" else f"Follow-up Lamaran Pekerjaan - {pos} - Muhammad Bagja Satrio"

        print("[AI] Menyusun draf follow-up email...")
        body = ai.generate_follow_up(comp, pos, lang=lang)

        print("\nPREVIEW EMAIL FOLLOW-UP:")
        print("-" * 50)
        print(body)
        print("-" * 50)

        act = input(f"Kirim email follow-up ke {comp}? (y/n/skip) [Default: y]: ").strip().lower() or "y"
        if act == "y":
            print(f"Mengirim email follow-up ke {email_addr}...")
            try:
                mailer.send_follow_up(email_addr, subject, body)
                today_str = datetime.now().strftime("%Y-%m-%d")
                tracker.update_status(comp, JobStatus.APPLIED, note=f"Follow-up sent on {today_str}")
                print(f"Follow-up terkirim dan tercatat di Google Sheets!")
            except Exception as e:
                print(f"Gagal mengirim follow-up: {e}")
        else:
            print("Follow-up dilewati.")

def main():
    while True:
        print("\n==============================================")
        print("      JOB APPLICATION AUTOMATION & TRACKER     ")
        print("==============================================")
        print("1. Kirim Cold Email Lamaran (+ Catat ke Sheets)")
        print("2. Jalankan Auto-Apply Portal (+ Catat ke Sheets)")
        print("3. Scan Respon Email & Update Status Sheets")
        print("4. Lihat Rekap Status Lamaran di Sheets")
        print("5. Web Scraper Email HRD di Internet + AI Matcher")
        print("6. Auto Follow-Up Lamaran Menggantung (> 5 Hari)")
        print("7. Jalankan Telegram Bot Remote Control (Listener HP)")
        print("8. Keluar")
        choice = input("\nPilih menu (1-8): ").strip()

        if choice == "1":
            menu_send_email()
        elif choice == "2":
            menu_portal_apply()
        elif choice == "3":
            menu_scan_inbox()
        elif choice == "4":
            menu_view_status()
        elif choice == "5":
            menu_scrape_hr_leads()
        elif choice == "6":
            menu_auto_follow_up()
        elif choice == "7":
            from src.notifier.telegram_bot import TelegramBotListener
            listener = TelegramBotListener()
            listener.run_polling_loop()
        elif choice == "8":
            print("Selesai.")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()
