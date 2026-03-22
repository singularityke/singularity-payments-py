from pydantic import AnyUrl, Field
from typing import Literal, List, Union, Optional
from .base import MpesaBaseModel
# --- Shared Types ---

B2BCommandID = Literal[
    "BusinessPayBill",
    "BusinessBuyGoods",
    "DisburseFundsToBusiness",
    "BusinessToBusinessTransfer",
    "MerchantToMerchantTransfer"
]

BalanceIdentifierType = Literal["1", "2", "4"]  # 1=MSISDN, 2=Till, 4=Paybill

class ResultParameterItem(MpesaBaseModel):
    """
    Represents a single result parameter item returned in M-Pesa API responses.

    Attributes:
        key (str): The parameter key (aliased as 'Key').
        value (Union[str, int, float]): The parameter value (aliased as 'Value').
    """
    key: str = Field(alias="Key")
    value: Union[str, int, float] = Field(alias="Value")

class ResultParametersType(MpesaBaseModel):
    """
    Represents a list of result parameter items in M-Pesa API responses.

    Attributes:
        result_parameter (List[ResultParameterItem]): List of result parameter items.
    """
    result_parameter: List[ResultParameterItem]

class CallbackResult(MpesaBaseModel):
    """
    Represents the result section of a callback from the M-Pesa API.

    Attributes:
        result_type (int): Type of the result.
        result_code (int): Result code indicating success or failure.
        result_desc (str): Description of the result.
        originator_conversation_id (str): Originator conversation ID.
        conversation_id (str): Conversation ID.
        transaction_id (str): Transaction ID.
        result_parameters (Optional[ResultParametersType]): Additional result parameters, if any.
    """
    result_type: int
    result_code: int
    result_desc: str
    originator_conversation_id: str
    conversation_id: str
    transaction_id: str
    result_parameters: Optional[ResultParametersType] = None

# --- STK Push (M-Pesa Express) ---

class STKPushRequest(MpesaBaseModel):
    """
    Model for initiating an STK Push (M-Pesa Express) payment request.

    Attributes:
        amount (float): Amount to be transacted.
        phone_number (str): Customer's phone number.
        account_reference (str): Reference for the account.
        transaction_desc (str): Description of the transaction.
        callback_url (AnyUrl): URL to receive payment callback.
    """
    amount: float
    phone_number: str
    account_reference: str
    transaction_desc: str
    callback_url: AnyUrl

class STKPushResponse(MpesaBaseModel):
    """
    Response model for an STK Push (M-Pesa Express) payment request.

    Attributes:
        merchant_request_id (str): Merchant request ID.
        checkout_request_id (str): Checkout request ID.
        response_code (str): Response code from the API.
        response_description (str): Description of the response.
        customer_message (str): Message to be shown to the customer.
    """
    merchant_request_id: str
    checkout_request_id: str
    response_code: str
    response_description: str
    customer_message: str
    

class CallbackMetadataType(MpesaBaseModel):
    """
    Metadata section of an STK callback, containing additional transaction details.

    Attributes:
        item (List[ResultParameterItem]): List of metadata items.
    """
    item: List[ResultParameterItem]

class STKCallbackDetails(MpesaBaseModel):
    """
    Details of an STK callback received from the M-Pesa API.

    Attributes:
        merchant_request_id (str): Merchant request ID.
        checkout_request_id (str): Checkout request ID.
        result_code (int): Result code indicating success or failure.
        result_desc (str): Description of the result.
        callback_metadata (Optional[CallbackMetadataType]): Additional callback metadata, if any.
    """
    merchant_request_id: str
    checkout_request_id: str
    result_code: int
    result_desc: str
    callback_metadata: Optional[CallbackMetadataType] = None

class STKResponseBody(MpesaBaseModel):
    """
    Body of an STK callback, containing the callback details.

    Attributes:
        stk_callback (STKCallbackDetails): The callback details.
    """
    stk_callback: STKCallbackDetails

class STKCallback(MpesaBaseModel):
    """
    Top-level model for an STK callback received from the M-Pesa API.

    Attributes:
        body (STKResponseBody): The body of the callback.
    """
    body: STKResponseBody

# --- C2B (Customer to Business) ---

class C2BRegisterRequest(MpesaBaseModel):
    """
    Model for registering C2B (Customer to Business) URLs with the M-Pesa API.

    Attributes:
        short_code (str): Business short code.
        response_type (Literal): Type of response expected ('Completed' or 'Cancelled').
        confirmation_url (AnyUrl): URL to receive confirmation callbacks.
        validation_url (AnyUrl): URL to receive validation callbacks.
    """
    short_code: str
    response_type: Literal["Completed", "Cancelled"] = "Completed"
    confirmation_url: AnyUrl
    validation_url: AnyUrl

class C2BRegisterResponse(MpesaBaseModel):
    """
    Response model for a C2B registration request.

    Attributes:
        originator_conversation_id (str): Originator conversation ID.
        response_code (str): Response code from the API.
        response_description (str): Description of the response.
    """
    originator_conversation_id: str
    response_code: str
    response_description: str

