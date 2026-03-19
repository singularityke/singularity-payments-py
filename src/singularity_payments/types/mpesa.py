from pydantic import BaseModel, AnyUrl, ConfigDict
from typing import Literal, Field, List, Union, Optional

# --- Shared Types ---

B2BCommandID = Literal[
    "BusinessPayBill",
    "BusinessBuyGoods",
    "DisburseFundsToBusiness",
    "BusinessToBusinessTransfer",
    "MerchantToMerchantTransfer"
]

BalanceIdentifierType = Literal["1", "2", "4"]  # 1=MSISDN, 2=Till, 4=Paybill

class ResultParameterItem(BaseModel):
    key: str
    value: Union[str, int, float]

class ResultParametersType(BaseModel):
    result_parameter: List[ResultParameterItem]

class CallbackResult(BaseModel):
    result_type: int
    result_code: int
    result_desc: str
    originator_conversation_id: str
    conversation_id: str
    transaction_id: str
    result_parameters: Optional[ResultParametersType] = None

# --- STK Push (M-Pesa Express) ---

class STKPushRequest(BaseModel):
    amount: float
    phone_number: str
    account_reference: str
    transaction_desc: str
    callback_url: AnyUrl

class STKPushResponse(BaseModel):
    merchant_request_id: str
    checkout_request_id: str
    response_code: str
    response_description: str
    customer_message: str

class CallbackMetadataType(BaseModel):
    item: List[ResultParameterItem]

class STKCallbackDetails(BaseModel):
    merchant_request_id: str
    checkout_request_id: str
    result_code: int
    result_desc: str
    callback_metadata: Optional[CallbackMetadataType] = None

class STKResponseBody(BaseModel):
    stk_callback: STKCallbackDetails

class STKCallback(BaseModel):
    body: STKResponseBody

# --- C2B (Customer to Business) ---

class C2BRegisterRequest(BaseModel):
    short_code: str
    response_type: Literal["Completed", "Cancelled"] = "Completed"
    confirmation_url: AnyUrl
    validation_url: AnyUrl

class C2BRegisterResponse(BaseModel):
    originator_conversation_id: str
    response_code: str
    response_description: str

class C2BCallback(BaseModel):
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

class C2BSimulateRequest(BaseModel):
    short_code: str
    amount: float
    msisdn: str
    bill_ref_number: str
    command_id: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"]

class C2BSimulateResponse(BaseModel):
    conversation_id: str
    originator_conversation_id: str
    response_description: str

# --- B2B / B2C / Reversals ---

class B2BRequest(BaseModel):
    amount: float
    party_b: str
    command_id: B2BCommandID
    sender_identifier_type: BalanceIdentifierType
    receiver_identifier_type: BalanceIdentifierType
    remarks: str
    account_reference: str
    result_url: AnyUrl
    queue_timeout_url: AnyUrl

class B2BResponse(BaseModel):
    conversation_id: str
    originator_conversation_id: str
    response_code: str
    response_description: str

class B2BCallback(BaseModel):
    result: CallbackResult

# --- Account Balance & Status ---

class AccountBalanceRequest(BaseModel):
    identifier_type: BalanceIdentifierType
    remarks: str
    result_url: AnyUrl
    queue_timeout_url: AnyUrl

class AccountBalanceResponse(BaseModel):
    conversation_id: str
    originator_conversation_id: str
    response_code: str
    response_description: str

class TransactionStatusRequest(BaseModel):
    transaction_id: str
    identifier_type: BalanceIdentifierType
    remarks: str
    occasion: Optional[str] = None
    result_url: AnyUrl
    queue_timeout_url: AnyUrl

# --- Reversal ---

class ReversalRequest(BaseModel):
    transaction_id: str
    amount: float
    receiver_party: str
    receiver_identifier_type: Literal["1", "2", "4", "11"]
    remarks: str
    occasion: Optional[str] = None
    result_url: AnyUrl
    queue_timeout_url: AnyUrl

# --- QR Code ---

class DynamicQRRequest(BaseModel):
    merchant_name: str
    ref_no: str
    amount: float
    trx_code: Literal["BG", "WA", "PB", "SM"]
    cpi: str  # Credit Party Identifier
    size: Optional[Literal["300", "500"]] = None

class DynamicQRResponse(BaseModel):
    response_code: str
    response_description: str
    qr_code: str