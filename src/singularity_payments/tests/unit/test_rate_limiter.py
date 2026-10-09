import pytest

from singularity_payments.utils.errors import MpesaRateLimitError
from singularity_payments.utils.ratelimiter import RateLimiter, RateLimiterOptions


@pytest.fixture
def make_limiter():
    """
    Factory fixture that builds in-memory rate limiters and destroys them
    (cancelling their background tasks) after each test.
    """
    created = []

    def _make(max_requests: int = 1, window_ms: int = 1000, key_prefix=None):
        rate_limiter = RateLimiter(
            options=RateLimiterOptions(
                max_requests=max_requests,
                window_ms=window_ms,
                key_prefix=key_prefix,
            )
        )
        created.append(rate_limiter)
        return rate_limiter

    yield _make

    for rate_limiter in created:
        rate_limiter.destroy()


@pytest.mark.asyncio
async def test_allow_requests_within_limit(make_limiter):
    """Requests up to the limit are allowed."""
    limiter = make_limiter(max_requests=3, window_ms=1000)
    for _ in range(3):
        assert await limiter.check_limit("test") is None


@pytest.mark.asyncio
async def test_raise_when_limit_exceeded(make_limiter):
    """The request that goes over the limit raises MpesaRateLimitError."""
    limiter = make_limiter(max_requests=2, window_ms=1000)
    await limiter.check_limit("test")
    await limiter.check_limit("test")
    with pytest.raises(MpesaRateLimitError):
        await limiter.check_limit("test")


@pytest.mark.asyncio
async def test_reset_window_after_expiry(make_limiter, monkeypatch):
    """After the time window elapses, the counter resets and requests are allowed again."""
    # Freeze time so the test is deterministic (no real sleeping).
    now = [1_000.0]
    monkeypatch.setattr(
        "singularity_payments.utils.ratelimiter.time.time", lambda: now[0]
    )

    limiter = make_limiter(max_requests=1, window_ms=1000)

    # First request within the window is allowed.
    await limiter.check_limit("test")

    # Second request is blocked because the limit (1) is reached.
    with pytest.raises(MpesaRateLimitError):
        await limiter.check_limit("test")

    # Advance past the window (window_ms=1000 => 1 second).
    now[0] += 1.001

    # The window has expired, so the key is allowed again.
    await limiter.check_limit("test")


@pytest.mark.asyncio
async def test_track_usage(make_limiter):
    """get_usage reports the number of requests made and the number remaining."""
    limiter = make_limiter(max_requests=5, window_ms=1000)
    await limiter.check_limit("test")
    await limiter.check_limit("test")

    usage = limiter.get_usage("test")
    assert usage.count == 2
    assert usage.remaining == 3


@pytest.mark.asyncio
async def test_handles_keys_independently(make_limiter):
    """Each key keeps its own counter."""
    limiter = make_limiter(max_requests=1, window_ms=1000)
    await limiter.check_limit("key1")
    await limiter.check_limit("key2")

    assert limiter.get_usage("key1").count == 1
    assert limiter.get_usage("key2").count == 1


@pytest.mark.asyncio
async def test_reset_specific_key(make_limiter):
    """Resetting one key clears only that key's counter."""
    limiter = make_limiter(max_requests=1, window_ms=1000)
    await limiter.check_limit("test")
    limiter.reset("test")

    # Allowed again because the counter was cleared.
    assert await limiter.check_limit("test") is None


@pytest.mark.asyncio
async def test_reset_all_keys(make_limiter):
    """reset_all clears every key's counter."""
    limiter = make_limiter(max_requests=1, window_ms=1000)
    await limiter.check_limit("key1")
    await limiter.check_limit("key2")

    limiter.reset_all()

    assert await limiter.check_limit("key1") is None
    assert await limiter.check_limit("key2") is None
