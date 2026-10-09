from .errors import (
    MpesaError,
    MpesaNetworkError,
    MpesaRateLimitError,
)
from typing import Callable, Union, Optional, List, Any
import random
import math
import asyncio
from ..types.base import MpesaBaseModel


class RetryOptions(MpesaBaseModel):
    """
    Configuration options for retrying operations with backoff.

    Attributes:
        max_retries (Optional[float]): Maximum number of retry attempts.
        initial_delay_ms (Optional[float]): Initial delay in milliseconds before the first retry.
        max_delay_ms (Optional[float]): Maximum delay in milliseconds between retries.
        backoff_multiplier (Optional[float]): Multiplier for exponential backoff.
        retryable_status_codes (Optional[List[float]]): List of status codes considered retryable.
        on_retry (Optional[Callable[[Exception, float], None]]): Callback function called on each retry.
    """

    max_retries: Optional[float] = None
    initial_delay_ms: Optional[float] = None
    max_delay_ms: Optional[float] = None
    backoff_multiplier: Optional[float] = None
    retryable_status_codes: Optional[List[float]] = None
    on_retry: Optional[Callable[[Exception, float], None]] = None


DEFAULT_RETRY_OPTIONS = RetryOptions(
    max_retries=3,
    initial_delay_ms=1000,
    max_delay_ms=10000,
    backoff_multiplier=2,
    retryable_status_codes=[408, 429, 500, 502, 503, 504],
    on_retry=None,
)


def is_retryable_error(error: Exception, retryable_status_codes: List[float]) -> bool:
    """
    Determine if an error is retryable based on its type or status code.

    Args:
        error (Exception): The exception to check.
        retryable_status_codes (List[float]): List of status codes considered retryable.

    Returns:
        bool: True if the error is retryable, False otherwise.
    """
    if isinstance(error, MpesaNetworkError):
        return error.is_retryable
    if isinstance(error, MpesaRateLimitError):
        return True
    if isinstance(error, MpesaError) and error.status_code:
        return error.status_code in retryable_status_codes
    # Network errors without status codes
    if getattr(error, "name", None) in ("FetchError", "ECONNREFUSED", "ETIMEDOUT"):
        return True
    return False


def calculate_delay(attempt: int, options: RetryOptions, error: Optional[Any]) -> float:
    """
    Calculate the delay before the next retry attempt, using exponential backoff and jitter.

    Args:
        attempt (int): The current retry attempt number.
        options (RetryOptions): Retry configuration options.
        error (Optional[Any]): The exception that caused the retry.

    Returns:
        float: The delay in milliseconds before the next retry.
    """
    # If rate limited, use retry after header
    if isinstance(error, MpesaRateLimitError) and error.retry_after:
        return error.retry_after * 1000
    delay = min(
        options.initial_delay_ms * (options.backoff_multiplier**attempt),
        options.max_delay_ms,
    )
    # Add jitter (±20%) to prevent retrying all at the same time
    jitter = random.uniform(-0.2 * delay, 0.2 * delay)
    return math.floor(delay + jitter)


async def sleep(ms: float):
    """
    Asynchronously sleep for the specified number of milliseconds.

    Args:
        ms (float): The number of milliseconds to sleep.
    """
    await asyncio.sleep(ms / 1000)


def _merge_retry_options(options: Optional[Union[RetryOptions, dict]]) -> RetryOptions:
    """
    Merge user-supplied retry options on top of the defaults.

    Args:
        options (Optional[Union[RetryOptions, dict]]): Partial options as either a
            :class:`RetryOptions` instance or a plain dict.

    Returns:
        RetryOptions: The defaults with any provided values overridden.
    """
    provided: dict = {}
    if options is not None:
        if isinstance(options, dict):
            provided = RetryOptions.model_validate(options).model_dump(exclude_none=True)
        else:
            provided = options.model_dump(exclude_none=True)
    return DEFAULT_RETRY_OPTIONS.model_copy(update=provided)


async def retry_with_backoff(
    fn: Callable, options: Optional[Union[RetryOptions, dict]] = None
):
    """
    Retry an asynchronous function with exponential backoff and optional jitter.

    Args:
        fn (Callable): The asynchronous function to retry.
        options (Union[RetryOptions, dict], optional): Retry configuration options.
            Defaults to DEFAULT_RETRY_OPTIONS.

    Returns:
        Any: The result of the function if successful.

    Raises:
        Exception: The last exception if all retries fail or the error is not retryable.
    """
    opts = _merge_retry_options(options)
    max_retries = int(opts.max_retries)
    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as error:
            last_error = error
            # Do not retry if not retryable or max retries reached
            if (
                not is_retryable_error(error, opts.retryable_status_codes)
                or attempt == max_retries
            ):
                raise error
            delay = calculate_delay(attempt, opts, error)
            if opts.on_retry is not None:
                opts.on_retry(error, attempt + 1)
            await sleep(delay)
    raise last_error
