from datetime import datetime

from parser.parser import AdParser
from scraper.playwright_scraper import RawAdRecord


def test_parser_normalizes_payload_record() -> None:
    parser = AdParser()
    raw = RawAdRecord(
        platform="tiktok",
        payload={
            "game_name": "Test Game",
            "hook": "Win free rewards now",
            "creative_type": "video",
            "country": "us",
            "first_seen": "2026-03-01 10:00:00",
            "last_seen": "2026-03-05 10:00:00",
        },
    )

    parsed = parser.parse(raw)

    assert parsed.platform == "tiktok"
    assert parsed.country == "US"
    assert parsed.first_seen == datetime(2026, 3, 1, 10, 0, 0)


def test_parser_raises_for_missing_hook() -> None:
    parser = AdParser()
    raw = RawAdRecord(platform="facebook", payload={"game_name": "Test Game"})

    try:
        parser.parse(raw)
    except ValueError as exc:
        assert "hook is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing hook")

