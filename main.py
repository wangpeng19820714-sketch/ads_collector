from __future__ import annotations

import argparse

from app.config import build_postgres_dsn, load_config
from app.logging_config import setup_logging
from app.pipeline import AdsCollectionPipeline
from scraper.facebook_scraper import FacebookAdsLibraryScraper
from scraper.playwright_scraper import MockScraper
from scraper.tiktok_scraper import TikTokCreativeCenterScraper
from storage.db import InMemoryStorage, PostgresStorage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ads Data Collector V1")
    parser.add_argument("--platform", default="tiktok", choices=["tiktok", "facebook"])
    parser.add_argument("--game-name", default=None)
    parser.add_argument("--storage", default="memory", choices=["memory", "postgres"])
    parser.add_argument("--scraper-mode", default="mock", choices=["mock", "live"])
    return parser.parse_args()


def build_scraper(args: argparse.Namespace, config: dict):
    if args.scraper_mode == "mock":
        return MockScraper(platform=args.platform)

    if args.platform == "tiktok":
        scrape_config = config.get("scrape", {})
        tiktok_config = config.get("tiktok", {})
        return TikTokCreativeCenterScraper(
            start_url=tiktok_config.get(
                "start_url",
                "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en",
            ),
            max_scroll=scrape_config.get("max_scroll", 10),
            delay_seconds=scrape_config.get("delay", 2),
            headless=scrape_config.get("headless", True),
            card_selectors=tiktok_config.get("card_selectors"),
            timeout_ms=scrape_config.get("timeout_ms", 60000),
        )

    if args.platform == "facebook":
        scrape_config = config.get("scrape", {})
        facebook_config = config.get("facebook", {})
        return FacebookAdsLibraryScraper(
            start_url=facebook_config.get(
                "start_url",
                "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&is_targeted_country=false&media_type=all&search_type=keyword_unordered",
            ),
            max_scroll=scrape_config.get("max_scroll", 5),
            delay_seconds=scrape_config.get("delay", 2),
            headless=scrape_config.get("headless", True),
            timeout_ms=scrape_config.get("timeout_ms", 60000),
        )

    raise NotImplementedError(f"Live scraper for platform `{args.platform}` is not implemented yet.")


def main() -> None:
    args = parse_args()
    config = load_config()
    setup_logging(
        level=config.get("logging", {}).get("level", "INFO"),
        log_file=config.get("logging", {}).get("file"),
    )

    scraper = build_scraper(args, config)
    if args.storage == "postgres":
        dsn = build_postgres_dsn(config["database"])
        storage = PostgresStorage(dsn)
    else:
        storage = InMemoryStorage()

    pipeline = AdsCollectionPipeline(scraper=scraper, storage=storage)
    result = pipeline.run(game_name=args.game_name)
    print(
        f"scraped={result.scraped} parsed={result.parsed} inserted={result.inserted} "
        f"updated={result.updated} failed={result.failed}"
    )


if __name__ == "__main__":
    main()
