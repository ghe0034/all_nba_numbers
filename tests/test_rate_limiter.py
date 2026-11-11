import pytest

from nba_ingest.rate_limiter import make_rate_limiter


class FakeClock:
    """Reloj controlado: `sleep` avanza el tiempo sin esperar de verdad."""

    def __init__(self):
        self.now = 1000.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_first_request_does_not_wait():
    clock = FakeClock()
    acquire = make_rate_limiter(2.0, clock=clock, sleep=clock.sleep)

    acquire()

    assert clock.sleeps == []


def test_request_right_after_previous_waits_full_interval():
    clock = FakeClock()
    acquire = make_rate_limiter(2.0, clock=clock, sleep=clock.sleep)

    acquire()
    acquire()

    assert clock.sleeps == [pytest.approx(2.0)]


def test_request_after_interval_has_elapsed_does_not_wait():
    clock = FakeClock()
    acquire = make_rate_limiter(2.0, clock=clock, sleep=clock.sleep)

    acquire()
    clock.now += 5.0
    acquire()

    assert clock.sleeps == []


def test_consecutive_requests_are_never_closer_than_interval():
    clock = FakeClock()
    acquire = make_rate_limiter(1.5, clock=clock, sleep=clock.sleep)
    request_times = []

    for _ in range(5):
        acquire()
        request_times.append(clock.now)

    gaps = [later - earlier for earlier, later in zip(request_times, request_times[1:])]
    assert all(gap >= 1.5 - 1e-9 for gap in gaps)


def test_negative_interval_is_rejected():
    with pytest.raises(ValueError):
        make_rate_limiter(-1.0)
