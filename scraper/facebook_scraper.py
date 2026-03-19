from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from scraper.playwright_scraper import BaseScraper, RawAdRecord

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - dependency may be absent in tests
    sync_playwright = None

logger = logging.getLogger(__name__)


class FacebookAdsLibraryScraper(BaseScraper):
    def __init__(
        self,
        start_url: str = "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&is_targeted_country=false&media_type=all&search_type=keyword_unordered",
        max_scroll: int = 5,
        delay_seconds: int = 2,
        headless: bool = True,
        timeout_ms: int = 60000,
        max_cards: int = 50,
    ) -> None:
        self.platform = "facebook"
        self.start_url = start_url
        self.max_scroll = max_scroll
        self.delay_seconds = delay_seconds
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.max_cards = max_cards

    def scrape(self, game_name: str | None = None) -> list[RawAdRecord]:
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed. Run `pip install -r requirements.txt` first.")

        target_url = self.build_search_url(game_name)
        logger.info("facebook scrape started", extra={"game_name": game_name, "url": target_url})

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context(
                locale="zh-CN",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                self.scroll_page(page)
                body_text = page.locator("body").inner_text()
                records = self.parse_listing_text(body_text, game_name=game_name)
                logger.info("facebook scrape completed", extra={"records": len(records), "game_name": game_name})
                return records
            finally:
                context.close()
                browser.close()

    def build_search_url(self, game_name: str | None) -> str:
        if not game_name:
            return self.start_url
        separator = "&" if "?" in self.start_url else "?"
        return f"{self.start_url}{separator}q={quote_plus(game_name)}"

    def scroll_page(self, page) -> None:
        for _ in range(self.max_scroll):
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(self.delay_seconds * 1000)

    def parse_listing_text(self, text: str, game_name: str | None = None) -> list[RawAdRecord]:
        normalized = text.replace("\u200b", "")
        chunks = re.split(r"(?=资料库编号[:：]\s*\d+)", normalized)
        records: list[RawAdRecord] = []
        for chunk in chunks:
            payload = self.extract_ad_payload(chunk, fallback_game_name=game_name)
            if payload is None:
                continue
            records.append(RawAdRecord(platform=self.platform, payload=payload))
            if len(records) >= self.max_cards:
                break
        return records

    def extract_ad_payload(self, chunk: str, fallback_game_name: str | None = None) -> dict | None:
        lines = [self.clean_field(line) for line in chunk.splitlines()]
        lines = [line for line in lines if line]
        if not lines or not any("资料库编号" in line for line in lines):
            return None

        library_id = self.find_pattern(chunk, r"资料库编号[:：]\s*(\d+)")
        date_line = self.find_pattern(chunk, r"((?:\d{4}年\d{1,2}月\d{1,2}日(?:\s*开始投放)?)(?:\s*-\s*\d{4}年\d{1,2}月\d{1,2}日)?)")
        status = self.first_matching_line(lines, ("投放中", "已停止"))
        brand = self.extract_brand_name(lines, fallback_game_name)
        hook = self.extract_hook(lines, brand or fallback_game_name)
        country = self.extract_country(chunk)
        creative_type = self.infer_creative_type(lines)

        if not hook:
            return None

        payload = {
            "library_id": library_id,
            "game_name": brand or fallback_game_name or "unknown game",
            "hook": hook,
            "creative_type": creative_type,
            "country": country or "ALL",
            "first_seen": self.extract_first_seen(date_line),
            "last_seen": self.extract_last_seen(date_line),
            "status": status,
            "detail_url": self.build_detail_url(library_id),
            "source_text": "\n".join(lines),
        }
        return payload

    @staticmethod
    def clean_field(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" :\n\t\r")

    @staticmethod
    def find_pattern(text: str, pattern: str) -> str | None:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def first_matching_line(lines: list[str], candidates: tuple[str, ...]) -> str | None:
        for line in lines:
            if line in candidates:
                return line
        return None

    def extract_brand_name(self, lines: list[str], fallback_game_name: str | None) -> str | None:
        for index, line in enumerate(lines):
            if line in {"查看摘要详情", "查看广告详情"}:
                for candidate in lines[index + 1 :]:
                    if candidate in {"赞助内容", "详细了解", "立即安装", "玩游戏", "平台", "打开下拉菜单"}:
                        continue
                    if "资料库编号" in candidate or "广告使用这个创意和文字" in candidate or "这条广告有多种版本" in candidate:
                        continue
                    if self.looks_like_date(candidate) or candidate in {"投放中", "已停止"}:
                        continue
                    return candidate
        if fallback_game_name:
            return fallback_game_name
        return None

    def extract_hook(self, lines: list[str], brand_name: str | None) -> str | None:
        skip_exact = {
            "赞助内容",
            "详细了解",
            "立即安装",
            "玩游戏",
            "平台",
            "打开下拉菜单",
            "查看摘要详情",
            "查看广告详情",
            "欧盟境内广告信息公示",
        }
        for line in lines:
            if line in skip_exact:
                continue
            if "资料库编号" in line or "条广告使用这个创意和文字" in line or "这条广告有多种版本" in line:
                continue
            if self.looks_like_date(line):
                continue
            if line in {"投放中", "已停止"}:
                continue
            if brand_name and line == brand_name:
                continue
            if re.fullmatch(r"0:\d{2}\s*/\s*\d+:\d{2}", line):
                continue
            if len(line) >= 12:
                return line
        return None

    @staticmethod
    def extract_country(text: str) -> str | None:
        match = re.search(r"country=([A-Z]{2,}|ALL)", text)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def infer_creative_type(lines: list[str]) -> str:
        text = " ".join(lines).lower()
        if "播放视频" in text or re.search(r"0:\d{2}\s*/\s*\d+:\d{2}", " ".join(lines)):
            return "video"
        if "carousel" in text:
            return "carousel"
        if "image" in text:
            return "image"
        return "unknown"

    @staticmethod
    def build_detail_url(library_id: str | None) -> str | None:
        if not library_id:
            return None
        return (
            "https://www.facebook.com/ads/library/"
            f"?active_status=active&ad_type=all&country=CN&id={library_id}"
            "&is_targeted_country=false&media_type=all&search_type=page"
        )

    @staticmethod
    def looks_like_date(value: str) -> bool:
        return bool(re.search(r"\d{4}年\d{1,2}月\d{1,2}日", value))

    @staticmethod
    def normalize_date(value: str) -> str:
        numbers = re.findall(r"\d+", value)
        year, month, day = numbers[:3]
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

    def extract_first_seen(self, date_line: str | None) -> str | None:
        if not date_line:
            return None
        if "开始投放" in date_line:
            return self.normalize_date(date_line)
        first_part = date_line.split("-")[0].strip()
        return self.normalize_date(first_part)

    def extract_last_seen(self, date_line: str | None) -> str | None:
        if not date_line or "开始投放" in date_line:
            return None
        parts = [part.strip() for part in date_line.split("-")]
        if len(parts) >= 2:
            return self.normalize_date(parts[1])
        return None
