import json
from datetime import date

import pytest
from tenacity import wait_none

from nba_ingest import client
from nba_ingest.catalog import EndpointDefinition
from nba_ingest.client import NbaApiError, build_request_params, fetch_endpoint
from nba_ingest.date_range import DateRange

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
    monkeypatch.setattr(
        client, "_get_once", client._get_once.retry_with(wait=wait_none())
    )


def test_returns_raw_bytes_unchanged_on_200():
    session = FakeSession([FakeResponse(200, VALID_BODY)])

    assert fetch_endpoint(ENDPOINT, "2025-26", session=session) == VALID_BODY


def test_request_sends_fixed_and_season_params_headers_and_timeout():
    session = FakeSession([FakeResponse(200, VALID_BODY)])

    fetch_endpoint(ENDPOINT, "2025-26", session=session)

    call = session.calls[0]
    assert call["url"] == "https://stats.nba.com/stats/demo"
    assert call["params"] == {"LeagueID": "00", "Season": "2025-26"}
    assert call["headers"]["Referer"].startswith("https://www.nba.com")
    assert call["impersonate"] == "chrome"
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


DATE_RANGE = DateRange(date(2024, 1, 8), date(2024, 1, 14))


def test_build_request_params_adds_nba_formatted_date_range():
    params = build_request_params(ENDPOINT, "2023-24", DATE_RANGE)

    assert params == {
        "LeagueID": "00",
        "Season": "2023-24",
        "DateFrom": "01/08/2024",
        "DateTo": "01/14/2024",
    }


def test_date_range_overrides_empty_date_params_from_fixed_params():
    endpoint = EndpointDefinition(
        id="demo",
        url="https://stats.nba.com/stats/demo",
        season_param_name="Season",
        fixed_params={"DateFrom": "", "DateTo": ""},
    )

    params = build_request_params(endpoint, "2023-24", DATE_RANGE)

    assert params["DateFrom"] == "01/08/2024"
    assert params["DateTo"] == "01/14/2024"


def test_build_request_params_without_range_sends_no_date_params():
    assert build_request_params(ENDPOINT, "2023-24") == {
        "LeagueID": "00",
        "Season": "2023-24",
    }


def test_fetch_endpoint_sends_date_range_to_api():
    session = FakeSession([FakeResponse(200, VALID_BODY)])

    fetch_endpoint(ENDPOINT, "2023-24", session=session, date_range=DATE_RANGE)

    assert session.calls[0]["params"]["DateFrom"] == "01/08/2024"
    assert session.calls[0]["params"]["DateTo"] == "01/14/2024"
