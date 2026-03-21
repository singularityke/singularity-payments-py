from collections.abc import Callable
from typing import Optional, Any
from .base import MpesaBaseModel

class MpesaConfig(MpesaBaseModel):
    consumer_key: str
    consumer_secret: str
    passkey: str
    short_code: str
    environment: str
    callback_url: Optional[str] = None
    timeout_url: Optional[str] = None
    result_url: Optional[str] = None
    initiator_name: Optional[str] = None
    security_credential: Optional[str] = None
   


class MpesaPlugin(MpesaBaseModel):
    name: str
    init: Callable[[Any], None]
    