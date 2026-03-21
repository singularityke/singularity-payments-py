from pydantic import PrivateAttr, Field, Optional
from ..types import MpesaConfig
from .errors import MpesaNetworkError, parse_mpesa_api_error, MpesaAuthError, MpesaTimeoutError, MpesaError
import time
import datetime
import logging
import base64
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep, before_sleep_log
from ..types.base import MpesaBaseModel


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


    def get_timestamp(self)->str:
        """
        Get timestamp in format yyyymmddhhmmss
        Returns:
            str: timestamp
        
        """
        return  datetime.now().strftime("%Y%m%d%H%M%S")

    def get_base_url(self)->str:
        """
        Get base url from environment
        Returns:
            base_url:str
        """
        return ENDPOINTS[self.config.environment]
    
    def get_password(self)->str:
        """
        Get base64 encoded password
        Returns:
            str: base64 encoded password
        """
        timestamp = self.get_timestamp
        password = base64.b64enocde(f"{self.config.short_code}:{self.config.passkey}:{timestamp}")
        return password
    

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10), 
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, MpesaNetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _perform_auth_request(self)->str:
        """
        Perform authentication request to get access token
        """
        base_url=ENDPOINTS[self.config.environment]
        auth = f"{self.config.consumer_key}:{self.consumerSecret}"
        auth_base64 = base64.b64encode(auth.encode())

        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT/1000) as client:
            try:
                response = await client.get(
                    f"{base_url}/oauth/v1/generate?grant_type=client_credentials",
                    headers={"Authorization":f"Basic {auth_base64}"}
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
                self._token_expiry = int(time.time()*1000)+(50*60*1000)
                return self._token
            
            except httpx.TimeoutException:
                raise MpesaTimeoutError("Request timed out while getting access token")
            
            except Exception as e:
                if isinstance(e, MpesaError):
                    raise e
                raise MpesaNetworkError(f"Error while getting access token: {e}", is_retryable=True, details=e)
                    


    async def get_access_token(self)->str:
        """
        Get access token from cache or perform authentication request
        Returns:
            str: access token

        """
        current_time_ms = int(time.time()*1000)

        if self.token and current_time_ms < self.token_expiry:
            return self.token
        
        return await self._perform_auth_request()