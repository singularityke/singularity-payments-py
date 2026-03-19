from pydantic import BaseModel, AnyUrl
from collections.abc import Callable
from typing import Optional, Any


class MpesaConfig(BaseModel):
    consumer_key: str
    consumer_secret: str
    passkey: str
    shortcode: str
    environment: str
    callback_url: Optional[str] = None
    timeout_url: Optional[str] = None
    result_url: Optional[str] = None
    initiator_name: Optional[str] = None
    security_credential: Optional[str] = None
   


class MpesaPluginConfig(BaseModel):
    name: str
    init: Callable[[Any], None]
    