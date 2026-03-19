from scraper.tiktok_scraper import TikTokCreativeCenterScraper


def test_tiktok_text_extractors_parse_structured_fallback_text() -> None:
    sample_text = """
    Win free rewards now
    Whiteout Survival
    Country: US
    First seen: 2026-03-01 10:00:00
    Last seen: 2026-03-05 12:30:00
    Video
    """

    assert TikTokCreativeCenterScraper.extract_hook_from_text(sample_text) == "Win free rewards now"
    assert TikTokCreativeCenterScraper.extract_game_name_from_text(sample_text) == "Whiteout Survival"
    assert TikTokCreativeCenterScraper.extract_country_from_text(sample_text) == "US"
    assert TikTokCreativeCenterScraper.extract_date_from_text(sample_text, "first") == "2026-03-01 10:00:00"
    assert TikTokCreativeCenterScraper.extract_date_from_text(sample_text, "last") == "2026-03-05 12:30:00"
    assert TikTokCreativeCenterScraper.infer_creative_type(sample_text) == "video"


def test_tiktok_builds_search_url_with_keyword() -> None:
    scraper = TikTokCreativeCenterScraper()

    url = scraper.build_search_url("Whiteout Survival")

    assert "keyword=Whiteout+Survival" in url


def test_tiktok_extracts_fields_from_detail_text() -> None:
    detail_text = """
    Source: Others
    About this ad
    Region
    View all (81)
    Industry
    Skincare
    Objective
    Video Views
    Brand name
    -
    Landing Page
    -
    Ad caption
    韓国薬局でゲットしたい 肌のトラブルケアにおすすめ
    #pcalm #韓国コスメ
    Ad performance
    Likes
    749
    """

    payload = TikTokCreativeCenterScraper.extract_detail_fields(detail_text)

    assert payload["hook"] == "韓国薬局でゲットしたい 肌のトラブルケアにおすすめ #pcalm #韓国コスメ"
    assert payload["game_name"] == "Skincare"
    assert payload["industry"] == "Skincare"
    assert payload["objective"] == "Video Views"
    assert payload["country"] == "MULTI"
    assert payload["creative_type"] == "video"
