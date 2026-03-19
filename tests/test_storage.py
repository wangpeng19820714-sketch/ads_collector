from datetime import datetime

from parser.parser import ParsedAd
from storage.db import InMemoryStorage


def build_ad(hook: str, last_seen_day: int) -> ParsedAd:
    return ParsedAd(
        platform="tiktok",
        game_name="Test Game",
        hook=hook,
        creative_type="video",
        country="US",
        first_seen=datetime(2026, 3, 1, 0, 0, 0),
        last_seen=datetime(2026, 3, last_seen_day, 0, 0, 0),
    )


def test_in_memory_storage_deduplicates_by_hook_and_platform() -> None:
    storage = InMemoryStorage()
    storage.init_schema()

    first_insert = storage.upsert_ad(build_ad("same hook", 3))
    second_insert = storage.upsert_ad(build_ad("same hook", 5))

    assert first_insert is True
    assert second_insert is False
    assert len(storage.list_ads()) == 1
    assert storage.list_ads()[0].last_seen == datetime(2026, 3, 5, 0, 0, 0)

