from app.pipeline import AdsCollectionPipeline
from scraper.playwright_scraper import MockScraper
from storage.db import InMemoryStorage


def test_pipeline_runs_end_to_end() -> None:
    scraper = MockScraper(platform="tiktok")
    storage = InMemoryStorage()
    pipeline = AdsCollectionPipeline(scraper=scraper, storage=storage)

    result = pipeline.run(game_name="Whiteout Survival")

    assert result.scraped >= 2
    assert result.parsed == result.scraped
    assert result.inserted == 1
    assert result.updated == 0
    assert result.failed == 0
    assert len(storage.list_ads()) == 1
    assert storage.list_ads()[0].game_name == "Whiteout Survival"


def test_pipeline_requires_exact_game_name_match_case_insensitive() -> None:
    scraper = MockScraper(
        platform="facebook",
        records=[
            {
                "game_name": "travel town",
                "hook": "exact lowercase match",
                "creative_type": "video",
                "country": "US",
                "first_seen": "2026-03-01 12:00:00",
                "last_seen": "2026-03-07 12:00:00",
            },
            {
                "game_name": "Travel Town - Merge Adventure",
                "hook": "partial extra suffix should be rejected",
                "creative_type": "video",
                "country": "US",
                "first_seen": "2026-03-01 12:00:00",
                "last_seen": "2026-03-07 12:00:00",
            },
        ],
    )
    storage = InMemoryStorage()
    pipeline = AdsCollectionPipeline(scraper=scraper, storage=storage)

    result = pipeline.run(game_name="Travel Town")

    assert result.scraped == 2
    assert result.parsed == 2
    assert result.inserted == 1
    assert result.updated == 0
    assert result.failed == 0
    assert len(storage.list_ads()) == 1
    assert storage.list_ads()[0].game_name == "travel town"
