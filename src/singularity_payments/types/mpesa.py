from pydantic import BaseModel, AnyUrl


class STKPushRequest(BaseModel):
    amount: float
    phone_number: str
    account_reference: str
    transaction_desc: str
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
    result_desc: str



class C2BRegisterRequest(BaseModel):
    short_code: str
    response_type: str = "Completed" or "Cancelled"
    confirmation_url: AnyUrl
    validation_url: AnyUrl


class Item(BaseModel):
    Name: str
    Value: str | float

class CallbackMetadata(BaseModel):
    Item: list[Item]
  

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


class B2CCommandID(str):
    BusinessPayment = "BusinessPayment"
    SalaryPayment = "SalaryPayment"
    PromotionPayment = "PromotionPayment"



class B2CRequest(BaseModel):
    amount: float
    phone_number: str
    command_id: B2CCommandID
    remarks: str
    occasion: str = None
    result_url: AnyUrl = None
    timeout_url: AnyUrl = None



class B2CResponse(BaseModel):
    conversation_id: str
    originator_conversation_id: str
    response_code: str
    response_description: str


class B2CCallbackResultParameters(BaseModel):
    key: str
    value: str | float

class B2CCallbackReferenceItem(BaseModel):
    key: str
    value: str | float

class B2CCallbackResult(BaseModel):
    result_type: int
    result_code: int
    result_desc: str
    originator_conversation_id: str
    conversation_id: str
    transaction_id: str
    result_parameters: list[B2CCallbackResultParameters] = None
    reference_data: B2CCallbackReferenceItem = None