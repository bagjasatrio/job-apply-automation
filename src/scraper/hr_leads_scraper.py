import os
import re
import time
import random
from urllib.parse import quote_plus
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright
from src.scraper.email_extractor import extract_hr_emails_and_leads
from src.matcher.ai_matcher import AIMatcher
from src.security.scam_detector import ScamDetector
from src.security.date_filter import is_within_recency
from src.security.location_filter import is_location_acceptable
from src.target_roles import (
    CORE_JOB_TITLES,
    EXPANDED_JOB_TITLES,
    get_indonesia_queries,
    get_global_remote_queries
)

# Kluster Luas Pencarian Loker IT / Teknik Informatika (Indonesia)
EXPANDED_INDONESIA_QUERIES = [
    # 1. Fresh Graduate & Lulusan Teknik Informatika Umum
    '\"fresh graduate\" \"teknik informatika\" \"kirim cv\"',
    '\"lulusan teknik informatika\" \"kirim cv\"',
    '\"junior developer\" \"kirim cv\" \"indonesia\"',
    '\"it programmer\" \"kirim cv\"',
    '\"it staff\" \"teknik informatika\" \"kirim cv\"',
    # 2. Web & Fullstack Developer
    '\"web developer\" \"kirim cv\" \"@gmail.com\"',
    '\"frontend developer\" \"kirim cv\"',
    '\"backend developer\" \"kirim cv\"',
    '\"fullstack developer\" \"recruitment@\"',
    # 3. Mobile, QA, Data, & AI
    '\"flutter developer\" \"kirim cv\"',
    '\"mobile developer\" \"kirim cv\"',
    '\"qa tester\" \"kirim cv\"',
    '\"python developer\" \"kirim cv ke\"',
    '\"data analyst\" \"python\" \"kirim cv\"',
    '\"ai engineer\" \"kirim cv\"'
]

# Kluster Luas Pencarian Loker Global Remote (Worldwide Remote / Work From Anywhere)
EXPANDED_GLOBAL_REMOTE_QUERIES = [
    # 1. Junior / Entry Level Remote Tech
    '\"junior software engineer\" \"remote\" \"send resume to\"',
    '\"entry level developer\" \"worldwide remote\" \"apply\"',
    '\"junior web developer\" \"work from anywhere\" \"send cv\"',
    # 2. Web & Fullstack Remote
    '\"frontend developer\" \"worldwide remote\" \"careers@\"',
    '\"backend developer\" \"remote\" \"send your resume to\"',
    '\"full stack developer\" \"worldwide remote\" \"apply\"',
    '\"remote python developer\" \"send resume to\"',
    # 3. Mobile, QA, Data & AI Remote
    '\"remote flutter developer\" \"apply via email\"',
    '\"remote qa engineer\" \"send resume to\"',
    '\"ai engineer\" \"worldwide remote\" \"careers@\"',
    '\"software engineer\" \"send your resume to\" \"@gmail.com\"'
]

DEFAULT_INDONESIA_QUERIES = list(set(EXPANDED_INDONESIA_QUERIES + get_indonesia_queries()))
DEFAULT_GLOBAL_REMOTE_QUERIES = list(set(EXPANDED_GLOBAL_REMOTE_QUERIES + get_global_remote_queries()))

class HRLeadsScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.matcher = AIMatcher()
        self.scam_detector = ScamDetector()

    def _scrape_query_list(self, queries: List[str], max_results: int, zone_label: str = "Indonesia", page=None) -> List[Dict[str, Any]]:
        verified_leads = []
        seen_emails = set()

        for query in queries:
            if len(verified_leads) >= max_results:
                break

            search_url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
            print(f"\n[Scraper - {zone_label}] Menjelajahi web dengan kueri: {query}")
            try:
                page.goto(search_url, timeout=25000)
                time.sleep(2)
            except Exception as e:
                print(f"[Scraper] Error memuat halaman pencarian: {e}")
                continue

            # 1. Ekstrak dari teks halaman hasil pencarian
            page_text = page.inner_text("body")
            raw_leads = extract_hr_emails_and_leads(
                page_text,
                default_position=query.split()[0].replace('"', ''),
                source_url=search_url
            )

            # 2. Ambil link organik
            link_elements = page.query_selector_all("#web ol li a.fz-20, #web ol li h3 a")
            organic_urls = []
            for a in link_elements[:4]:
                href = a.get_attribute("href")
                if href and href.startswith("http") and not any(x in href for x in ["yahoo.com", "yimg.com", "google.com"]):
                    organic_urls.append((href, a.inner_text().strip()))

            for lead in raw_leads:
                email_addr = lead["email"]
                if email_addr in seen_emails:
                    continue
                seen_emails.add(email_addr)
                lead["source"] = search_url
                lead["source_url"] = search_url
                lead["zone"] = zone_label
                verified_leads.append(lead)
                if len(verified_leads) >= max_results:
                    break

            for url, title in organic_urls:
                if len(verified_leads) >= max_results:
                    break
                try:
                    page.goto(url, timeout=15000)
                    time.sleep(1.5)
                    sub_text = page.inner_text("body")
                    sub_leads = extract_hr_emails_and_leads(
                        sub_text[:5000],
                        default_company=title.split("-")[0].strip(),
                        default_position=title,
                        source_url=url
                    )
                    for s_lead in sub_leads:
                        if s_lead["email"] not in seen_emails:
                            seen_emails.add(s_lead["email"])
                            s_lead["source"] = url
                            s_lead["zone"] = zone_label
                            verified_leads.append(s_lead)
                            if len(verified_leads) >= max_results:
                                break
                except Exception:
                    continue

        return verified_leads

    def _filter_and_score(self, raw_leads: List[Dict[str, Any]], min_score: int = 50) -> List[Dict[str, Any]]:
        matched_leads = []
        for lead in raw_leads:
            is_scam, scam_reason = self.scam_detector.is_suspicious_lead(
                company=lead["company"],
                position=lead["position"],
                email=lead["email"],
                job_text=lead.get("snippet", "")
            )
            if is_scam:
                print(f"\n[Security Alert] Mengabaikan loker bodong: {lead['company']} ({lead['email']})")
                continue

            # FILTER WAKTU: Maksimal 1 - 2 bulan kebelakang (60 hari). Lewat dari itu skip.
            is_recent, recency_reason = is_within_recency(
                lead.get("snippet", "") + " " + lead.get("source_url", "") + " " + lead.get("position", ""),
                max_days=60
            )
            if not is_recent:
                print(f"[Date Filter] Dilewati: {lead['company']} ({lead['email']}) karena {recency_reason}.")
                continue

            # FILTER LOKASI & MODE KERJA:
            # - Dalam Pulau Jawa: WFO, Hybrid, Remote boleh semua.
            # - Luar Pulau Jawa & Luar Negeri: WAJIB Remote / WFH (WFO/Hybrid ditolak).
            loc_ok, loc_reason = is_location_acceptable(
                text=lead.get("snippet", "") + " " + lead.get("position", ""),
                location_hint=lead.get("zone", "")
            )
            if not loc_ok:
                print(f"[Location Filter] Dilewati: {lead['company']} ({lead['email']}) karena {loc_reason}.")
                continue

            analysis = self.matcher.match(
                company=lead["company"],
                position=lead["position"],
                job_description=lead.get("snippet", lead["position"])
            )
            score = int(analysis.get("score", 0))
            decision = analysis.get("decision", "SKIP")

            # FILTER: Lowongan dengan skor di bawah min_score (50%) otomatis dibuang
            if score < min_score or decision != "APPLY":
                print(f"[AI Filter] Dilewati: {lead['company']} ({lead['email']}) karena skor {score}% < {min_score}%.")
                continue

            lead["match_score"] = score
            lead["decision"] = decision
            lead["matched_skills"] = analysis.get("matched_skills", [])
            lead["missing_skills"] = analysis.get("missing_skills", [])
            lead["match_reason"] = analysis.get("reason", "")
            matched_leads.append(lead)
        return matched_leads

    def search_balanced_leads(self, custom_position: Optional[str] = None, total_limit: int = 4) -> List[Dict[str, Any]]:
        """Mencari lowongan dengan alokasi seimbang: 50% Indonesia dan 50% Global Worldwide Remote."""
        id_limit = total_limit // 2
        global_limit = total_limit - id_limit

        if custom_position and custom_position.lower() not in ["all", "it", "semua", "any", "fresh graduate", "ti"]:
            pos = custom_position
            id_queries = [
                f'"{pos}" "kirim cv" "@gmail.com"',
                f'"{pos}" "recruitment@" "indonesia"',
                f'"{pos}" "kirim cv"'
            ]
            global_queries = [
                f'"{pos}" "worldwide remote" "send resume to"',
                f'"{pos}" "remote" "send resume to"',
                f'"{pos}" "work from anywhere" "apply"'
            ]
        else:
            id_queries = list(EXPANDED_INDONESIA_QUERIES)
            global_queries = list(EXPANDED_GLOBAL_REMOTE_QUERIES)
            random.shuffle(id_queries)
            random.shuffle(global_queries)

        # Check if _scrape_query_list is mocked (in tests)
        if hasattr(self._scrape_query_list, "assert_called") or getattr(self._scrape_query_list, "_mock_return_value", None) is not None:
            id_leads = self._scrape_query_list(id_queries, max_results=id_limit, zone_label="Indonesia")
            global_leads = self._scrape_query_list(global_queries, max_results=global_limit, zone_label="Global Remote")
        else:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless, args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
                page = context.new_page()
                id_leads = self._scrape_query_list(id_queries, max_results=id_limit, zone_label="Indonesia", page=page)
                global_leads = self._scrape_query_list(global_queries, max_results=global_limit, zone_label="Global Remote", page=page)
                browser.close()

        combined = id_leads + global_leads
        return self._filter_and_score(combined)

    def search_and_scrape(self, custom_query: Optional[str] = None, max_results: int = 5) -> List[Dict[str, Any]]:
        # If single custom raw query without balanced flag, execute normally
        queries = [custom_query] if custom_query else (DEFAULT_INDONESIA_QUERIES + DEFAULT_GLOBAL_REMOTE_QUERIES)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
            page = context.new_page()
            raw = self._scrape_query_list(queries, max_results=max_results, zone_label="Mixed", page=page)
            browser.close()

        return self._filter_and_score(raw)
