import random

import pytest

from nba_ingest.retry import compute_delay_seconds, parse_retry_after, should_retry

BASE = 2.0
CAP = 30.0


@pytest.mark.parametrize("status", [429, 403, 500, 502, 503])
def test_retryable_statuses_retry_while_attempts_remain(status):
    assert should_retry(status, attempt=1, max_attempts=5)


@pytest.mark.parametrize("status", [200, 404, 400])
def test_non_retryable_statuses_do_not_retry(status):
    assert not should_retry(status, attempt=1, max_attempts=5)


def test_no_retry_when_attempts_exhausted():
    assert not should_retry(429, attempt=5, max_attempts=5)


class NoJitterRng:
    """RNG stub que devuelve siempre el extremo inferior: jitter = 0."""

    def uniform(self, low: float, high: float) -> float:
        return low


def test_delay_grows_exponentially_without_jitter():
    rng = NoJitterRng()

    delays = [compute_delay_seconds(attempt, BASE, CAP, rng=rng) for attempt in (1, 2, 3)]

    assert delays == [2.0, 4.0, 8.0]


def test_delay_never_exceeds_cap():
    rng = random.Random(42)

    delays = [compute_delay_seconds(attempt, BASE, CAP, rng=rng) for attempt in range(1, 30)]

    assert max(delays) <= CAP


def test_delay_is_never_negative():
    rng = random.Random(7)

    delays = [compute_delay_seconds(attempt, BASE, CAP, rng=rng) for attempt in range(1, 30)]

    assert min(delays) >= 0


def test_retry_after_seconds_is_parsed():
    assert parse_retry_after("12") == 12.0


def test_retry_after_missing_or_unparseable_returns_none():
    assert parse_retry_after(None) is None
    assert parse_retry_after("Wed, 21 Oct 2026 07:28:00 GMT") is None


def test_retry_after_takes_priority_over_computed_delay_but_respects_cap():
    delay = compute_delay_seconds(1, BASE, CAP, rng=random.Random(0), retry_after=500.0)

    assert delay == CAP


def test_retry_after_is_used_when_present():
    delay = compute_delay_seconds(1, BASE, CAP, rng=random.Random(0), retry_after=7.0)

    assert delay == 7.0