class C2BCallback(MpesaBaseModel):
    """
    Model for a C2B (Customer to Business) payment callback from the M-Pesa API.

    Attributes:
        transaction_type (str): Type of transaction.
        trans_id (str): Transaction ID.
        trans_time (str): Transaction timestamp.
        trans_amount (str): Amount transacted.
        business_short_code (str): Business short code.
        bill_ref_number (str): Bill reference number.
        invoice_number (Optional[str]): Invoice number, if any.
        org_account_balance (Optional[str]): Organization account balance, if any.
        third_party_trans_id (Optional[str]): Third-party transaction ID, if any.
        msisdn (str): Customer's phone number.
        first_name (Optional[str]): Customer's first name, if any.
        middle_name (Optional[str]): Customer's middle name, if any.
        last_name (Optional[str]): Customer's last name, if any.
    """
    transaction_type: str
    trans_id: str
    trans_time: str
    trans_amount: str
    business_short_code: str
    bill_ref_number: str
    invoice_number: Optional[str] = None
    org_account_balance: Optional[str] = None
    third_party_trans_id: Optional[str] = None
    msisdn: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

class C2BSimulateRequest(MpesaBaseModel):
    """
    Model for simulating a C2B (Customer to Business) payment request.

    Attributes:
        short_code (str): Business short code.
        amount (float): Amount to simulate.
        msisdn (str): Customer's phone number.
        bill_ref_number (str): Bill reference number.
        command_id (Literal): Command ID for the simulation.
    """
    short_code: str
    amount: float
    msisdn: str
    bill_ref_number: str
    command_id: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"]

class C2BSimulateResponse(MpesaBaseModel):
    """
    Response model for a C2B simulation request.

    Attributes:
        conversation_id (str): Conversation ID.
        originator_conversation_id (str): Originator conversation ID.
        response_description (str): Description of the response.
    """
    conversation_id: str
    originator_conversation_id: str
    response_description: str

# --- B2B / B2C / Reversals ---

class B2BRequest(MpesaBaseModel):
    amount: float
    party_b: str
    command_id: B2BCommandID
    sender_identifier_type: BalanceIdentifierType
    receiver_identifier_type: BalanceIdentifierType
    remarks: str
    account_reference: str
    result_url: AnyUrl
    queue_timeout_url: AnyUrl

class B2BResponse(MpesaBaseModel):
    conversation_id: str
    originator_conversation_id: str
    response_code: str
    response_description: str

class B2BCallback(MpesaBaseModel):
    result: CallbackResult



B2CCommandID = Literal["BusinessPayment", "SalaryPayment", "PromotionPayment"]



class B2CRequest(MpesaBaseModel):
    amount:float
    phone_number:str
    command_id:B2CCommandID
    remarks:str
    occasion:Optional[str] = None
    result_url:Optional[str]=None
    timeout_url:Optional[str]=None


class B2CResponse(MpesaBaseModel):
    conversation_id: str
    originator_conversation_id: str
    response_code: str
    response_description: str

class B2CReferenceItem(MpesaBaseModel):
    key: str = Field(alias="Key")
    value: str = Field(alias="Value")


class B2CCallbackResult(MpesaBaseModel):
    result_type: int
    result_code: int
    result_desc: str
    originator_conversation_id: str
    conversation_id: str
    transaction_id: str
    result_parameters: Optional[ResultParametersType] = None
    reference_data: Optional[B2CReferenceItem] = None


class B2CCallback(MpesaBaseModel):
    result: B2CCallbackResult





# --- Account Balance & Status ---

class AccountBalanceRequest(MpesaBaseModel):
    identifier_type: BalanceIdentifierType
    remarks: str
    result_url: AnyUrl
    queue_timeout_url: AnyUrl

class AccountBalanceResponse(MpesaBaseModel):
    conversation_id: str
    originator_conversation_id: str
    response_code: str
    response_description: str

class AccountBalanceCallback(MpesaBaseModel):
    result: CallbackResult


class GeneralTransactionStatusRequest(MpesaBaseModel):
    transaction_id: str
    party_a: Optional[str]=None
    identidier_type:Literal["1", '2', "4"]
    remarks: Optional[str] = None
    occasion:Optional[str]=None
    result_url: Optional[str] = None
    timeout_url:Optional[str]=None


class GeneralTransactionStatusResponse(MpesaBaseModel):
    conversation_id: str
    originator_conversation_id: str
    responce_code: str
    response_description: str

class TransactionStatusCallback(MpesaBaseModel):
    result: CallbackResult



class TransactionStatusResponse(MpesaBaseModel):
    response_code:str
    response_description:str
    merchant_request_id:str
    checkout_request_id:str
    result_code:str
    result_desc:str


class TransactionStatusRequest(MpesaBaseModel):
    checkout_request_id:str

# --- Reversal ---

class ReversalRequest(MpesaBaseModel):
    transaction_id: str
    amount: float
    receiver_party: str
    receiver_identifier_type: Literal["1", "2", "4", "11"]
    remarks: str
    occasion: Optional[str] = None
    result_url: AnyUrl
    queue_timeout_url: AnyUrl



class ReversalResponse(MpesaBaseModel):
    conversation_id: str
    originator_conversation_id: str
    response_code: str
    response_description: str

class ReversalCallback(MpesaBaseModel):
    result: CallbackResult


# --- QR Code ---

class DynamicQRRequest(MpesaBaseModel):
    merchant_name: str
    ref_no: str
    amount: float
    transaction_type: Literal["BG", "WA", "PB", "SM"]
    credit_party_identifier: str  # Credit Party Identifier
    size: Optional[Literal["300", "500"]] = None # QrCode Size in pixels

class DynamicQRResponse(MpesaBaseModel):
    response_code: str
    response_description: str
    qr_code: str