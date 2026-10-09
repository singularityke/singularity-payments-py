import pytest

from singularity_payments.utils.errors import MpesaNetworkError, MpesaRateLimitError
from singularity_payments.utils.retry import retry_with_backoff


@pytest.fixture
def fake_sleep(monkeypatch):
    """
    Replace the real backoff sleep with a recorder so tests run instantly.

    Returns:
        list: The delays (in milliseconds) that would have been slept.
    """
    delays = []

    async def _sleep(ms):
        delays.append(ms)

    monkeypatch.setattr("singularity_payments.utils.retry.sleep", _sleep)
    return delays


@pytest.mark.asyncio
async def test_succeed_on_first_attempt(fake_sleep):
    """A function that succeeds immediately is called exactly once."""
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        return "success"

    result = await retry_with_backoff(fn)

    assert result == "success"
    assert calls["n"] == 1
    assert fake_sleep == []


@pytest.mark.asyncio
async def test_retry_on_retryable_errors(fake_sleep):
    """A retryable error is retried and the function eventually succeeds."""
    error = MpesaNetworkError("Network error", True)
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise error
        return "success"

    result = await retry_with_backoff(fn, {"max_retries": 3})

    assert result == "success"
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_does_not_retry_on_non_retryable_errors(fake_sleep):
    """A non-retryable error is raised immediately without retrying."""
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        raise ValueError("Fatal error")

    with pytest.raises(ValueError):
        await retry_with_backoff(fn)

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_retry_up_to_max_retries(fake_sleep):
    """An always-failing retryable error is retried up to the limit, then raised."""
    error = MpesaNetworkError("Network error", True)
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        raise error

    with pytest.raises(MpesaNetworkError):
        await retry_with_backoff(fn, {"max_retries": 2})

    # Initial attempt + 2 retries.
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_calls_on_retry_callback(fake_sleep):
    """The on_retry callback fires once per retry with the error and attempt number."""
    seen = []

    def on_retry(error, attempt):
        seen.append((error, attempt))

    error = MpesaNetworkError("Network error", True)
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise error
        return "success"

    result = await retry_with_backoff(fn, {"max_retries": 2, "on_retry": on_retry})

    assert result == "success"
    assert len(seen) == 1
    assert seen[0][0] is error
    assert seen[0][1] == 1


@pytest.mark.asyncio
async def test_respects_rate_limit_retry_after(fake_sleep):
    """A rate-limit error sleeps for retry_after seconds (converted to ms)."""
    error = MpesaRateLimitError("Rate limited", 2, None)
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise error
        return "success"

    result = await retry_with_backoff(fn, {"max_retries": 2})

    assert result == "success"
    assert calls["n"] == 2
    assert fake_sleep == [2000]


@pytest.mark.asyncio
async def test_retry_on_network_errors(fake_sleep):
    """Network errors flagged as retryable are retried."""
    error = MpesaNetworkError("Service unavailable", True)
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise error
        return "success"

    result = await retry_with_backoff(fn, {"max_retries": 2})

    assert result == "success"
    assert calls["n"] == 2
