from pydantic import AnyUrl, ConfigDict
from typing import Literal, Field, List, Union, Optional
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
    key: str = Field(alias="Key")
    value: Union[str, int, float] = Field(alias="Value")

class ResultParametersType(MpesaBaseModel):
    result_parameter: List[ResultParameterItem]

class CallbackResult(MpesaBaseModel):
    result_type: int
    result_code: int
    result_desc: str
    originator_conversation_id: str
    conversation_id: str
    transaction_id: str
    result_parameters: Optional[ResultParametersType] = None

# --- STK Push (M-Pesa Express) ---

class STKPushRequest(MpesaBaseModel):
    amount: float
    phone_number: str
    account_reference: str
    transaction_desc: str
    callback_url: AnyUrl

class STKPushResponse(MpesaBaseModel):
    merchant_request_id: str
    checkout_request_id: str
    response_code: str
    response_description: str
    customer_message: str

class CallbackMetadataType(MpesaBaseModel):
    item: List[ResultParameterItem]

class STKCallbackDetails(MpesaBaseModel):
    merchant_request_id: str
    checkout_request_id: str
    result_code: int
    result_desc: str
    callback_metadata: Optional[CallbackMetadataType] = None

class STKResponseBody(MpesaBaseModel):
    stk_callback: STKCallbackDetails

class STKCallback(MpesaBaseModel):
    body: STKResponseBody

# --- C2B (Customer to Business) ---

class C2BRegisterRequest(MpesaBaseModel):
    short_code: str
    response_type: Literal["Completed", "Cancelled"] = "Completed"
    confirmation_url: AnyUrl
    validation_url: AnyUrl

class C2BRegisterResponse(MpesaBaseModel):
    originator_conversation_id: str
    response_code: str
    response_description: str

class C2BCallback(MpesaBaseModel):
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
    short_code: str
    amount: float
    msisdn: str
    bill_ref_number: str
    command_id: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"]

class C2BSimulateResponse(MpesaBaseModel):
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

class B2CReferenceItem:
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

class TransactionStatusRequest(MpesaBaseModel):
    checkout_request_id:str


class TransactionStatusResponse(MpesaBaseModel):
    response_code:str
    response_description:str
    merchant_request_id:str
    checkout_request_id:str
    result_code:str
    result_desc:str

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