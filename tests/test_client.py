import json

import pytest

from nba_ingest.catalog import EndpointDefinition
from nba_ingest.client import NbaApiError, fetch_endpoint
from nba_ingest.headers import DEFAULT_USER_AGENT

ENDPOINT = EndpointDefinition(
    id="demo",
    path="/stats/demo",
    season_param_name="Season",
    fixed_params={"LeagueID": "00"},
)
VALID_BODY = b'{ "resultSets" : [] }\n'


class FakeResponse:
    def __init__(self, status_code, content=b"", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


class FakeSession:
    """Sesión falsa que devuelve respuestas predefinidas y registra las llamadas."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        return self.responses.pop(0)


class NoJitterRng:
    def uniform(self, low, high):
        return low


def fetch(session, acquire_slot=lambda: None, sleep=lambda seconds: None, **overrides):
    options = {
        "session": session,
        "acquire_slot": acquire_slot,
        "sleep": sleep,
        "rng": NoJitterRng(),
        "max_attempts": 3,
        "base_delay": 1.0,
        "max_delay": 10.0,
    }
    options.update(overrides)
    return fetch_endpoint(ENDPOINT, "2025-26", **options)


def test_returns_raw_bytes_unchanged_on_200():
    session = FakeSession([FakeResponse(200, VALID_BODY)])

    body = fetch(session)

    assert body == VALID_BODY


def test_request_sends_fixed_and_season_params_with_headers_and_timeout():
    session = FakeSession([FakeResponse(200, VALID_BODY)])

    fetch(session)

    call = session.calls[0]
    assert call["url"] == "https://stats.nba.com/stats/demo"
    assert call["params"] == {"LeagueID": "00", "Season": "2025-26"}
    assert call["headers"]["User-Agent"] == DEFAULT_USER_AGENT
    assert call["timeout"] is not None


def test_acquire_slot_runs_before_every_attempt():
    events = []
    session = FakeSession([FakeResponse(429), FakeResponse(200, VALID_BODY)])

    fetch(
        session,
        acquire_slot=lambda: events.append("acquire"),
        sleep=lambda seconds: events.append("sleep"),
    )

    assert events == ["acquire", "sleep", "acquire"]


def test_retries_429_then_succeeds():
    slept = []
    session = FakeSession([FakeResponse(429), FakeResponse(200, VALID_BODY)])

    body = fetch(session, sleep=slept.append)

    assert body == VALID_BODY
    assert len(session.calls) == 2
    assert slept == [1.0]


def test_non_retryable_status_raises_immediately():
    session = FakeSession([FakeResponse(404)])

    with pytest.raises(NbaApiError, match="404"):
        fetch(session)

    assert len(session.calls) == 1


def test_raises_after_max_attempts_exhausted():
    session = FakeSession([FakeResponse(503), FakeResponse(503), FakeResponse(503)])

    with pytest.raises(NbaApiError, match="3 intento"):
        fetch(session, max_attempts=3)

    assert len(session.calls) == 3


def test_invalid_json_body_raises_decode_error():
    session = FakeSession([FakeResponse(200, b"<html>blocked</html>")])

    with pytest.raises(json.JSONDecodeError):
        fetch(session)


def test_retry_after_header_is_honoured():
    slept = []
    session = FakeSession(
        [FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse(200, VALID_BODY)]
    )

    fetch(session, sleep=slept.append)

    assert slept == [7.0]
