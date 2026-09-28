from typing import List
import os
from src.portals.base import BasePortalBot
from src.models import ApplicationRecord, JobStatus
from src.ai_assistant import AIAssistant
from src.sheets import get_tracker

DAILY_APPLY_LIMIT = 15

class JobstreetBot(BasePortalBot):
    def apply_jobstreet_jobs(self, keyword: str, max_apply: int = 5, headless: bool = False) -> List[ApplicationRecord]:
        tracker = get_tracker()
        today_applied = tracker.get_today_apply_count()
        if today_applied >= DAILY_APPLY_LIMIT:
            print(f"[Quota Guard] Batas aman harian ({DAILY_APPLY_LIMIT} lamaran) sudah tercapai.")
            return []

        page = self.start_browser(headless=headless)
        results = []
        assistant = AIAssistant() if os.getenv("GEMINI_API_KEY") else None

        from src.target_roles import CORE_JOB_TITLES

        if keyword.lower() in ["all", "semua", "any", "it", ""]:
            search_keywords = CORE_JOB_TITLES
        else:
            search_keywords = [keyword]

        for kw in search_keywords:
            if len(results) >= max_apply or (today_applied + len(results)) >= DAILY_APPLY_LIMIT:
                break

            slug_kw = kw.lower().replace(" ", "-")
            url = f"https://www.jobstreet.co.id/id/{slug_kw}-jobs"
            print(f"[Jobstreet] Membuka pencarian lowongan: {kw}")
            try:
                page.goto(url)
                self.human_delay(2.5, 4.0)
            except Exception as e:
                print(f"[Jobstreet] Gagal membuka {kw}: {e}")
                continue

            # Cek login
            if page.query_selector("a[data-automation='login-link']"):
                print("[Jobstreet] Silakan login manual pada jendela browser jika belum login.")
                input("Tekan ENTER setelah selesai login di Jobstreet...")

            cards = page.query_selector_all("article[data-automation='job-card']")
            print(f"[Jobstreet] Ditemukan {len(cards)} kartu lowongan untuk '{kw}'.")

            for idx, card in enumerate(cards):
                if len(results) >= max_apply or (today_applied + len(results)) >= DAILY_APPLY_LIMIT:
                    break
                try:
                    card.scroll_into_view_if_needed()
                    card.click()
                    self.human_delay(2.0, 3.5)

                    title_el = page.query_selector("h1[data-automation='job-detail-title']")
                    company_el = page.query_selector("span[data-automation='advertiser-name']")

                    title = title_el.inner_text().strip() if title_el else kw
                    company = company_el.inner_text().strip() if company_el else "Jobstreet Company"

                    if tracker.is_already_applied(company):
                        print(f"[Anti-Duplicate] Dilewati: {company} sudah pernah dilamar.")
                        continue

                    desc_el = page.query_selector("div[data-automation='jobDescription']")
                    job_desc = desc_el.inner_text().strip() if desc_el else ""

                    if assistant and job_desc:
                        print(f"[AI Screen] Menganalisa kecocokan CV untuk: {title} di {company}...")
                        eval_res = assistant.screen_job_qualification(title, job_desc[:1500])
                        score = eval_res.get("score", 0)
                        is_match = eval_res.get("is_match", True)
                        reason = eval_res.get("reason", "")
                        if not is_match or score < 50:
                            print(f"[AI Screen] Dilewati (Skor: {score}%). Alasan: {reason}")
                            continue
                        else:
                            print(f"[AI Screen] Cocok (Skor: {score}%). Alasan: {reason}")

                    apply_btn = page.query_selector("a[data-automation='job-detail-apply']")
                    if apply_btn:
                        print(f"[Jobstreet] Deteksi lowongan: {title} di {company}")
                        record = ApplicationRecord(
                            company=company,
                            position=title,
                            channel="Jobstreet",
                            status=JobStatus.APPLIED,
                            notes="Applied via Jobstreet"
                        )
                        results.append(record)
                except Exception as e:
                    print(f"[Jobstreet] Error kartu {idx}: {e}")
                    continue
                print(f"[Jobstreet] Error: {e}")
                continue

        self.close()
        return results
