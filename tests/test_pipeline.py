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
    assert result.inserted == 2
    assert result.updated == 0
    assert result.failed == 0
    assert len(storage.list_ads()) == 2
