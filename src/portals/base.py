from playwright.sync_api import sync_playwright, Page, BrowserContext
import time
import random
import os

class BasePortalBot:
    def __init__(self, user_data_dir: str = "./browser_session"):
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.playwright = None
        self.context: BrowserContext = None
        self.page: Page = None

    def start_browser(self, headless: bool = False) -> Page:
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=headless,
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        return self.page

    def human_delay(self, min_s: float = 2.0, max_s: float = 4.5):
        time.sleep(random.uniform(min_s, max_s))

    def close(self):
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
