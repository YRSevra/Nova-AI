"""
modules/browser.py — Browser Automation (Phase 2)
──────────────────────────────────────────────────
Controls a web browser using Playwright.

SETUP (run once after pip install):
    playwright install chromium

CAPABILITIES:
- Open websites
- Click buttons
- Fill forms
- Scrape content
- Automate logins

Example Nova commands that will trigger this module:
- "Fill my name in the form"
- "Book a flight from Ahmedabad to Mumbai"
- "Scroll down and click the download button"

NOTE: This module is for Phase 2. It's included here as a stub
so you can see the structure and start building it.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """Controls a browser using Playwright for web automation."""

    def __init__(self, config: dict):
        self.config = config
        self._browser = None
        self._page = None

    def start(self):
        """Launch the browser (headless by default)."""
        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=False  # Set True to run without visible window
            )
            self._page = self._browser.new_page()
            logger.info("Browser started")
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")

    def stop(self):
        """Close the browser."""
        if self._browser:
            self._browser.close()
        if hasattr(self, '_playwright'):
            self._playwright.stop()

    def open_url(self, url: str) -> str:
        """Open a URL and return the page title."""
        if not self._page:
            self.start()
        self._page.goto(url)
        return self._page.title()

    def click(self, selector: str):
        """Click a button or link by CSS selector."""
        self._page.click(selector)

    def fill_form(self, selector: str, value: str):
        """Fill a form field."""
        self._page.fill(selector, value)

    def get_text(self, selector: str) -> str:
        """Get text content from an element."""
        return self._page.inner_text(selector)

    def search_google(self, query: str) -> str:
        """Open Google and search for something."""
        if not self._page:
            self.start()
        self._page.goto("https://www.google.com")
        self._page.fill('input[name="q"]', query)
        self._page.press('input[name="q"]', "Enter")
        self._page.wait_for_load_state("networkidle")
        return f"Google search results for '{query}' are open."

    def screenshot(self, path: str = "screenshot.png"):
        """Take a screenshot of the current page."""
        if self._page:
            self._page.screenshot(path=path)
            return path
        return None
