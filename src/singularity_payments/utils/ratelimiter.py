from .errors import MpesaRateLimitError
from typing import Optional, Dict, Any, Callable, Awaitable, Union
from pydantic import PrivateAttr
import asyncio
import logging
import time
import math
from ..types.base import MpesaBaseModel


logger = logging.getLogger(__name__)


class RateLimiterOptions(MpesaBaseModel):
    """
    Configuration options for the RateLimiter.

    Attributes:
        max_requests (float): Maximum number of requests allowed per window.
        window_ms (float): Time window in milliseconds.
        key_prefix (Optional[str]): Prefix prepended to every rate limit key.
    """

    max_requests: float
    window_ms: float
    key_prefix: Optional[str] = None


class RateLimitEntry(MpesaBaseModel):
    """
    Represents a single rate limit entry for a key.

    Attributes:
        count (float): Number of requests made in the current window.
        reset_at (float): Unix timestamp (seconds) when the rate limit resets.
    """

    count: float
    reset_at: float


class GetUsageReturnType(MpesaBaseModel):
    """
    Usage information for a rate-limited key.

    Attributes:
        count (float): Number of requests made.
        remaining (float): Number of requests remaining in the window.
        reset_at (float): Unix timestamp (seconds) when the rate limit resets.
    """

    count: float
    remaining: float
    reset_at: float


