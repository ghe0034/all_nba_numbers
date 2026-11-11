from nba_ingest.headers import DEFAULT_USER_AGENT, build_headers


def test_headers_include_user_agent_and_referer_and_origin():
    headers = build_headers()

    assert headers["User-Agent"] == DEFAULT_USER_AGENT
    assert headers["Referer"].startswith("https://www.nba.com")
    assert headers["Origin"].startswith("https://www.nba.com")


def test_headers_include_nba_stats_api_headers():
    headers = build_headers()

    assert headers["x-nba-stats-origin"] == "stats"
    assert headers["x-nba-stats-token"] == "true"


def test_user_agent_can_be_overridden():
    headers = build_headers(user_agent="custom-agent/1.0")

    assert headers["User-Agent"] == "custom-agent/1.0"


def test_blank_user_agent_falls_back_to_default():
    assert build_headers(user_agent="  ")["User-Agent"] == DEFAULT_USER_AGENT
