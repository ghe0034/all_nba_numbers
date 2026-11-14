from nba_ingest.headers import build_headers


def test_headers_include_referer_origin_and_accept():
    headers = build_headers()

    assert headers["Referer"].startswith("https://www.nba.com")
    assert headers["Origin"].startswith("https://www.nba.com")
    assert "application/json" in headers["Accept"]


def test_headers_leave_browser_fingerprint_to_impersonation():
    headers = build_headers()

    assert "User-Agent" not in headers
    assert not any(name.lower().startswith("sec-") for name in headers)


def test_user_agent_is_sent_only_when_overridden():
    headers = build_headers(user_agent="custom-agent/1.0")

    assert headers["User-Agent"] == "custom-agent/1.0"


def test_blank_user_agent_is_ignored():
    assert "User-Agent" not in build_headers(user_agent="  ")
