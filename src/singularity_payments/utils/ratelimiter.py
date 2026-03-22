from .errors import MpesaRateLimitError
from typing import Optional, Dict, Any, Callable
import asyncio
import time
import math
from ..types.base import MpesaBaseModel



class RateLimiterOptions(MpesaBaseModel):
    """
    Configuration options for the RateLimiter.

    Attributes:
        max_requests (float): Maximum number of requests allowed per window.
        window_ms (float): Time window in milliseconds.
        key_prefix (Optional[str]): Prefix for rate limit keys.
    """
    max_requests: float
    window_ms: float
    key_prefix: Optional[str] = None


class RateLimitEntry(MpesaBaseModel):
    """
    Represents a single rate limit entry for a key.

    Attributes:
        count (float): Number of requests made in the current window.
        reset_at (float): Timestamp when the rate limit resets.
    """
    count: float
    reset_at: float

class GetUsageReturnType(MpesaBaseModel):
    """
    Usage information for a rate-limited key.

    Attributes:
        count (float): Number of requests made.
        remaining (float): Number of requests remaining in the window.
        reset_at (float): Timestamp when the rate limit resets.
    """
    count: float
    remaining: float
    reset_at: float

class RateLimiter(MpesaBaseModel):
    """
    In-memory rate limiter for controlling request rates per key.

    Attributes:
        key_prefix (str): Prefix for rate limit keys.
        _store (Dict[str, Any]): Internal storage for rate limit entries.
        options (RateLimiterOptions): Configuration options for the rate limiter.
        _cleanup_task (Optional[asyncio.Task]): Background cleanup task.
    """
    key_prefix: str = "mpesa"
    _store: Dict[str, Any] = {}
    options: RateLimiterOptions
    _cleanup_task: Optional[asyncio.Task] = None

    def __init__(self, options: RateLimiterOptions):
        super().__init__(options=options)
        self.start_cleanup()

    def _start_cleanup(self) -> None:
        """
        Start the background cleanup task to remove expired rate limit entries.
        """
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
    async def _run_cleanup_loop(self) -> None:
        """
        Background loop that removes expired rate limit entries every minute.
        """
        while True:
            try:
                await asyncio.sleep(60)
                now = time.time()
                for key, entry in list(self._store.items()):
                    if now and entry >= entry.reset_at:
                        self._store.pop(key, None)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
    
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
        full_key = f"{self.options.key_prefix}:{key}"
        now = time.time()
        entry = self._store.get(full_key)
        if entry is None or now >= entry.reset_at:
            self._store[full_key] = RateLimitEntry(count=1, reset_at=now + self.options.window_ms/1000)
            return
        if entry.count >= self.options.max_requests:
            retry_after = math.ceil(entry.reset_at - now)
            raise MpesaRateLimitError(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after=retry_after,
                reset_at=entry.reset_at,
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
        full_key = f"{self.options.key_prefix}:{key}"
        entry = self._store.get(full_key)
        now = time.time()
        if entry is None or now >= entry.reset_at:
            return GetUsageReturnType(count=0, remaining=max(0, self.options.max_requests), reset_at=now + self.options.window_ms/1000)
        return GetUsageReturnType(count=entry.count, remaining=max(0, self.options.max_requests - entry.count), reset_at=entry.reset_at)

    def reset(self, key: str):
        """
        Reset the rate limit for a specific key.

        Args:
            key (str): Unique identifier for the rate limit (e.g., phone number, IP address).
        """
        full_key = f"{self.options.key_prefix}:{key}"
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

    Attributes:
        get (Callable[[str], Optional[str]]): Function to get a value by key.
        set (Callable[[RedisLikeSet], Any]): Function to set a value.
        incr (Callable[[str], float]): Function to increment a value by key.
        expire (Callable[[str, float], Any]): Function to set key expiration.
    """
    get: Callable[[str], Optional[str]]
    set: Callable[[RedisLikeSet], Any]
    incr: Callable[[str], float]
    expire: Callable[[str, float], Any]

class RedisRateLimiter(MpesaBaseModel):
    """
    Rate limiter implementation using a Redis-like backend for distributed environments.

    Attributes:
        _options (RateLimiterOptions): Configuration options for the rate limiter.
        _redis (RedisLike): Redis-like backend for storage.
        key_prefix (str): Prefix for rate limit keys.
    """
    _options: RateLimiterOptions
    _redis: RedisLike
    key_prefix: str = "mpesa"


    def __init__(self, name, redis:RedisLike, **options):
        super().__init__(**options)
        self._redis = redis


    async def check_limit(self, key:str):
        full_key=f"{self.options.key_prefix}:{key}"
        count = await self.redis.incr(full_key)  

        if count ==1:
            # First request, set expiry
            await self.redis.expire(full_key, math.ceil(self.options.windows_ms/1000))

        if count > self.options.max_requests:
            ttl_key = f"{full_key}:ttl"
            ttl = await self.redis.get(ttl_key)
            retry_after = (
                int(ttl)
                if ttl is not None and ttl > 0
                else math.ceil(self.options.windows_ms/1000)
            )

            raise MpesaRateLimitError(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after=retry_after,
                details={
                    'limit':self.options.max_requests,
                    'window_ms':self.options.windows_ms,
                }
            )
        
    async def reset(self, key: str):
        """
        Reset the rate limit for a specific key in the Redis backend.

        Args:
            key (str): Unique identifier for the rate limit (e.g., phone number, IP address).
        """
        full_key = f"{self.options.key_prefix}:{key}"
        await self.redis.set(key=full_key, value="0", mode="EX", duration=0)


