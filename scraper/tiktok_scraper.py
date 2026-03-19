from __future__ import annotations

import logging
import re
import time
from urllib.parse import quote_plus

from scraper.playwright_scraper import BaseScraper, RawAdRecord

try:
    from playwright.sync_api import Locator, Page, sync_playwright
except ImportError:  # pragma: no cover - dependency may be absent in tests
    Locator = object  # type: ignore[assignment]
    Page = object  # type: ignore[assignment]
    sync_playwright = None

logger = logging.getLogger(__name__)


class TikTokCreativeCenterScraper(BaseScraper):
    DEFAULT_CARD_SELECTORS = [
        "[data-e2e='creative-card']",
        "[data-e2e='ad-card']",
        "[class*='CreativeCard']",
        "[class*='creative-card']",
    ]
    DEFAULT_HOOK_SELECTORS = [
        "[data-e2e='creative-caption']",
        "[data-e2e='card-caption']",
        "[class*='caption']",
        "[class*='desc']",
    ]
    DEFAULT_GAME_SELECTORS = [
        "[data-e2e='app-name']",
        "[class*='appName']",
        "[class*='app-name']",
        "[class*='title']",
    ]
    DEFAULT_COUNTRY_SELECTORS = [
        "[data-e2e='country']",
        "[class*='country']",
        "span:has-text('Country')",
    ]
    DEFAULT_FIRST_SEEN_SELECTORS = [
        "[data-e2e='first-seen']",
        "[class*='firstSeen']",
        "span:has-text('First seen')",
    ]
    DEFAULT_LAST_SEEN_SELECTORS = [
        "[data-e2e='last-seen']",
        "[class*='lastSeen']",
        "span:has-text('Last seen')",
    ]
    DEFAULT_CREATIVE_TYPE_SELECTORS = [
        "[data-e2e='creative-type']",
        "[class*='creativeType']",
        "[class*='tag']",
    ]

    def __init__(
        self,
        start_url: str = "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en",
        max_scroll: int = 10,
        delay_seconds: int = 2,
        headless: bool = True,
        card_selectors: list[str] | None = None,
        timeout_ms: int = 60000,
        max_cards: int = 5,
    ) -> None:
        self.platform = "tiktok"
        self.start_url = start_url
        self.max_scroll = max_scroll
        self.delay_seconds = delay_seconds
        self.headless = headless
        self.card_selectors = card_selectors or self.DEFAULT_CARD_SELECTORS
        self.timeout_ms = timeout_ms
        self.max_cards = max_cards

    def scrape(self, game_name: str | None = None) -> list[RawAdRecord]:
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed. Run `pip install -r requirements.txt` first.")

        target_url = self.build_search_url(game_name)
        logger.info("tiktok scrape started", extra={"game_name": game_name, "url": target_url})

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                self.dismiss_cookie_banner(page)
                self.scroll_page(page)
                cards = self.resolve_cards(page)
                records = self.extract_records(page, cards, game_name=game_name)
                logger.info("tiktok scrape completed", extra={"records": len(records), "game_name": game_name})
                return records
            finally:
                context.close()
                browser.close()

    def build_search_url(self, game_name: str | None) -> str:
        if not game_name:
            return self.start_url
        separator = "&" if "?" in self.start_url else "?"
        return f"{self.start_url}{separator}keyword={quote_plus(game_name)}"

    def dismiss_cookie_banner(self, page: Page) -> None:
        button_selectors = [
            "button:has-text('Accept')",
            "button:has-text('I agree')",
            "button:has-text('Allow all')",
        ]
        for selector in button_selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=1000):
                    button.click(timeout=1000)
                    return
            except Exception:
                continue

    def scroll_page(self, page: Page) -> None:
        for _ in range(self.max_scroll):
            page.mouse.wheel(0, 4000)
            time.sleep(self.delay_seconds)

    def resolve_cards(self, page: Page):
        for selector in self.card_selectors:
            try:
                locator = page.locator(selector)
                count = locator.count()
                if count > 0:
                    logger.info("card selector matched", extra={"selector": selector, "count": count})
                    return locator
            except Exception:
                continue
        fallback_selector = "div[class*='TopadsVideoCard_card__']"
        locator = page.locator(fallback_selector)
        if locator.count() > 0:
            logger.info("card selector matched", extra={"selector": fallback_selector, "count": locator.count()})
            return locator
        raise RuntimeError("No TikTok creative cards found. Update selectors or verify the page layout.")

    def extract_records(self, page: Page, cards, game_name: str | None = None) -> list[RawAdRecord]:
        records: list[RawAdRecord] = []
        for index in range(min(cards.count(), self.max_cards)):
            card = cards.nth(index)
            payload = self.extract_card_payload(card, fallback_game_name=game_name)
            detail_href = self.extract_detail_href(card)
            if detail_href:
                payload.update(self.fetch_detail_payload(page, detail_href))
            if payload.get("hook"):
                records.append(RawAdRecord(platform=self.platform, payload=payload))
        return records

    def extract_card_payload(self, card: Locator, fallback_game_name: str | None = None) -> dict:
        full_text = self.safe_inner_text(card)
        return {
            "game_name": self.extract_text(card, self.DEFAULT_GAME_SELECTORS) or fallback_game_name or self.extract_game_name_from_text(full_text),
            "hook": self.extract_text(card, self.DEFAULT_HOOK_SELECTORS) or self.extract_hook_from_text(full_text),
            "creative_type": self.extract_text(card, self.DEFAULT_CREATIVE_TYPE_SELECTORS) or self.infer_creative_type(full_text),
            "country": self.extract_text(card, self.DEFAULT_COUNTRY_SELECTORS) or self.extract_country_from_text(full_text),
            "first_seen": self.extract_text(card, self.DEFAULT_FIRST_SEEN_SELECTORS) or self.extract_date_from_text(full_text, "first"),
            "last_seen": self.extract_text(card, self.DEFAULT_LAST_SEEN_SELECTORS) or self.extract_date_from_text(full_text, "last"),
            "source_text": full_text,
        }

    def extract_detail_href(self, card: Locator) -> str | None:
        try:
            href = card.locator("a[href*='/business/creativecenter/topads/']").first.get_attribute("href")
        except Exception:
            return None
        if not href:
            return None
        if href.startswith("http"):
            return href
        return f"https://ads.tiktok.com{href}"

    def fetch_detail_payload(self, page: Page, detail_url: str) -> dict:
        detail_page = page.context.new_page()
        try:
            detail_page.goto(detail_url, wait_until="domcontentloaded", timeout=min(self.timeout_ms, 30000))
            detail_page.wait_for_timeout(2000)
            detail_text = detail_page.locator("body").inner_text()
            return self.extract_detail_fields(detail_text)
        except Exception as exc:
            logger.warning("failed to fetch detail page", extra={"detail_url": detail_url, "error": str(exc)})
            return {"detail_url": detail_url}
        finally:
            detail_page.close()

    def extract_text(self, card: Locator, selectors: list[str]) -> str | None:
        for selector in selectors:
            try:
                value = card.locator(selector).first.inner_text(timeout=1500).strip()
                if value:
                    return self.clean_field(value)
            except Exception:
                continue
        return None

    def safe_inner_text(self, card: Locator) -> str:
        try:
            return card.inner_text(timeout=2000).strip()
        except Exception:
            return ""

    @staticmethod
    def clean_field(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" :\n\t")

    @classmethod
    def extract_detail_fields(cls, detail_text: str) -> dict:
        caption = cls.extract_block_value(detail_text, "Ad caption", ["Ad performance", "Interactive time analysis", "Recommended for you"])
        objective = cls.extract_single_value(detail_text, "Objective")
        industry = cls.extract_single_value(detail_text, "Industry")
        brand_name = cls.extract_single_value(detail_text, "Brand name")
        source = cls.extract_single_value(detail_text, "Source")
        region = cls.extract_single_value(detail_text, "Region")
        creative_type = cls.infer_creative_type(detail_text)

        payload = {
            "hook": caption,
            "game_name": cls.preferred_game_name(brand_name, industry),
            "creative_type": creative_type,
            "country": cls.normalize_region(region),
            "source": source,
            "detail_text": detail_text,
            "objective": objective,
            "industry": industry,
            "brand_name": brand_name,
        }
        return {key: value for key, value in payload.items() if value not in (None, "", "-")}

    @classmethod
    def extract_single_value(cls, text: str, label: str) -> str | None:
        lines = [line.strip() for line in text.splitlines()]
        for index, line in enumerate(lines):
            if line.strip().lower() == label.lower():
                for next_line in lines[index + 1 :]:
                    candidate = cls.clean_field(next_line)
                    if candidate:
                        return candidate
                return None
        return None

    @classmethod
    def extract_block_value(cls, text: str, label: str, stop_labels: list[str]) -> str | None:
        lines = [line.rstrip() for line in text.splitlines()]
        for index, line in enumerate(lines):
            if line.strip().lower() != label.lower():
                continue
            values: list[str] = []
            for next_line in lines[index + 1 :]:
                candidate = cls.clean_field(next_line)
                if not candidate:
                    continue
                if any(candidate.lower() == stop_label.lower() for stop_label in stop_labels):
                    break
                values.append(candidate)
            if values:
                return " ".join(values)
            return None
        return None

    @classmethod
    def normalize_region(cls, region: str | None) -> str | None:
        if not region:
            return None
        normalized = cls.clean_field(region)
        if normalized.lower().startswith("view all"):
            return "MULTI"
        return normalized.upper()

    @classmethod
    def preferred_game_name(cls, brand_name: str | None, industry: str | None) -> str | None:
        cleaned_brand = cls.clean_field(brand_name) if brand_name else None
        if cleaned_brand and cleaned_brand != "-":
            return cleaned_brand
        cleaned_industry = cls.clean_field(industry) if industry else None
        return cleaned_industry

    @classmethod
    def extract_hook_from_text(cls, text: str) -> str | None:
        lines = [cls.clean_field(line) for line in text.splitlines() if cls.clean_field(line)]
        ignored_prefixes = ("country", "first seen", "last seen", "region", "advertiser", "language")
        for line in lines:
            lowered = line.lower()
            if lowered.startswith(ignored_prefixes):
                continue
            if len(line) >= 12 and "202" not in line and not re.fullmatch(r"[A-Z]{2}", line):
                return line
        return None

    @classmethod
    def extract_game_name_from_text(cls, text: str) -> str | None:
        patterns = [
            r"App(?:lication)?\s*[:\-]\s*(.+)",
            r"Game\s*[:\-]\s*(.+)",
            r"Advertiser\s*[:\-]\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return cls.clean_field(match.group(1))

        lines = [cls.clean_field(line) for line in text.splitlines() if cls.clean_field(line)]
        if len(lines) >= 2:
            return lines[1]
        return None

    @classmethod
    def extract_country_from_text(cls, text: str) -> str | None:
        patterns = [
            r"Country\s*[:\-]\s*([A-Za-z]{2,})",
            r"Region\s*[:\-]\s*([A-Za-z]{2,})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return cls.clean_field(match.group(1)).upper()
        return None

    @classmethod
    def extract_date_from_text(cls, text: str, label: str) -> str | None:
        pattern = rf"{label}\s+seen\s*[:\-]\s*([0-9]{{4}}[-/][0-9]{{2}}[-/][0-9]{{2}}(?:\s+[0-9]{{2}}:[0-9]{{2}}(?::[0-9]{{2}})?)?)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return cls.clean_field(match.group(1)).replace("/", "-")
        return None

    @staticmethod
    def infer_creative_type(text: str) -> str:
        lowered = text.lower()
        if "video" in lowered:
            return "video"
        if "image" in lowered:
            return "image"
        if "carousel" in lowered:
            return "carousel"
        return "unknown"
