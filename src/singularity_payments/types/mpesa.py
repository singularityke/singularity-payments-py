from pydantic import Field
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
    name: str = Field(alias="Name")
    value: Union[str, int, float] = Field(alias="Value")

class ResultParametersType(MpesaBaseModel):
    """
    Represents a list of result parameter items in M-Pesa API responses.

    Attributes:
        result_parameter (List[ResultParameterItem]): List of result parameter items.
    """
    result_parameter: List[ResultParameterItem] = Field(alias="ResultParamter")

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
    result_type: int= Field(alias="ResultType")
    result_code: int= Field(alias="ResultCode")
    result_desc: str= Field(alias="ResultDesc")
    originator_conversation_id: str= Field(alias="OriginatorConversationID")
    conversation_id: str= Field(alias="ConversationID")
    transaction_id: str= Field(alias="TransactionID")
    result_parameters: Optional[ResultParametersType] = Field(None,alias="ResultParameters")

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
    phone_number: str= Field(alias="phoneNumber")
    account_reference: str= Field(alias="accountReference")
    transaction_desc: str= Field(alias="transactionDescription")
    callback_url: Optional[str]= Field(None, alias="callbackUrl")

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
    merchant_request_id: str= Field(alias="MerchantRequestID")
    checkout_request_id: str= Field(alias="CheckoutRequestID")
    response_code: str= Field(alias="ResponseCode")
    response_description: str= Field(alias="ResponseDescription")
    customer_message: str= Field(alias="CustomerMessage")
    

class CallbackMetadataType(MpesaBaseModel):
    """
    Metadata section of an STK callback, containing additional transaction details.

    Attributes:
        item (List[ResultParameterItem]): List of metadata items.
    """
    item: List[ResultParameterItem]= Field(alias="Item")

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
    merchant_request_id: str= Field(alias="MerchantRequestID")
    checkout_request_id: str= Field(alias="CheckoutRequestID")
    result_code: int= Field(alias="ResultCode")
    result_desc: str= Field(alias="ResultDesc")
    callback_metadata: Optional[CallbackMetadataType] = Field(None, alias="CallbackMetadata")

class STKResponseBody(MpesaBaseModel):
    """
    Body of an STK callback, containing the callback details.

    Attributes:
        stk_callback (STKCallbackDetails): The callback details.
    """
    stk_callback: STKCallbackDetails= Field(alias="stkCallback")

class STKCallback(MpesaBaseModel):
    """
    Top-level model for an STK callback received from the M-Pesa API.

    Attributes:
        body (STKResponseBody): The body of the callback.
    """
    body: STKResponseBody= Field(alias="Body")

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
    short_code: str= Field(alias="shortCode")
    response_type: Literal["Completed", "Cancelled"] = Field(alias="ResponseType")
    confirmation_url: str = Field(alias="confirmationURL")
    validation_url: str= Field(alias="validationURL")

class C2BRegisterResponse(MpesaBaseModel):
    """
    Response model for a C2B registration request.

    Attributes:
        originator_conversation_id (str): Originator conversation ID.
        response_code (str): Response code from the API.
        response_description (str): Description of the response.
    """
    originator_conversation_id: str = Field(alias="OriginatorConversationID")
    response_code: str= Field(alias="ResponseCode")
    response_description: str= Field(alias="ResultDescription")

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
    transaction_type: str= Field(alias="TransactionType")
    trans_id: str= Field(alias="TransID")
    trans_time: str= Field(alias="TransTime")
    trans_amount: str= Field(alias="TransAmount")
    business_short_code: str= Field(alias="BusinessShortCode")
    bill_ref_number: str= Field(alias="BillRefNumber")
    invoice_number: Optional[str] = Field(None, alias="InvoiceNumber")
    org_account_balance: Optional[str] = Field(None, alias="OrgAccountBalance")
    third_party_trans_id: Optional[str] = Field(None, alias="ThirdPartyTransID")
    msisdn: str= Field(alias="MSISDN")
    first_name: Optional[str] = Field(None, alias="FirstName")
    middle_name: Optional[str] = Field(None, alias="MiddleName")
    last_name: Optional[str] = Field(None, alias="LastName")

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
    short_code: str= Field(alias="ShortCode")
    amount: float= Field(alias="Amount")
    msisdn: str= Field(alias="MSISDN")
    bill_ref_number: str= Field(alias="BillRefNumber")
    command_id: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"]= Field(alias="CommandID")

class C2BSimulateResponse(MpesaBaseModel):
    """
    Response model for a C2B simulation request.

    Attributes:
        conversation_id (str): Conversation ID.
        originator_conversation_id (str): Originator conversation ID.
        response_description (str): Description of the response.
    """
    conversation_id: str= Field(alias="ConversationID")
    originator_conversation_id: str= Field(alias="OriginatorConversationID")
    response_description: str= Field(alias="ResponseDescription")

# --- B2B / B2C / Reversals ---

class B2BRequest(MpesaBaseModel):
    amount: float= Field(alias="amount")
    party_b: str= Field(alias="partyB")
    command_id: B2BCommandID= Field(alias="commandID")
    sender_identifier_type: BalanceIdentifierType= Field(alias="senderIdentifierType")
    receiver_identifier_type: BalanceIdentifierType= Field(alias="receiverIdentifierType")
    remarks: str
    account_reference: str= Field(alias="accountReference")
    result_url: str= Field(alias="resultUrl")
    timeout_url: str= Field(alias="timeoutUrl")

class B2BResponse(MpesaBaseModel):
    conversation_id: str= Field(alias="ConversationID")
    originator_conversation_id: str= Field(alias="OriginatorConversationID")
    response_code: str= Field(alias="ResponseCode")
    response_description: str= Field(alias="ResponseDescription")

