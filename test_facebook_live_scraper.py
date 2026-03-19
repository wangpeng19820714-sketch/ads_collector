from scraper.facebook_scraper import FacebookAdsLibraryScraper


def test_facebook_listing_parser_extracts_basic_fields() -> None:
    text = """
    约12,000条结果
    已停止
    资料库编号：1881097159349902
    2025年5月28日 - 2025年9月8日
    平台
    查看广告详情
    Whiteout Survival
    赞助内容
    Face extreme cold after the apocalypse buries the world
    抱歉，播放视频时出错了。
    详细了解
    """

    scraper = FacebookAdsLibraryScraper()
    records = scraper.parse_listing_text(text, game_name="Whiteout Survival")

    assert len(records) == 1
    payload = records[0].payload
    assert payload["game_name"] == "Whiteout Survival"
    assert payload["hook"] == "Face extreme cold after the apocalypse buries the world"
    assert payload["creative_type"] == "video"
    assert payload["first_seen"] == "2025-05-28"
    assert payload["last_seen"] == "2025-09-08"
    assert "facebook.com/ads/library/" in payload["detail_url"]


def test_facebook_builds_search_url() -> None:
    scraper = FacebookAdsLibraryScraper()

    url = scraper.build_search_url("Whiteout Survival")

    assert "q=Whiteout+Survival" in url