class RateLimiter(MpesaBaseModel):
    """
    In-memory rate limiter for controlling request rates per key.

    Requests are tracked in a per-process dictionary. Each key gets its own
    counter that resets once its time window elapses. A background task
    periodically removes expired entries so the store does not grow forever.

    Attributes:
        key_prefix (str): Fallback prefix for rate limit keys.
        options (RateLimiterOptions): Configuration options for the rate limiter.
    """

    key_prefix: str = "mpesa"
    options: RateLimiterOptions
    _store: Dict[str, RateLimitEntry] = PrivateAttr(default_factory=dict)
    _cleanup_task: Optional[asyncio.Task] = PrivateAttr(default=None)

    def __init__(self, options: Union[RateLimiterOptions, dict]):
        # Accept either a RateLimiterOptions instance or a plain dict so the
        # client can pass the raw options mapping.
        if isinstance(options, dict):
            options = RateLimiterOptions.model_validate(options)
        super().__init__(options=options)

    def _full_key(self, key: str) -> str:
        """
        Build the namespaced storage key for a rate limit key.

        Args:
            key (str): The raw rate limit key.

        Returns:
            str: The key prefixed with the configured (or default) prefix.
        """
        prefix = self.options.key_prefix or self.key_prefix
        return f"{prefix}:{key}"

    def _start_cleanup(self) -> None:
        """
        Start the background cleanup task if an event loop is running.

        The limiter may be created outside of an async context (for example,
        inside ``MpesaClient.__init__``), where no event loop exists yet. In
        that case cleanup is deferred until the first ``check_limit`` call.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = loop.create_task(self._run_cleanup_loop())

    async def _run_cleanup_loop(self) -> None:
        """
        Background loop that removes expired rate limit entries every minute.
        """
        while True:
            try:
                await asyncio.sleep(60)
                now = time.time()
                for key, entry in list(self._store.items()):
                    if now >= entry.reset_at:
                        self._store.pop(key, None)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup loop: {e}")

    def destroy(self):
        """
        Stop the background cleanup task and clear all rate limit entries.
        """
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        self.reset_all()

    async def check_limit(self, key: str):
        """
        Check if a request is allowed for the given key, raising an error if the rate limit is exceeded.

        Args:
            key (str): Unique identifier for the rate limit (e.g., phone number, IP address).

        Raises:
            MpesaRateLimitError: If the rate limit is exceeded.

        Returns:
            None: If the request is allowed.
        """
        self._start_cleanup()

        full_key = self._full_key(key)
        now = time.time()
        entry = self._store.get(full_key)
        if entry is None or now >= entry.reset_at:
            self._store[full_key] = RateLimitEntry(
                count=1, reset_at=now + self.options.window_ms / 1000
            )
            return
        if entry.count >= self.options.max_requests:
            retry_after = math.ceil(entry.reset_at - now)
            raise MpesaRateLimitError(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after,
                {
                    "limit": self.options.max_requests,
                    "window_ms": self.options.window_ms,
                    "reset_at": entry.reset_at,
                },
            )
        entry.count += 1

    def get_usage(self, key: str) -> GetUsageReturnType:
        """
        Get the current usage statistics for a given key.

        Args:
            key (str): Unique identifier for the rate limit (e.g., phone number, IP address).

        Returns:
            GetUsageReturnType: Object containing current usage information.
        """
        full_key = self._full_key(key)
        entry = self._store.get(full_key)
        now = time.time()
        if entry is None or now >= entry.reset_at:
            return GetUsageReturnType(
                count=0,
                remaining=max(0, self.options.max_requests),
                reset_at=now + self.options.window_ms / 1000,
            )
        return GetUsageReturnType(
            count=entry.count,
            remaining=max(0, self.options.max_requests - entry.count),
            reset_at=entry.reset_at,
        )

    def reset(self, key: str):
        """
        Reset the rate limit for a specific key.

        Args:
            key (str): Unique identifier for the rate limit (e.g., phone number, IP address).
        """
        full_key = self._full_key(key)
        if full_key in self._store:
            del self._store[full_key]

    def reset_all(self):
        """
        Clear all rate limits for all keys.
        """
        self._store.clear()


class RedisLikeSet(MpesaBaseModel):
    """
    Data structure for setting a value in a Redis-like store.

    Attributes:
        key (str): The key to set.
        value (str): The value to set.
        mode (str): The mode for setting (e.g., 'EX' for expire).
        duration (str): Duration for the key to expire.
    """

    key: str
    value: str
    mode: str
    duration: str


class RedisLike(MpesaBaseModel):
    """
    Interface for a Redis-like key-value store.

    Each method must be awaitable so the rate limiter can work with both real
    async Redis clients and simple in-memory fakes.

    Attributes:
        get (Callable[[str], Awaitable[Optional[str]]]): Get a value by key.
        set (Callable[[RedisLikeSet], Awaitable[Any]]): Set a value.
        incr (Callable[[str], Awaitable[float]]): Increment a value by key.
        expire (Callable[[str, float], Awaitable[Any]]): Set key expiration.
    """

    get: Callable[[str], Awaitable[Optional[str]]]
    set: Callable[[RedisLikeSet], Awaitable[Any]]
    incr: Callable[[str], Awaitable[float]]
    expire: Callable[[str, float], Awaitable[Any]]


class RedisRateLimiter(MpesaBaseModel):
    """
    Rate limiter implementation using a Redis-like backend for distributed environments.

    Attributes:
        key_prefix (str): Fallback prefix for rate limit keys.
    """

    key_prefix: str = "mpesa"
    _options: Optional[RateLimiterOptions] = PrivateAttr(default=None)
    _redis: Optional[RedisLike] = PrivateAttr(default=None)

    def __init__(self, redis: RedisLike, options: Union[RateLimiterOptions, dict]):
        super().__init__()
        if isinstance(options, dict):
            options = RateLimiterOptions.model_validate(options)
        self._redis = redis
        self._options = options

    def _full_key(self, key: str) -> str:
        """
        Build the namespaced storage key for a rate limit key.

        Args:
            key (str): The raw rate limit key.

        Returns:
            str: The key prefixed with the configured (or default) prefix.
        """
        assert self._options is not None
        prefix = self._options.key_prefix or self.key_prefix
        return f"{prefix}:{key}"

    async def check_limit(self, key: str):
        """
        Check if a request is allowed for the given key, raising an error if the rate limit is exceeded.

        Args:
            key (str): Unique identifier for the rate limit (e.g., phone number, IP address).

        Raises:
            MpesaRateLimitError: If the rate limit is exceeded.

        Returns:
            None: If the request is allowed.
        """
        assert self._redis is not None and self._options is not None

        full_key = self._full_key(key)
        count = await self._redis.incr(full_key)

        if count == 1:
            # First request, set expiry
            await self._redis.expire(
                full_key, math.ceil(self._options.window_ms / 1000)
            )

        if count > self._options.max_requests:
            ttl_key = f"{full_key}:ttl"
            ttl = await self._redis.get(ttl_key)
            retry_after = (
                int(ttl)
                if ttl is not None and int(ttl) > 0
                else math.ceil(self._options.window_ms / 1000)
            )

            raise MpesaRateLimitError(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after,
                {
                    "limit": self._options.max_requests,
                    "window_ms": self._options.window_ms,
                },
            )

    async def reset(self, key: str):
        """
        Reset the rate limit for a specific key in the Redis backend.

        Args:
            key (str): Unique identifier for the rate limit (e.g., phone number, IP address).
        """
        assert self._redis is not None

        full_key = self._full_key(key)
        await self._redis.set(
            RedisLikeSet(key=full_key, value="0", mode="EX", duration="0")
        )
