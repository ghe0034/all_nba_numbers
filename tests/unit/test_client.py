import json

import pytest
from tenacity import wait_none

from nba_ingest import client
from nba_ingest.catalog import EndpointDefinition
from nba_ingest.client import NbaApiError, fetch_endpoint
from nba_ingest.headers import DEFAULT_USER_AGENT

ENDPOINT = EndpointDefinition(
    id="demo",
    url="https://stats.nba.com/stats/demo",
    season_param_name="Season",
    fixed_params={"LeagueID": "00"},
)
VALID_BODY = b'{ "resultSets" : [] }\n'


class FakeResponse:
    def __init__(self, status_code, content=b""):
        self.status_code = status_code
        self.content = content


class FakeSession:
    """Sesión falsa: devuelve respuestas predefinidas y registra las llamadas."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *args, **kwargs):
        call_record = {"url": url}
        call_record.update(kwargs)
        self.calls.append(call_record)
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def without_backoff_waits(monkeypatch):
    """Quita las esperas exponenciales de tenacity para que los tests sean instantáneos."""
    monkeypatch.setattr(client, "_get_once", client._get_once.retry_with(wait=wait_none()))


def test_returns_raw_bytes_unchanged_on_200():
    session = FakeSession([FakeResponse(200, VALID_BODY)])

    assert fetch_endpoint(ENDPOINT, "2025-26", session=session) == VALID_BODY


def test_request_sends_fixed_and_season_params_headers_and_timeout():
    session = FakeSession([FakeResponse(200, VALID_BODY)])

    fetch_endpoint(ENDPOINT, "2025-26", session=session)

    call = session.calls[0]
    assert call["url"] == "https://stats.nba.com/stats/demo"
    assert call["params"] == {"LeagueID": "00", "Season": "2025-26"}
    assert call["headers"]["User-Agent"] == DEFAULT_USER_AGENT
    assert call["timeout"] is not None


def test_user_agent_override_reaches_request_headers():
    session = FakeSession([FakeResponse(200, VALID_BODY)])

    fetch_endpoint(ENDPOINT, "2025-26", session=session, user_agent="agente/1.0")

    assert session.calls[0]["headers"]["User-Agent"] == "agente/1.0"


@pytest.mark.parametrize("status", [403, 429, 503])
def test_retryable_status_is_retried_then_succeeds(status):
    session = FakeSession([FakeResponse(status), FakeResponse(200, VALID_BODY)])

    body = fetch_endpoint(ENDPOINT, "2025-26", session=session)

    assert body == VALID_BODY
    assert len(session.calls) == 2


def test_non_retryable_status_raises_immediately():
    session = FakeSession([FakeResponse(404)])

    with pytest.raises(NbaApiError, match="404"):
        fetch_endpoint(ENDPOINT, "2025-26", session=session)

    assert len(session.calls) == 1


def test_raises_after_max_attempts_exhausted():
    session = FakeSession([FakeResponse(503)] * client.MAX_ATTEMPTS)

    with pytest.raises(NbaApiError, match="503"):
        fetch_endpoint(ENDPOINT, "2025-26", session=session)

    assert len(session.calls) == client.MAX_ATTEMPTS


def test_invalid_json_body_raises_decode_error():
    session = FakeSession([FakeResponse(200, b"<html>blocked</html>")])

    with pytest.raises(json.JSONDecodeError):
        fetch_endpoint(ENDPOINT, "2025-26", session=session)
