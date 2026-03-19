from pydantic import BaseModel, AnyUrl
from typing import Literal, List, Union, Optional

class STKPushRequest(BaseModel):
    amount: float
    phone_number: str
    account_reference: str
    transaction_description: str
    callback_url: AnyUrl = None

class STKPushResponse(BaseModel):
    merchant_request_id: str
    checkout_request_id: str
    response_code: str
    response_description: str
    customer_message: str



class TransactionStatusRequest(BaseModel):
    checkout_request_id: str



class TransactionStatusResponse(BaseModel):
    response_code: str
    response_description: str
    merchant_request_id: str
    checkout_request_id: str
    result_code: str
    result_description: str



class C2BRegisterRequest(BaseModel):
    short_code: str
    response_type: str = "Completed" or "Cancelled"
    confirmation_url: AnyUrl
    validation_url: AnyUrl


class Item(BaseModel):
    name: str
    value: str | float

class CallbackMetadata(BaseModel):
    items: list[Item]
  

# export interface STKCallback {
#   Body: {
#     stkCallback: {
#       MerchantRequestID: string;
#       CheckoutRequestID: string;
#       ResultCode: number;
#       ResultDesc: string;
#       CallbackMetadata?: CallbackMetadata;
#     };
#   };
# }

class stkCallbackType(BaseModel):
    merchant_request_id: str
    checkout_request_id: str
    result_code: int
    result_desc: str
    callback_metadata: CallbackMetadata = None

class STKCallback(BaseModel):
    Body: dict[str, stkCallbackType]


class C2BCallback(BaseModel):
    transaction_type: str
    trans_id: str
    trans_time: str
    trans_amount: str
    business_short_code: str
    bill_ref_number: str
    invoice_number: str = None
    org_account_balance: str = None
    third_party_trans_id: str = None
    msisdn: str
    first_name: str = None
    middle_name: str = None
    last_name: str = None



class C2BRegisterResponse(BaseModel):
    originator_conversation_id: str
    response_code: str
    response_description: str


# B2C (Business to Customer) Types





B2BCommmandID = Literal[
    "BusinessPayBill",
    "BusinessBuyGoods",
    "DisburseFundsToBusiness",
    "BusinessToBusinessTransfer",
    "MerchantToMerchantTransfer"
]


BalanceIdentifierType = Literal["1", "2", "4"] #1=MSISDN, 2=Till, 4=Paybill

class B2BRequest(BaseModel):
    amount: float
    party_b:str
    commandId:B2BCommmandID
    sender_identifier_type:BalanceIdentifierType
    receiver_identifier_type:BalanceIdentifierType
    remarks:str
    account_reference:str
    result_url: str = None
    timeout_url: str = None



class B2BResponse(BaseModel):
    conversation_ID: str
    originator_conversation_ID:str
    response_code:str
    response_description:str

class ResultParameterItem(BaseModel):
    key: str
    value: Union[str, int, float]

class ResultParameters(BaseModel):
    result_parameter: List[ResultParameterItem]

class B2BCallbackResult(BaseModel):
    result_type:int
    result_code:int
    result_desc:str
    originator_conversation_id:str
    conversation_id:str
    transaction_id:str
    result_parameters:Optional[ResultParameters] = None



class B2BCallback(BaseModel):
    result:B2BCallbackResult



class AccountBalanceRequest(BaseModel):
    party_a:Optional[str] = None
    identifier_type:BalanceIdentifierType = None
    remarks:Optional[str] = None
    result_url:Optional[str] = None
    timeout_url:Optional[str] = None



class AccountBalanceResponse(BaseModel):
    conversation_id:str
    originator_conversation_id:str
    response_code:str
    response_description:str

class AccountBalanceCallback(BaseModel):
    result:B2BCallbackResult # I reused it here



class GeneralTransactionStatusRequest(BaseModel):
    transaction_id:str
    party_a:Optional[str] = None
    identifier_type:Optional[BalanceIdentifierType] = None
    remarks:Optional[str] = None
    occasion:Optional[str] = None
    result_url:Optional[str] = None
    timeouturl:Optional[str] = None



class GeneralTransactionStatusResponse(BaseModel):
    conversation_id:str
    originator_conversation_id:str
    response_code:str
    response_description:str

class TransactionStatusCallback(BaseModel):
    result:B2BCallbackResult # I reused it here


class ReversalRequest(BaseModel):
    transaction_id:str
    amount:float
    receiver_party:Optional[str]=None
    receiver_identifier_type:Literal["1,", "2", "4", "11" ] = None
    remarks:Optional[str]=None
    occassion:Optional[str]=None
    result_url:Optional[str] = None
    timeout_url:Optional[str] = None


class ReversalResponse(BaseModel):
    conversation_id:str
    originator_conversation_id:str
    response_code:str
    response_description:str

class ReversalCallback(BaseModel):
    result:B2BCallbackResult # I reused it here


class DynamicQRRequest(BaseModel):
    merchant_name:str
    ref_no:str
    amount:float
    transaction_type:Literal["BG", "WA", "PB", "SM"] # BuyGoods, Withdraw, Paybill, SendMoney
    credit_party_identifier:str # Till or Paybill number
    size:Literal["300", "500"] = None # QrCode in pixesl



class DynamicQRResponse(BaseModel):
    response_code:str
    response_description:str
    qrcode:str # Base64 encoded image

class C2BSimulateRequest(BaseModel):
    short_code:str =None
    amount:float
    phone_number:str
    bill_ref_number:str
    command_id:Literal["CustomerPaybillOnline", "CustomerBuyGoodsOnline"]


class C2BSimulateResponse(BaseModel):
    conversation_id:str
    originator_conversation_id:str
    response_description:str