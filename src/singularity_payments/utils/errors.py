from pydantic import Optional
from typing import Any



class MpesaError(Exception):
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
    def __init__(self, 
                message: str, 
                details: Optional[Any],
                ):
        super().__init__(message, "AUTH_ERROR", 401, details)
        self.name = "MpesaAuthError"


class MpesaValidationError(MpesaError):
    def __init__(self, 
                message: str, 
                details: Optional[Any],
                ):
        super().__init__(message, "VALIDATION_ERROR", 400, details)
        self.name = "MpesaValidationError"

class MpesaNetworkError(MpesaError):
    def __init__(self, 
                message: str, 
                is_retryable: bool, 
                details: Optional[Any],
                ):
        super().__init__(message, "NETWORK_ERROR", 503, details)
        self.name = "MpesaNetworkError"


class MpesaTimeoutError(MpesaError):
    def __init__(self, 
                message: str, 
                details: Optional[Any],
                ):
        super().__init__(message, "TIMEOUT_ERROR", 408, details)
        self.name = "MpesaTimeoutError"



class MpesaRateLimitError(MpesaError):
    def __init__(self, 
                message: str,
                retry_after: Optional[float] = None,
                details: Optional[Any] = None,
                ):
        super().__init__(message, "RATE_LIMIT_ERROR", 429, details)
        self.name = "MpesaRateLimitError"



class MpesaApiError(MpesaError):
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

    
    