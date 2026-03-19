from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from scraper.playwright_scraper import RawAdRecord

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ParsedAd:
    platform: str
    game_name: str
    hook: str
    creative_type: str
    country: str
    first_seen: datetime | None
    last_seen: datetime | None
    material_url: str | None = None
    library_id: str | None = None

    def dedup_key(self) -> tuple[str, str]:
        return self.platform.lower(), self.hook.strip().lower()


class AdParser:
    """Converts raw scraper payloads into the normalized ad model."""

    def parse(self, raw_record: RawAdRecord) -> ParsedAd:
        payload = raw_record.payload
        if "raw_text" in payload:
            return self._parse_from_text(raw_record.platform, payload["raw_text"])

        hook = self._require_non_empty(payload.get("hook"), "hook")
        game_name = self._require_non_empty(payload.get("game_name"), "game_name")
        creative_type = payload.get("creative_type", "unknown").strip() or "unknown"
        country = self._normalize_country(payload.get("country"))
        first_seen = self._parse_datetime(payload.get("first_seen"))
        last_seen = self._parse_datetime(payload.get("last_seen"))

        return ParsedAd(
            platform=raw_record.platform,
            game_name=game_name,
            hook=hook,
            creative_type=creative_type,
            country=country,
            first_seen=first_seen,
            last_seen=last_seen,
            material_url=self._optional_text(payload.get("material_url") or payload.get("detail_url")),
            library_id=self._optional_text(payload.get("library_id")),
        )

    def _parse_from_text(self, platform: str, raw_text: str) -> ParsedAd:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        hook = lines[0] if lines else "unknown hook"
        game_name = lines[1] if len(lines) > 1 else "unknown game"
        logger.warning("fallback text parser used", extra={"platform": platform})
        return ParsedAd(
            platform=platform,
            game_name=game_name,
            hook=hook,
            creative_type="unknown",
            country="UNKNOWN",
            first_seen=None,
            last_seen=None,
        )

    @staticmethod
    def _require_non_empty(value: str | None, field_name: str) -> str:
        if value is None or not str(value).strip():
            raise ValueError(f"{field_name} is required")
        return str(value).strip()

    @staticmethod
    def _optional_text(value: str | None) -> str | None:
        if value is None or not str(value).strip():
            return None
        return str(value).strip()

    @staticmethod
    def _normalize_country(value: str | None) -> str:
        if value is None or not str(value).strip():
            return "UNKNOWN"
        return str(value).strip().upper()

    @staticmethod
    def _parse_datetime(value: str | datetime | None) -> datetime | None:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value

        normalized = str(value).strip().replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
        logger.warning("failed to parse datetime", extra={"value": value})
        return None
