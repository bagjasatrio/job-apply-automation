from typing import List
import os
from src.portals.base import BasePortalBot
from src.models import ApplicationRecord, JobStatus
from src.ai_assistant import AIAssistant
from src.sheets import get_tracker

DAILY_APPLY_LIMIT = 15

class GlintsBot(BasePortalBot):
    def apply_glints_jobs(self, keyword: str, max_apply: int = 5, headless: bool = False) -> List[ApplicationRecord]:
        tracker = get_tracker()
        today_applied = tracker.get_today_apply_count()
        if today_applied >= DAILY_APPLY_LIMIT:
            print(f"[Quota Guard] Batas aman harian ({DAILY_APPLY_LIMIT} lamaran) sudah tercapai.")
            return []

        page = self.start_browser(headless=headless)
        results = []
        assistant = AIAssistant() if os.getenv("GEMINI_API_KEY") else None

        from src.target_roles import CORE_JOB_TITLES
        import urllib.parse

        if keyword.lower() in ["all", "semua", "any", "it", ""]:
            search_keywords = CORE_JOB_TITLES
        else:
            search_keywords = [keyword]

        for kw in search_keywords:
            if len(results) >= max_apply or (today_applied + len(results)) >= DAILY_APPLY_LIMIT:
                break

            encoded_kw = urllib.parse.quote_plus(kw)
            url = f"https://glints.com/id/opportunities/jobs/explore?keyword={encoded_kw}&country=ID"
            print(f"[Glints] Membuka pencarian lowongan: {kw}")
            try:
                page.goto(url)
                self.human_delay(2.5, 4.0)
            except Exception as e:
                print(f"[Glints] Gagal membuka {kw}: {e}")
                continue

            # Cek status login
            if page.query_selector("button:has-text('Masuk'), a:has-text('Masuk')"):
                print("[Glints] Silakan login manual pada jendela browser jika belum login.")
                input("Tekan ENTER setelah selesai login di Glints...")

            job_cards = page.query_selector_all("div[class*='JobCard'], div[data-testid='job-card']")
            print(f"[Glints] Ditemukan {len(job_cards)} lowongan untuk '{kw}'.")

            for idx, card in enumerate(job_cards):
                if len(results) >= max_apply or (today_applied + len(results)) >= DAILY_APPLY_LIMIT:
                    break
                try:
                    card.scroll_into_view_if_needed()
                    card.click()
                    self.human_delay(2.0, 3.5)

                    title_el = page.query_selector("h1[class*='TopFold__JobOverViewTitle']")
                    company_el = page.query_selector("a[class*='TopFold__CompanyLink']")

                    title = title_el.inner_text().strip() if title_el else kw
                    company = company_el.inner_text().strip() if company_el else "Glints Company"

                    if tracker.is_already_applied(company):
                        print(f"[Anti-Duplicate] Dilewati: {company} sudah pernah dilamar.")
                        continue

                    desc_el = page.query_selector("div[class*='JobDescription'], div[class*='DescriptionContainer']")
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

                    apply_btn = page.query_selector("button:has-text('Lamar Cepat'), button:has-text('Apply Now'), button:has-text('Lamar')")
                    if apply_btn:
                        print(f"[Glints] Menjalankan pelamaran untuk: {title} di {company}")
                        apply_btn.click()
                        self.human_delay(2.0, 3.0)

                        record = ApplicationRecord(
                            company=company,
                            position=title,
                            channel="Glints",
                            status=JobStatus.APPLIED,
                            notes="Applied via Glints Portal"
                        )
                        results.append(record)
                except Exception as e:
                    print(f"[Glints] Gagal memproses card {idx}: {e}")
                    continue

        self.close()
        return results