class B2BCallback(MpesaBaseModel):
    result: CallbackResult= Field(alias="Result")



B2CCommandID = Literal["BusinessPayment", "SalaryPayment", "PromotionPayment"]



class B2CRequest(MpesaBaseModel):
    amount:float= Field(alias="amount")
    phone_number:str= Field(alias="phoneNumber")
    command_id:B2CCommandID= Field(alias="commandID")
    remarks:str
    occasion:Optional[str]=None
    result_url:Optional[str]=Field(None, alias="resultUrl")
    timeout_url:Optional[str]=Field(None, alias="timoutUrl")


class B2CResponse(MpesaBaseModel):
    conversation_id: str= Field(alias="ConversationID")
    originator_conversation_id: str= Field(alias="OriginatorConversationID")
    response_code: str= Field(alias="ResponseCode")
    response_description: str= Field(alias="ResponseDescription")

class B2CReferenceItem(MpesaBaseModel):
    key: str = Field(alias="Key")
    value: str = Field(alias="Value")


class B2CCallbackResult(MpesaBaseModel):
    result_type: int= Field(alias="ResultType")
    result_code: int= Field(alias="ResultCode")
    result_desc: str= Field(alias="ResultDesc")
    originator_conversation_id: str= Field(alias="OriginatorConversationID")
    conversation_id: str= Field(alias="ConversationID")
    transaction_id: str= Field(alias="TransactionID")
    result_parameters: Optional[ResultParametersType] = Field(None, alias="ResultParameters")
    reference_data: Optional[B2CReferenceItem] = Field(None, alias="ReferenceData")


class B2CCallback(MpesaBaseModel):
    result: B2CCallbackResult= Field(alias="Result")





# --- Account Balance & Status ---

class AccountBalanceRequest(MpesaBaseModel):
    party_a:Optional[str]= Field(None, alias="partyA")
    identifier_type: Optional[BalanceIdentifierType]= Field(None, alias="IdentifierType")
    remarks: Optional[str]=None
    result_url: Optional[str]= Field(None,alias="resultUrl")
    timeout_url: Optional[str]= Field(None,alias="timeoutUrl")

class AccountBalanceResponse(MpesaBaseModel):
    conversation_id: str= Field(alias="ConversationID")
    originator_conversation_id: str= Field(alias="OriginatorConversationID")
    response_code: str= Field(alias="ResponseCode")
    response_description: str= Field(alias="ResponseDescription")

class AccountBalanceCallback(MpesaBaseModel):
    result: CallbackResult= Field(alias="Result")


class GeneralTransactionStatusRequest(MpesaBaseModel):
    transaction_id: str= Field(alias="TransactionID")
    party_a: Optional[str]= Field(None, alias="partyA")
    identidier_type:Optional[Literal["1", '2', "4"]]= Field(None, alias="identifierType")
    remarks: Optional[str]=None
    occasion:Optional[str]= None
    result_url: Optional[str] = Field(None, alias="resultUrl")
    timeout_url:Optional[str]= Field(None, alias="timeoutUrl")


class GeneralTransactionStatusResponse(MpesaBaseModel):
    conversation_id: str= Field(alias="ConversationID")
    originator_conversation_id: str= Field(alias="OriginatorConversationID")
    response_code: str= Field(alias="ResponseCode")
    response_description: str= Field(alias="ResponseDescription")

class TransactionStatusCallback(MpesaBaseModel):
    result: CallbackResult= Field(alias="Result")



class TransactionStatusResponse(MpesaBaseModel):
    response_code:str= Field(alias="ResponseCode")
    response_description:str= Field(alias="ResponseDescription")
    merchant_request_id:str= Field(alias="MerchantRequestID")
    checkout_request_id:str= Field(alias="CheckoutRequestID")
    result_code:str= Field(alias="ResultCode")
    result_desc:str= Field(alias="ResultDesc")


class TransactionStatusRequest(MpesaBaseModel):
    checkout_request_id:str= Field(alias="CheckoutRequestID")

# --- Reversal ---

class ReversalRequest(MpesaBaseModel):
    transaction_id: str= Field(alias="transactionID")
    amount: float
    receiver_party: Optional[str]= Field(None,alias="receiverParty")
    receiver_identifier_type: Optional[Literal["1", "2", "4", "11"]]= Field(None,alias="receiverIdentifierType")
    remarks: Optional[str]= None
    occasion: Optional[str] = None
    result_url: Optional[str]= Field(None, alias="resultUrl")
    timeout_url: Optional[str]= Field(None, alias="timeoutUrl")



class ReversalResponse(MpesaBaseModel):
    conversation_id: str= Field(alias="ConversationID")
    originator_conversation_id: str= Field(alias="OriginatorConversationID")
    response_code: str= Field(alias="ResponseCode")
    response_description: str= Field(alias="ResponseDescription")

class ReversalCallback(MpesaBaseModel):
    result: CallbackResult= Field(alias="Result")


# --- QR Code ---

class DynamicQRRequest(MpesaBaseModel):
    merchant_name: str= Field(alias="merchantName")
    ref_no: str= Field(alias="refNo")
    amount: float
    transaction_type: Literal["BG", "WA", "PB", "SM"]= Field(alias="transactionType") #  BuyGoods, Withdraw, Paybill, SendMoney
    credit_party_identifier: str= Field(alias="creditPartyIdentifier")  # Credit Party Identifier
    size: Optional[Literal["300", "500"]]=None  # QrCode Size in pixels

class DynamicQRResponse(MpesaBaseModel):
    response_code: str= Field(alias="ResponseCode")
    response_description: str= Field(alias="ResponseDescription")
    qr_code: str= Field(alias="QRCode")