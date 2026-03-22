
from typing import Any,Optional


class MpesaError(Exception):
    """
    Base exception for all M-Pesa related errors.

    Attributes:
        message (Optional[str]): Description of the error.
        status_code (Optional[str]): HTTP status code or error code.
        details (Optional[Any]): Additional error details or context.
    """
    def __init__(self, 
        message: Optional[str]=None, 
        status_code: Optional[str]=None, 
        details: Optional[Any]=None,
        ):
        super().__init__(message)
        self.name = "MpesaError"
        self.message = message
        self.status_code = status_code
        self.details = details



class MpesaAuthError(MpesaError):
    """
    Exception raised for authentication errors with the M-Pesa API.

    Attributes:
        message (str): Description of the authentication error.
        details (Optional[Any]): Additional error details or context.
    """
    def __init__(self, 
                message: str, 
                details: Optional[Any],
                ):
        super().__init__(message, "AUTH_ERROR", 401, details)
        self.name = "MpesaAuthError"


class MpesaValidationError(MpesaError):
    """
    Exception raised for validation errors with the M-Pesa API.

    Attributes:
        message (str): Description of the validation error.
        details (Optional[Any]): Additional error details or context.
    """
    def __init__(self, 
                message: str, 
                details: Optional[Any],
                ):
        super().__init__(message, "VALIDATION_ERROR", 400, details)
        self.name = "MpesaValidationError"

class MpesaNetworkError(MpesaError):
    """
    Exception raised for network-related errors with the M-Pesa API.

    Attributes:
        message (str): Description of the network error.
        is_retryable (bool): Indicates if the error is retryable.
        details (Optional[Any]): Additional error details or context.
    """
    def __init__(self, 
                message: str, 
                is_retryable: bool, 
                details: Optional[Any],
                ):
        super().__init__(message, "NETWORK_ERROR", 503, details)
        self.name = "MpesaNetworkError"


class MpesaTimeoutError(MpesaError):
    """
    Exception raised for timeout errors with the M-Pesa API.

    Attributes:
        message (str): Description of the timeout error.
        details (Optional[Any]): Additional error details or context.
    """
    def __init__(self, 
                message: str, 
                details: Optional[Any],
                ):
        super().__init__(message, "TIMEOUT_ERROR", 408, details)
        self.name = "MpesaTimeoutError"



class MpesaRateLimitError(MpesaError):
    """
    Exception raised when the M-Pesa API rate limit is exceeded.

    Attributes:
        message (str): Description of the rate limit error.
        retry_after (Optional[float]): Time in seconds to wait before retrying.
        details (Optional[Any]): Additional error details or context.
    """
    def __init__(self, 
                message: str,
                retry_after: Optional[float] = None,
                details: Optional[Any] = None,
                ):
        super().__init__(message, "RATE_LIMIT_ERROR", 429, details)
        self.name = "MpesaRateLimitError"



class MpesaApiError(MpesaError):
    """
    Exception raised for general API errors returned by the M-Pesa API.

    Attributes:
        message (str): Description of the API error.
        code (str): Error code returned by the API.
        status_code (float): HTTP status code of the response.
        response_body (Optional[Any]): The full API response body.
    """
    def __init__(self,
                 message: str,
                 code: str,
                 status_code: float,
                 response_body: Optional[Any] = None
                  ):
        super().__init__(message, code, status_code, response_body)
        self.name = "MpesaApiError"


# Parese Mpesa API error response
def parse_mpesa_api_error(
        status_code: float, 
        response_body: Any
        ) -> MpesaError:
    """
    Parse an M-Pesa API error response and return the appropriate MpesaError instance.

    Args:
        status_code (float): HTTP status code of the response.
        response_body (Any): JSON response body of the API call.

    Returns:
        MpesaError: An instance of the appropriate MpesaError subclass based on the error response.
    """
    error_message = (
        response_body.get("errorMessage") or
        response_body.get("ResponseDescription") or
        response_body.get("message") or 
        "Unknown API error"
        )
    
    error_code = (
        response_body.get("errorCode") or
        response_body.get("ResponseCode") or
        "UNKNOWN_ERROR"
        )
    
    if status_code == 401 or status_code == 403:
        return MpesaAuthError(error_message, response_body)
    
    if status_code == 400:
        return MpesaValidationError(error_message, response_body)
    
    if status_code == 503:
        retry_after = response_body.get("retryAfter")
        return MpesaRateLimitError(error_message, retry_after, response_body)
    
    if status_code >= 500:
        return MpesaNetworkError(error_message, True, response_body)
   
    return MpesaApiError(error_message, error_code, status_code, response_body)

    
    