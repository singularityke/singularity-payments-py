from .errors import MpesaError, MpesaAuthError, MpesaValidationError, MpesaNetworkError, MpesaRateLimitError
from pydantic import BaseModel
from typing import Callable, Union, Optional, List, Any
import random
import math
import asyncio
class RetryOptions(BaseModel):
    max_retries:Optional[float]=None
    initial_delay_ms:Optional[float]=None
    max_delay_ms:Optional[float]=None
    backoff_multiplier:Optional[float]=None
    retryable_status_codes:Optional[List[float]]=None
    on_retry:Optional[Callable[[Exception, float], None]]=None



DEFAULT_RETRY_OPTIONS = RetryOptions(
    max_retries=3,
    initial_delay_ms=1000,
    max_delay_ms=10000,
    backoff_multiplier=2,
    retryable_status_codes=[408, 429, 500, 502, 503, 504],
    on_retry=None
)


def is_retryable_error(error: Exception, retryable_status_codes:List[float]) -> bool:
    if isinstance(error, MpesaNetworkError):
        return error.is_retryable
    
    if isinstance(error, MpesaRateLimitError):
        return True
    
    if isinstance(error, MpesaError) and error.status_code:
        return error.status_code in retryable_status_codes
    

    # Network errors without status codes
    if (
        error.name == "FetchError" or
        error.name == "ECONNREFUSED" or
        error.name == "ETIMEDOUT" 
    ):
        return True
    
    return False


def calculate_delay(
        attempt:int,
        options:RetryOptions,
        error:Optional[Any]
)->float:
    # If rate limited, use retry after header
    if isinstance(error, MpesaRateLimitError) and error.retry_after:
        return error.retry_after * 1000
    
    delay = min(
        options.initial_delay_ms * (options.backoff_multiplier ** attempt),
        options.max_delay_ms
    )

    # Add jitter (±20%) to prevent retrying all at the same time
    jitter = random.uniform(-0.2*delay, 0.2*delay)
    return math.floor(delay + jitter)


async def sleep(ms:float):
    await asyncio.sleep(ms/1000) 


async def retry_with_backoff(
    fn:Callable,
    options:RetryOptions={}
):
    opts = DEFAULT_RETRY_OPTIONS | options
    last_error:Exception = None


    for attempt in range(opts.max_retries+1):
        try:
            return await fn()
        except Exception as error:
            last_error = error

            # Do not retry if not retryable or max retries
            if (
                is_retryable_error(error, opts.retryable_status_codes) is None or 
                attempt == opts.max_retries
            ):
                raise error
            
            delay = calculate_delay(attempt, opts, error)
            opts.on_retry(error, attempt+1)

            await sleep(delay)

    raise last_error is None
