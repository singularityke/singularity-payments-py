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
    Key: str
    Value: Union[str, int, float]

class ResultParametersType(BaseModel):
    ResultParameter: List[ResultParameterItem]

class CallbackResult(BaseModel):
    ResultType: int
    ResultCode: int
    ResultDesc: str
    OriginatorConversationID: str
    ConversationID: str
    TransactionID: str
    ResultParameters: Optional[ResultParametersType] = None

# --- STK Push (M-Pesa Express) ---

class STKPushRequest(BaseModel):
    Amount: float
    PhoneNumber: str
    AccountReference: str
    TransactionDesc: str
    CallbackUrl: AnyUrl

class STKPushResponse(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResponseCode: str
    ResponseDescription: str
    CustomerMessage: str

class CallbackMetadataType(BaseModel):
    Item: List[ResultParameterItem]

class STKCallbackDetails(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[CallbackMetadataType] = None

class STKResponseBody(BaseModel):
    stkCallback: STKCallbackDetails

class STKCallback(BaseModel):
    Body: STKResponseBody

# --- C2B (Customer to Business) ---

class C2BRegisterRequest(BaseModel):
    ShortCode: str
    ResponseType: Literal["Completed", "Cancelled"] = "Completed"
    ConfirmationURL: AnyUrl
    ValidationURL: AnyUrl

class C2BRegisterResponse(BaseModel):
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str

class C2BCallback(BaseModel):
    TransactionType: str
    TransID: str
    TransTime: str
    TransAmount: str
    BusinessShortCode: str
    BillRefNumber: str
    InvoiceNumber: Optional[str] = None
    OrgAccountBalance: Optional[str] = None
    ThirdPartyTransID: Optional[str] = None
    MSISDN: str
    FirstName: Optional[str] = None
    MiddleName: Optional[str] = None
    LastName: Optional[str] = None

class C2BSimulateRequest(BaseModel):
    ShortCode: str
    Amount: float
    Msisdn: str
    BillRefNumber: str
    CommandID: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"]

class C2BSimulateResponse(BaseModel):
    ConversationID: str
    OriginatorConversationID: str
    ResponseDescription: str

# --- B2B / B2C / Reversals ---

class B2BRequest(BaseModel):
    Amount: float
    PartyB: str
    CommandID: B2BCommandID
    SenderIdentifierType: BalanceIdentifierType
    ReceiverIdentifierType: BalanceIdentifierType
    Remarks: str
    AccountReference: str
    ResultURL: AnyUrl
    QueueTimeOutURL: AnyUrl

class B2BResponse(BaseModel):
    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str

class B2BCallback(BaseModel):
    Result: CallbackResult

# --- Account Balance & Status ---

class AccountBalanceRequest(BaseModel):
    IdentifierType: BalanceIdentifierType
    Remarks: str
    ResultURL: AnyUrl
    QueueTimeOutURL: AnyUrl

class AccountBalanceResponse(BaseModel):
    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str

class TransactionStatusRequest(BaseModel):
    TransactionID: str
    IdentifierType: BalanceIdentifierType
    Remarks: str
    Occasion: Optional[str] = None
    ResultURL: AnyUrl
    QueueTimeOutURL: AnyUrl

# --- Reversal ---

class ReversalRequest(BaseModel):
    TransactionID: str
    Amount: float
    ReceiverParty: str
    ReceiverIdentifierType: Literal["1", "2", "4", "11"]
    Remarks: str
    Occasion: Optional[str] = None
    ResultURL: AnyUrl
    QueueTimeOutURL: AnyUrl

# --- QR Code ---

class DynamicQRRequest(BaseModel):
    MerchantName: str
    RefNo: str
    Amount: float
    TrxCode: Literal["BG", "WA", "PB", "SM"]
    CPI: str  # Credit Party Identifier
    Size: Optional[Literal["300", "500"]] = None

class DynamicQRResponse(BaseModel):
    ResponseCode: str
    ResponseDescription: str
    QRCode: str