from pydantic import BaseModel, PrivateAttr, Field, Optional
from ..types import MpesaConfig
import time
import base64
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt


ENDPOINTS = {
    "sandbox":"https://sandbox.safaricom.co.ke",
    "production":"https://api.safaricom.co.ke"
}

class TokenResponse(BaseModel):
    access_token:str
    expires_in:str


class MpesaAuth(BaseModel):
    config:MpesaConfig
    _token:Optional[str] = PrivateAttr(default=None)
    _token_expiry:Optional[int] = PrivateAttr(default=None)
    REQUEST_TIMEOUT:int = Field(default=30000, frozen=True) # 30 seconds


    async def fetch_new_token(self)->str:
        base_url = ENDPOINTS[self.config.environment]
        auth = f"{self.config.consumerKey}:{self.config.consumerSecret}"
        encoded_auth = base64.b64encode(auth.encode('utf-8')).decode('utf-8')

        @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
        async def make_request():
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT/1000) as client:
                response = await client.get(
                    f"{base_url}/oauth/v1/generate?grant_type=client_credentials",
                    headers={"Authorization":f"Basic {encoded_auth}"}
                )
                response.raise_for_status()
                return response.json()
            

    async def get_access_token(self)->str:
        """
        Get a valid access token, refreshing it if necessary.
        
        """
        current_time_ms = int(time.time()*1000)
        if self._token and current_time_ms < self._token_expiry:
            return self._token



