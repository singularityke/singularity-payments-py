from collections.abc import Callable
from typing import Optional, Any
from pydantic import Field
from .base import MpesaBaseModel

class MpesaConfig(MpesaBaseModel):
    """
    Configuration model for M-Pesa API credentials and endpoints.

    Attributes:
        consumer_key (str): The M-Pesa API consumer key.
        consumer_secret (str): The M-Pesa API consumer secret.
        passkey (str): The passkey for STK push transactions.
        short_code (str): The business short code registered with M-Pesa.
        environment (str): The environment to use (e.g., 'sandbox', 'production').
        callback_url (Optional[str]): URL for receiving payment callbacks.
        timeout_url (Optional[str]): URL for receiving timeout notifications.
        result_url (Optional[str]): URL for receiving result notifications.
        initiator_name (Optional[str]): Name of the API initiator.
        security_credential (Optional[str]): Encrypted security credential for the initiator.
    """
    consumer_key: str= Field(alias="ConsumerKey")
    consumer_secret: str= Field(alias="ConsumerSecret")
    passkey: str
    short_code: str= Field(alias="shortcode")
    environment: str
    callback_url: Optional[str] = Field(None, alias="callbackUrl")
    timeout_url: Optional[str] = Field(None, alias="timeoutUrl")
    result_url: Optional[str] = Field(None, alias="resultUrl")
    initiator_name: Optional[str] =Field(alias="initiatorName")
    security_credential: Optional[str] = Field(None, alias="securityCredential")
   


class MpesaPlugin(MpesaBaseModel):
    """
    Model for registering plugins with the M-Pesa client.

    Attributes:
        name (str): Name of the plugin.
        init (Callable[[Any], None]): Initialization function for the plugin.
    """
    name: str
    init: Callable[[Any], None]
    