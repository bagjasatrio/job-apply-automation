from typing import List, Dict, Any, Optional
import os
from src.portals.base import BasePortalBot
from src.models import ApplicationRecord, JobStatus
from src.ai_assistant import AIAssistant
from src.sheets import get_tracker
from src.security.date_filter import is_within_recency
from src.security.location_filter import is_location_acceptable

DAILY_APPLY_LIMIT = 15

class LinkedInBot(BasePortalBot):
    def apply_easy_jobs(
        self,
        keyword: str,
        location: str = "Indonesia",
        max_apply: int = 5,
        headless: bool = False,
        remote_only: bool = False
    ) -> List[ApplicationRecord]:
        tracker = get_tracker()
        today_applied = tracker.get_today_apply_count()
        if today_applied >= DAILY_APPLY_LIMIT:
            print(f"[Quota Guard] Batas aman harian ({DAILY_APPLY_LIMIT} lamaran) sudah tercapai untuk hari ini. Disarankan istirahat untuk menjaga reputasi akun.")
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
            url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_kw}&location={location}&f_AL=true&f_TPR=r5184000"
            if remote_only:
                url += "&f_WT=2"
            print(f"[LinkedIn] Navigasi lowongan: {kw} di {location} ({url})")
            try:
                page.goto(url)
                self.human_delay(2.5, 4.0)
            except Exception as e:
                print(f"[LinkedIn] Gagal memuat halaman {kw}: {e}")
                continue

            # Cek apakah butuh login
            if "login" in page.url or page.query_selector("input#username"):
                print("[LinkedIn] Sesi belum login. Silakan login manual pada jendela browser yang terbuka.")
                print("[LinkedIn] Sesi browser akan disimpan otomatis di folder session.")
                input("Tekan ENTER setelah selesai login di browser...")

            cards = page.query_selector_all(".job-card-container, .jobs-search-results__list-item")
            print(f"[LinkedIn] Ditemukan {len(cards)} kartu lowongan untuk '{kw}'.")

            for idx, card in enumerate(cards):
                if len(results) >= max_apply or (today_applied + len(results)) >= DAILY_APPLY_LIMIT:
                    break
                try:
                    card.scroll_into_view_if_needed()
                    card.click()
                    self.human_delay(2.0, 3.5)

                    title_el = page.query_selector(".job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title")
                    company_el = page.query_selector(".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name")

                    job_title = title_el.inner_text().strip() if title_el else kw
                    company_name = company_el.inner_text().strip() if company_el else "Unknown Company"

                    # 1. Anti-Duplicate Check
                    if tracker.is_already_applied(company_name):
                        print(f"[Anti-Duplicate] Dilewati: {company_name} sudah pernah dilamar sebelumnya.")
                        continue

                    # 2. Filter Waktu Lowongan: Maksimal 1-2 Bulan (60 hari)
                    card_text = card.inner_text() if card else ""
                    is_recent, date_reason = is_within_recency(f"{job_title} {card_text}", max_days=60)
                    if not is_recent:
                        print(f"[Date Filter] Dilewati: {company_name} ({job_title}) karena {date_reason}.")
                        continue

                    # 3. Filter Lokasi & Mode Kerja: Luar Jawa WAJIB Remote / WFH (WFO/Hybrid skip)
                    loc_ok, loc_reason = is_location_acceptable(f"{job_title} {card_text}", location_hint=location)
                    if not loc_ok:
                        print(f"[Location Filter] Dilewati: {company_name} ({job_title}) karena {loc_reason}.")
                        continue

                    # 2. Ekstrak deskripsi lowongan untuk screening AI
                    desc_el = page.query_selector(".jobs-description__content, #job-details, .jobs-box__html-content")
                    job_desc = desc_el.inner_text().strip() if desc_el else ""

                    if assistant and job_desc:
                        print(f"[AI Screen] Menganalisa kecocokan CV untuk: {job_title} di {company_name}...")
                        eval_res = assistant.screen_job_qualification(job_title, job_desc[:1500])
                        score = eval_res.get("score", 0)
                        is_match = eval_res.get("is_match", True)
                        reason = eval_res.get("reason", "")
                        if not is_match or score < 50:
                            print(f"[AI Screen] Dilewati (Skor: {score}%). Alasan: {reason}")
                            continue
                        else:
                            print(f"[AI Screen] Cocok (Skor: {score}%). Alasan: {reason}")

                    # 3. Cari tombol Easy Apply
                    apply_button = page.query_selector("button.jobs-apply-button")
                    if apply_button:
                        text = apply_button.inner_text().lower()
                        if "easy apply" in text or "lamar cepat" in text:
                            print(f"[LinkedIn] Menjalankan Easy Apply untuk: {job_title} di {company_name}")
                            apply_button.click()
                            self.human_delay(2.0, 3.0)

                            # 4. Tangani multi-step modal & AI Form Answerer
                            submitted = self._handle_modal_steps(page, assistant)

                            if submitted:
                                record = ApplicationRecord(
                                    company=company_name,
                                    position=job_title,
                                    channel="LinkedIn",
                                    status=JobStatus.APPLIED,
                                    notes="Applied via LinkedIn Easy Apply (AI Answered)"
                                )
                                results.append(record)
                except Exception as e:
                    print(f"[LinkedIn] Gagal apply pada card {idx}: {e}")
                    continue
                continue

        self.close()
        return results

    def _handle_modal_steps(self, page, assistant: Optional[AIAssistant], max_steps: int = 5) -> bool:
        """Menangani modal step Easy Apply dan menjawab pertanyaan formulir via AI."""
        for _ in range(max_steps):
            modal = page.query_selector("div.jobs-easy-apply-modal, div[role='dialog']")
            if not modal:
                return True

            # Jawab pertanyaan input teks/angka jika ada
            if assistant:
                inputs = modal.query_selector_all("input[type='text'], input[type='number'], textarea")
                for inp in inputs:
                    try:
                        val = inp.input_value()
                        if not val:
                            inp_id = inp.get_attribute("id") or ""
                            label_el = modal.query_selector(f"label[for='{inp_id}']") if inp_id else None
                            q_text = label_el.inner_text().strip() if label_el else "Experience"
                            f_type = inp.get_attribute("type") or "text"
                            ans = assistant.answer_screening_question(q_text, field_type=f_type)
                            inp.fill(str(ans))
                            self.human_delay(0.4, 0.8)
                    except Exception:
                        pass

                # Jawab radio button
                fieldsets = modal.query_selector_all("fieldset")
                for fs in fieldsets:
                    try:
                        checked = fs.query_selector("input[type='radio']:checked")
                        if not checked:
                            legend = fs.query_selector("legend")
                            q_text = legend.inner_text().strip() if legend else ""
                            radios = fs.query_selector_all("input[type='radio']")
                            labels = [fs.query_selector(f"label[for='{r.get_attribute('id')}']") for r in radios if r.get_attribute("id")]
                            options = [l.inner_text().strip() for l in labels if l]
                            if q_text and options:
                                choice = assistant.answer_screening_question(q_text, field_type="choice", options=options)
                                for r, l in zip(radios, labels):
                                    if l and choice.lower() in l.inner_text().lower():
                                        r.click()
                                        break
                    except Exception:
                        pass

            # Cek apakah ada tombol Submit
            submit_btn = modal.query_selector("button[aria-label='Submit application'], button[aria-label='Kirim lamaran'], button:has-text('Submit application'), button:has-text('Kirim lamaran')")
            if submit_btn and submit_btn.is_visible():
                submit_btn.click()
                self.human_delay(2.0, 3.0)
                return True

            # Cek tombol Next / Review
            next_btn = modal.query_selector("button[aria-label='Continue to next step'], button[aria-label='Review your application'], button:has-text('Next'), button:has-text('Review')")
            if next_btn and next_btn.is_visible():
                next_btn.click()
                self.human_delay(1.5, 2.5)
            else:
                break

        return False

    def apply_balanced_jobs(
        self,
        keyword: str = "Software Engineer",
        total_apply: int = 4,
        headless: bool = False
    ) -> List[ApplicationRecord]:
        """Melamar dengan pembagian seimbang: 50% Indonesia dan 50% Global Worldwide Remote."""
        id_target = total_apply // 2
        global_target = total_apply - id_target

        print(f"\n[LinkedIn Balanced] Alokasi target: {id_target} Indonesia, {global_target} Global Remote")
        id_results = self.apply_easy_jobs(keyword=keyword, location="Indonesia", max_apply=id_target, headless=headless, remote_only=False)
        global_results = self.apply_easy_jobs(keyword=keyword, location="Worldwide", max_apply=global_target, headless=headless, remote_only=True)

        return id_results + global_results
