from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable

try:
    from playwright.sync_api import Page, sync_playwright
except ImportError:  # pragma: no cover - dependency may be absent in tests
    Page = object  # type: ignore[assignment]
    sync_playwright = None

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RawAdRecord:
    platform: str
    payload: dict


class BaseScraper:
    """Base scraper contract used by the main pipeline and tests."""

    def scrape(self, game_name: str | None = None) -> list[RawAdRecord]:
        raise NotImplementedError


class MockScraper(BaseScraper):
    """Deterministic scraper used for local development and tests."""

    def __init__(self, platform: str, records: Iterable[dict] | None = None) -> None:
        self.platform = platform
        self._records = list(records or self._default_records(platform))

    def scrape(self, game_name: str | None = None) -> list[RawAdRecord]:
        logger.info("mock scrape started", extra={"platform": self.platform, "game_name": game_name})
        return [RawAdRecord(platform=self.platform, payload=record) for record in self._records]

    @staticmethod
    def _default_records(platform: str) -> list[dict]:
        return [
            {
                "game_name": "Whiteout Survival",
                "hook": "Build your shelter before the storm hits.",
                "creative_type": "video",
                "country": "US",
                "first_seen": "2026-03-01 12:00:00",
                "last_seen": "2026-03-07 12:00:00",
            },
            {
                "game_name": "Gossip Harbor",
                "hook": "Merge your way to unlock seaside secrets.",
                "creative_type": "image",
                "country": "GB",
                "first_seen": "2026-03-03 09:15:00",
                "last_seen": "2026-03-10 16:45:00",
            },
        ]


class PlaywrightCreativeCenterScraper(BaseScraper):
    """Minimal Playwright scraper shell for future real-site integration."""

    def __init__(
        self,
        platform: str,
        start_url: str,
        max_scroll: int = 10,
        delay_seconds: int = 2,
        headless: bool = True,
        card_selector: str = "[data-e2e='ad-card']",
    ) -> None:
        self.platform = platform
        self.start_url = start_url
        self.max_scroll = max_scroll
        self.delay_seconds = delay_seconds
        self.headless = headless
        self.card_selector = card_selector

    def scrape(self, game_name: str | None = None) -> list[RawAdRecord]:
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed. Run `pip install -r requirements.txt` first.")

        logger.info("playwright scrape started", extra={"platform": self.platform, "game_name": game_name})
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            page = browser.new_page()
            try:
                page.goto(self.start_url, wait_until="domcontentloaded", timeout=60000)
                self._scroll_page(page)
                cards = page.locator(self.card_selector)
                records: list[RawAdRecord] = []
                for index in range(cards.count()):
                    text = cards.nth(index).inner_text()
                    records.append(RawAdRecord(platform=self.platform, payload={"raw_text": text}))
                logger.info("playwright scrape completed", extra={"platform": self.platform, "records": len(records)})
                return records
            finally:
                browser.close()

    def _scroll_page(self, page: Page) -> None:
        for _ in range(self.max_scroll):
            page.mouse.wheel(0, 3000)
            time.sleep(self.delay_seconds)

