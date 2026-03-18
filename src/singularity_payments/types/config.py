from pydantic import BaseModel, AnyUrl
from collections.abc import Callable


class MpesaConfig(BaseModel):
    consumer_key: str
    consumer_secret: str
    passkey: str
    shortcode: str
    environment: str
    callback_url: AnyUrl = None
    timeout_url: AnyUrl = None
    result_url: AnyUrl = None
    initiator_name: str = None
    security_credential: str = None
   


class MpesaPluginConfig(BaseModel):
    name:str
    init: Callable
    