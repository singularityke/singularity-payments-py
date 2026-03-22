from pydantic import PrivateAttr, Field
from ..types.config import MpesaConfig
from .errors import MpesaNetworkError, parse_mpesa_api_error, MpesaAuthError, MpesaTimeoutError, MpesaError
import time
import datetime
import logging
import base64
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log
from ..types.base import MpesaBaseModel
from typing import Optional

logger = logging.getLogger(__name__)


ENDPOINTS = {
    "sandbox":"https://sandbox.safaricom.co.ke",
    "production":"https://api.safaricom.co.ke"
}

class TokenResponse(MpesaBaseModel):
    access_token:str
    expires_in:str



class MpesaAuth(MpesaBaseModel):
    config:MpesaConfig
    _token:Optional[str] = PrivateAttr(default=None)
    _token_expiry:Optional[int] = PrivateAttr(default=None)
    REQUEST_TIMEOUT:int = Field(default=30000, frozen=True) # 30 seconds


    def get_timestamp(self) -> str:
        """
        Generate a timestamp string in the format YYYYMMDDHHMMSS.

        Returns:
            str: The current timestamp as a string (e.g., '20260322153045').
        """
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def get_base_url(self) -> str:
        """
        Retrieve the base URL for the current environment (sandbox or production).

        Returns:
            str: The base URL for API requests.
        """
        return ENDPOINTS[self.config.environment]
    
    def get_password(self) -> str:
        """
        Generate a base64-encoded password for STK Push authentication.

        Returns:
            str: The base64-encoded password string required for STK Push requests.
        """
        timestamp = self.get_timestamp()
        password_str = f"{self.config.short_code}{self.config.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        return password
    

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, MpesaNetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _perform_auth_request(self) -> str:
        """
        Perform an authentication request to obtain a new access token from the M-Pesa API.

        This method is automatically retried on network errors or timeouts.

        Returns:
            str: The access token string.

        Raises:
            MpesaAuthError: If the response does not contain an access token.
            MpesaTimeoutError: If the request times out.
            MpesaNetworkError: For other network-related errors.
        """
        base_url = ENDPOINTS[self.config.environment]
        auth = f"{self.config.consumer_key}:{self.config.consumer_secret}"
        auth_base64 = base64.b64encode(auth.encode()).decode()

        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT / 1000) as client:
            try:
                response = await client.get(
                    f"{base_url}/oauth/v1/generate?grant_type=client_credentials",
                    headers={"Authorization": f"Basic {auth_base64}"}
                )

                if response.status_code != 200:
                    try:
                        error_body = await response.json()
                    except Exception:
                        error_body = {}
                    raise parse_mpesa_api_error(
                        response.status_code,
                        error_body
                    )

                data = response.json()
                access_token = data.get("access_token")

                if not access_token:
                    raise MpesaAuthError("No access token in response", data)

                self._token = access_token
                # Cache for 50 minutes (3000 seconds) in milliseconds
                self._token_expiry = int(time.time() * 1000) + (50 * 60 * 1000)
                return self._token

            except httpx.TimeoutException:
                raise MpesaTimeoutError("Request timed out while getting access token")

            except Exception as e:
                if isinstance(e, MpesaError):
                    raise e
                raise MpesaNetworkError(f"Error while getting access token: {e}", is_retryable=True, details=e)


    async def get_access_token(self) -> str:
        """
        Retrieve a valid access token for authenticating API requests.

        If a cached token is available and not expired, it is returned. Otherwise, a new token is requested.

        Returns:
            str: The access token string.
        """
        current_time_ms = int(time.time() * 1000)

        if self._token and self._token_expiry and current_time_ms < self._token_expiry:
            return self._token

        return await self._perform_auth_request()