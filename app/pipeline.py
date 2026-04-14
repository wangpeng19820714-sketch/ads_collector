from __future__ import annotations

import logging
from dataclasses import dataclass

from analyzer.hook_classifier import HookClassifier
from parser.parser import AdParser, ParsedAd

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineResult:
    scraped: int
    parsed: int
    inserted: int
    updated: int
    failed: int


class AdsCollectionPipeline:
    def __init__(self, scraper, storage, parser: AdParser | None = None, classifier: HookClassifier | None = None) -> None:
        self.scraper = scraper
        self.storage = storage
        self.parser = parser or AdParser()
        self.classifier = classifier or HookClassifier()

    def run(self, game_name: str | None = None) -> PipelineResult:
        self.storage.init_schema()
        raw_records = self.scraper.scrape(game_name=game_name)
        expected_game_name = self._normalize_name(game_name)

        parsed_records: list[ParsedAd] = []
        failed = 0
        for raw in raw_records:
            try:
                parsed = self.parser.parse(raw)
                parsed_records.append(parsed)
            except Exception as exc:
                failed += 1
                logger.exception("failed to parse ad record", extra={"platform": raw.platform, "error": str(exc)})

        inserted = 0
        updated = 0
        for ad in parsed_records:
            normalized_ad_name = self._normalize_name(ad.game_name)
            if expected_game_name and normalized_ad_name != expected_game_name:
                logger.info(
                    "skipped ad due to exact game-name mismatch",
                    extra={
                        "platform": ad.platform,
                        "expected_game_name": game_name,
                        "parsed_game_name": ad.game_name,
                    },
                )
                continue
            hook_type = self.classifier.classify(ad)
            logger.info(
                "parsed ad",
                extra={
                    "platform": ad.platform,
                    "game_name": ad.game_name,
                    "country": ad.country,
                    "hook_type": hook_type,
                },
            )
            is_new = self.storage.upsert_ad(ad)
            if is_new:
                inserted += 1
            else:
                updated += 1

        return PipelineResult(
            scraped=len(raw_records),
            parsed=len(parsed_records),
            inserted=inserted,
            updated=updated,
            failed=failed,
        )

    @staticmethod
    def _normalize_name(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split()).strip().casefold()
        return normalized or None

