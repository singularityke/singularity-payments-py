from .errors import MpesaRateLimitError
from typing import Optional, Dict, Any, Callable
import asyncio
import time
import math
from ..types.base import MpesaBaseModel



class RateLimiterOptions(MpesaBaseModel):
    max_requests:float
    window_ms:float
    key_prefix:Optional[str]=None


class RateLimitEntry(MpesaBaseModel):
    count:float
    reset_at:float

class GetUsageReturnType(MpesaBaseModel):
    count:float
    remaining:float
    reset_at:float

class RateLimiter(MpesaBaseModel):
    key_prefix: str = "mpesa"
    _store: Dict[str, Any] = {}
    options: RateLimiterOptions
    _cleanup_task: Optional[asyncio.Task] = None

    def __init__(self, options: RateLimiterOptions):
        super().__init__(options=options)
        self.start_cleanup()

    def _start_cleanup(self)->None:
        """Starts the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
    async def _run_cleanup_loop(self)->None:
        """Background loop to remove expired entries every minute."""
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
        """Stop cleanup task and clear store."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        self.reset_all()



    async def check_limit(self, key: str):
        """
        Check if request is allowed, throws MpesaRateLimitError if exceeded.
        Args:
            key(str): Unique identifier for the rate limit (e.g. phone number, IP address)
        Raises:
            MpesaRateLimitError: If rate limit is exceeded
        Returns:
            None: If request is allowed
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
        Get current usage for a key
        Args:
            key(str): Unique identifier for the rate limit (e.g. phone number, IP address)
        Returns:
            GetUsageReturnType: Object with current usage information
        """
        full_key = f"{self.options.key_prefix}:{key}"
        entry = self._store.get(full_key)
        now = time.time()
        if entry is None or now >= entry.reset_at:
            return GetUsageReturnType(count=0, remaining=max(0, self.options.max_requests), reset_at=now + self.options.window_ms/1000)
        return GetUsageReturnType(count=entry.count, remaining=max(0, self.options.max_requests - entry.count), reset_at=entry.reset_at)

    def reset(self, key: str):
        """
        Reset rate limit for a key.
        Args:
            key(str): Unique identifier for the rate limit (e.g. phone number, IP address)
        """
        full_key = f"{self.options.key_prefix}:{key}"
        if full_key in self._store:
            del self._store[full_key]

    def reset_all(self):
        """
        Clear all rate limits.
        """
        self._store.clear()
           


class RedisLikeSet(MpesaBaseModel):
    key:str
    value:str
    mode:str
    duration:str

class RedisLike(MpesaBaseModel):
    get:Callable[[str], Optional[str]]
    set:Callable[[RedisLikeSet], Any]
    incr:Callable[[str], float]
    expire:Callable[[str, float], Any]

class RedisRateLimiter(MpesaBaseModel):
    _options:RateLimiterOptions
    _redis:RedisLike
    key_prefix:str="mpesa"


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
        
    async def reset(self, key:str):
        """
        Reset rate limit for a key.
        Args:
            key(str): Unique identifier for the rate limit (e.g. phone number, IP address)
            """
        full_key=f"{self.options.key_prefix}:{key}"
        await self.redis.set(key=full_key, value="0", mode="EX", duration=0)


