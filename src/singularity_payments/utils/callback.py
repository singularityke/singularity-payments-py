from ..types.mpesa import  (
    STKCallback, 
    CallbackMetadataType, 
    C2BCallback,
    B2BCallback,
    ReversalCallback, 
    TransactionStatusCallback, 
    AccountBalanceCallback
)
from typing import Optional, Callable, Any, ClassVar
import datetime
import logging
from ..types.base import MpesaBaseModel


class ParsedCallbackData(MpesaBaseModel):
    merchant_request_id:str
    checkout_request_id:str
    result_code:str
    result_description:str
    amount: Optional[float]=None
    mpesa_receipt_number: Optional[str]=None
    transaction_date: Optional[str]=None
    phone_number: Optional[str]=None
    is_success: bool
    error_message: Optional[str]=None



class ParsedC2BCallback(MpesaBaseModel):
    transaction_type:str
    transaction_id:str
    transaction_time:str
    amount:float
    business_short_code:str
    bill_ref_number:str
    invoice_number:Optional[str]=None
    msisdn:str
    first_name:Optional[str]=None
    middle_name:Optional[str]=None
    last_name:Optional[str]=None


class OnB2CResultType(MpesaBaseModel):
    is_success:bool
    transaction_id:Optional[str]=None
    amount:Optional[float]=None
    recipient_phone:Optional[str]=None
    charges:Optional[float]=None
    error_message:Optional[str]=None

class OnB2BResultType(MpesaBaseModel):
    is_success:bool
    transaction_id:Optional[str]=None
    amount:Optional[float]=None
    conversation_id:Optional[str]=None
    originator_conversation_id:Optional[str]=None
    debit_account_balance:Optional[str]=None
    transaction_completed_time:Optional[str]=None
    receiver_party_public_name:Optional[str]=None
    currency:Optional[str]=None
    error_message:Optional[str]=None


class OnAccountBalanceResultType(MpesaBaseModel):
    is_success:bool
    working_account_balance:Optional[float]=None
    available_balance:Optional[float]=None
    booked_balance:Optional[float]=None
    error_message:Optional[str]=None


class OnTransactionStatusResultType(MpesaBaseModel):
    is_success:bool
    receipt_no:Optional[str]=None
    amount:Optional[float]=None
    completed_time:Optional[str]=None
    originator_conversation_id:Optional[str]=None
    error_message:Optional[str]=None

class ParseReversalCallbackReturnType(MpesaBaseModel):
    is_success:bool
    transaction_id:Optional[str]=None
    error_message:Optional[str]

class OnReversalResultType(MpesaBaseModel):
    is_success:bool
    transaction_id:Optional[str]=None
    error_message:Optional[str]=None


class LoggerType(MpesaBaseModel):
    info:Callable[[str, Any,], Any]
    error:Callable[[str, Any], Any]
    warn:Callable[[str, Any], Any]


class ParseB2BCallbackReturnType(MpesaBaseModel):
    is_success:bool
    transaction_id:Optional[str]=None
    amount:Optional[float]=None
    conversation_id:Optional[str]=None
    originator_conversation_id:Optional[str]=None
    debit_account_balance:Optional[str]=None
    debit_party_affected_account_balance:Optional[str]=None
    transaction_completed_time:Optional[str]=None
    receiver_party_public_name:Optional[str]=None
    currency:Optional[str]=None
    error_message:Optional[str]=None

class CreateCallbackResponseReturnType(MpesaBaseModel):
    result_code:float
    result_desc:str

class ParseAccountBalanceCallbackReturnType(MpesaBaseModel):
    is_success:bool
    working_balance:Optional[float]=None
    available_balance:Optional[float]=None
    booked_balance:Optional[float]=None
    error_message:Optional[str]=None

class CallbackHandlerOptions(MpesaBaseModel):
    on_success:Optional[Callable[[ParsedCallbackData], Any]]=None,
    on_failure:Optional[Callable[[ParsedCallbackData], Any]]=None,
    on_callback:Optional[Callable[[ParsedCallbackData], Any]]=None,
    on_c2b_confirmation:Optional[Callable[[ParsedC2BCallback], Any]]=None,
    on_c2b_validation:Optional[Callable[[C2BCallback], Any]]=None,
    on_b2c_result:Optional[Callable[[OnB2CResultType], Any]]=None,
    on_b2b_result:Optional[Callable[[OnB2BResultType], Any]]=None,
    on_account_balance_result:Optional[Callable[[OnAccountBalanceResultType], Any]]=None,
    on_transaction_status_result:Optional[Callable[[OnTransactionStatusResultType], Any]]=None,
    on_reversal_result:Optional[Callable[[OnReversalResultType], Any]]=None,
    validate_ip:Optional[bool]=None,
    allowed_ips:Optional[list[str]]=None,
    is_duplicate:Optional[Callable[[str],bool]]=None,
    logger:Optional[LoggerType]=None
    
        



class MpesaCallbackHandler(MpesaBaseModel):
    logger:ClassVar[logging.Logger] = logging.getLogger(__name__)   
    options: CallbackHandlerOptions 
    
    SAFARICOM_IPS: ClassVar[list[str]] = [
        "196.201.214.200", "196.201.214.206", "196.201.213.114",
        "196.201.214.207", "196.201.214.208", "196.201.213.44",
        "196.201.212.127", "196.201.212.138", "196.201.212.129",
        "196.201.212.136", "196.201.212.74", "196.201.212.69",
    ]

    def model_post_init(self, __context):
        """
        Initialize the callback handler, merging default options with user-provided options.

        This method is called after model initialization to ensure all options are set.
        """
        # If AllowedIps is empty, use the Safaricom defaults
        if not self.Options.AllowedIps:
            self.Options.AllowedIps = self.SAFARICOM_IPS


    def validate_callback_ip(self, ip_address: str) -> bool:
        """
        Validate if the provided IP address is allowed to send callbacks.

        Args:
            ip_address (str): The IP address to validate.

        Returns:
            bool: True if the IP is allowed, False otherwise.
        """
        if self.options.validate_ip is None:
            return True
        allowed_ips = self.options.allowed_ips or self.SAFARICOM_IPS
        return ip_address in allowed_ips
    
    def parse_callback(self, callback: STKCallback) -> ParsedCallbackData:
        """
        Parse an STK callback and extract relevant transaction data.

        Args:
            callback (STKCallback): The STK callback object received from M-Pesa.

        Returns:
            ParsedCallbackData: Parsed callback data with transaction details.
        """
        stk_callback = callback.body.stk_callback
        parsed = ParsedCallbackData(
            merchant_request_id=stk_callback.merchant_request_id,
            checkout_request_id=stk_callback.checkout_request_id,
            result_code=stk_callback.result_code,
            result_description=stk_callback.result_description,
            is_success=stk_callback.result_code == 0,
            error_message=stk_callback.result_description if stk_callback.result_code != 0 else None
        )
        if stk_callback.result_code == 0 and stk_callback.callback_metadata:
            metadata = self.extract_metadata(stk_callback.callback_metadata)
            parsed = parsed.model_copy(update=metadata)
        return parsed
    

    # Parse C2B callback data
    def parse_c2b_callback(self, callback: C2BCallback) -> ParsedC2BCallback:
        """
        Parse a C2B (Customer to Business) callback and extract transaction details.

        Args:
            callback (C2BCallback): The C2B callback object received from M-Pesa.

        Returns:
            ParsedC2BCallback: Parsed C2B callback data with transaction details.
        """
        return ParsedC2BCallback(
            transaction_type=callback.transaction_type,
            transaction_id=callback.trans_id,
            transaction_time=callback.trans_time,
            amount=float(callback.trans_amount),
            business_short_code=callback.business_short_code,
            bill_ref_number=callback.bill_ref_number,
            invoice_number=callback.invoice_number,
            msisdn=callback.msisdn,
            first_name=callback.first_name,
            middle_name=callback.middle_name,
            last_name=callback.last_name
        )
    

    def _extract_metadata(self, metadata: CallbackMetadataType) -> dict:
        """
        Extract transaction metadata from an STK callback.

        Args:
            metadata (CallbackMetadataType): The callback metadata object.

        Returns:
            dict: Extracted metadata as a dictionary (amount, receipt number, date, phone number).
        """
        result = {}
        for item in metadata.Item:
            name = item.Name
            value = item.Value
            if name == "Amount":
                result["amount"] = float(value)
            elif name == "MpesaReceiptNumber":
                result["mpesa_receipt_number"] = str(value)
            elif name == "TransactionDate":
                result['transaction_date'] = str(value)
            elif name == "PhoneNumber":
                result['phone_number'] = str(value)
        return result
    

    def _format_transaction_date(date_str: str) -> str:
        """
        Format a transaction date string from 'YYYYMMDDHHMMSS' to ISO format.

        Args:
            date_str (str): The date string to format.

        Returns:
            str: The formatted date string in ISO format, or the original if parsing fails.
        """
        try:
            dt = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            return dt.isoformat()
        except ValueError:
            return date_str  # Return original if parsing fails
        

    def is_success(data: ParsedCallbackData) -> bool:
        """
        Check if the transaction was successful.

        Args:
            data (ParsedCallbackData): Parsed callback data.

        Returns:
            bool: True if the transaction was successful, False otherwise.
        """
        return data.result_code == 0
    
    def is_failure(data: ParsedCallbackData) -> bool:
        """
        Check if the transaction was a failure.

        Args:
            data (ParsedCallbackData): Parsed callback data.

        Returns:
            bool: True if the transaction was a failure, False otherwise.
        """
        return data.result_code != 0
    

    def get_error_message(result_code: int) -> str:
        """
        Get a human-readable error message for a given M-Pesa result code.

        Args:
            result_code (int): The M-Pesa API result code.

        Returns:
            str: The corresponding error message.
        """
        error_messages = {
            "0": "Success",
            "1": "Insufficient Funds in Mpesa account",
            "17": "User cancelled the transaction",
            "26": "System internal error",
            "1001": "Unable to lock subscriber, a transaction is already in process",
            "1019": "Transaction expired. No response from user",
            "1032": "Request cancelled by user",
            "1037": "Timeout in sending PIN request",
            "2001": "Wrong PIN entered",
            "9999": "Request cancelled by user"
        }
        return error_messages.get(str(result_code), f"Transaction failed with code: {str(result_code)}")
     

    async def handle_callback(self, callback: STKCallback, ip_address: Optional[str] = None) -> Any:
        """
        Handle an incoming STK callback, including IP validation, duplicate checking, and event dispatch.

        Args:
            callback (STKCallback): The STK callback object.
            ip_address (Optional[str]): The IP address of the incoming request.

        Returns:
            Any: The result of the callback handling process.
        """
        # Validate IP if provided
        if ip_address and not self.validate_callback_ip(ip_address):
            self.logger.warning(f"Invalid callback IP address: {ip_address}")
            raise Exception(f"Invalid callback IP address: {ip_address}")
        # Parse the callback
        parsed = self.parse_callback(callback)
        self.logger.info("Processing STK callback", {
            "checkout_request_id": parsed.checkout_request_id,
            "result_code": parsed.result_code,
        })
        # Check for duplicates if handler provided
        if self.options.is_duplicate:
            is_dupe = await self.options.is_duplicate(parsed.checkout_request_id)
            if is_dupe:
                self.logger.warning("Duplicate callback detected for CheckoutRequestID", {parsed.checkout_request_id})
                return  # silently ignore duplicate
        # Call the general callback handler if provided
        if self.options.on_callback:
            await self.options.on_callback(parsed)
        # Call specific handlers based on success/failure
        if self.is_success(parsed) and self.options.on_success:
            await self.options.on_success(parsed)
        elif self.is_failure(parsed) and self.options.on_failure:
            await self.options.on_failure(parsed)



    async def handle_c2b_validation(self, callback: C2BCallback) -> bool:
        """
        Handle a C2B validation request, dispatching to the appropriate handler if provided.

        Args:
            callback (C2BCallback): The C2B callback object.

        Returns:
            bool: True if the transaction is accepted, False otherwise.
        """
        self.logger.info("Processing C2B validation", {
            "transaction_id": callback.trans_id,
        })
        if self.options.on_c2b_validation:
            return await self.options.on_c2b_validation(
                self.parse_c2b_callback(callback)
            )
        # Default: accept all transactions
        return True
    


    async def handle_c2b_confirmation(self, callback: C2BCallback) -> Any:
        """
        Handle a C2B confirmation request, dispatching to the appropriate handler if provided.

        Args:
            callback (C2BCallback): The C2B callback object.

        Returns:
            Any: The result of the confirmation handler, if any.
        """
        self.logger.info("Processing C2B confirmation", {
            "transaction_id": callback.trans_id,
        })
        if self.options.on_c2b_confirmation:
            await self.options.on_c2b_confirmation(
                self.parse_c2b_callback(callback)
            )

        # parse B2C callback data
    def parse_b2c_callback(self, callback: B2BCallback) -> OnB2CResultType:
        """
        Parse a B2C (Business to Customer) callback and extract transaction details.

        Args:
            callback (B2BCallback): The B2C callback object.

        Returns:
            OnB2CResultType: Parsed B2C callback data with transaction details.
        """
        result = callback.result
        parsed = {
            "is_success": result.result_code == 0,
            "error_message": self.get_error_message(result.result_code) if result.result_code != 0 else None,
        }
        if result.result_code == 0 and result.result_parameters:
            for param in result.result_parameters.result_parameter:
                key = param.key
                value = param.value
                if key == "TransactionReceipt":
                    parsed["transaction_id"] = str(value)
                elif key == "TransactionAmount":
                    parsed["amount"] = float(value)
                elif key == "ReceiverPartyPublicName":
                    parsed["recipient_phone"] = str(value)
                elif key == "B2CChargesPaidAccountAvailableFunds":
                    parsed["charges"] = float(value)
        return OnB2CResultType(**parsed)
        


    def parse_b2b_callback(self, callback: B2BCallback) -> ParseB2BCallbackReturnType:
        """
        Parse a B2B (Business to Business) callback and extract transaction details.

        Args:
            callback (B2BCallback): The B2B callback object.

        Returns:
            ParseB2BCallbackReturnType: Parsed B2B callback data with transaction details.
        """
        result = callback.result
        parsed = {
            "is_success": result.result_code == 0,
            "transaction_id": result.transaction_id,
            "conversation_id": result.conversation_id,
            "originator_conversation_id": result.originator_conversation_id,
            "error_message": self.get_error_message(result.result_code) if result.result_code != 0 else None,
        }
        if result.result_code == 0 and result.result_parameters:
            for param in result.result_parameters.result_parameter:
                key = param.key
                value = param.value
                if key == "Amount":
                    parsed["amount"] = float(value)
                elif key == "DebitAccountBalance":
                    parsed["debit_account_balance"] = str(value)
                elif key == "DebitPartyAffectedAccountBalance":
                    parsed["debit_party_affected_account_balance"] = str(value)
                elif key == "TransactionCompletedDateTime":
                    parsed["transaction_completed_time"] = self._format_transaction_date(str(value))
                elif key == "ReceiverPartyPublicName":
                    parsed["receiver_party_public_name"] = str(value)
                elif key == "Currency":
                    parsed["currency"] = str(value)
        return ParseB2BCallbackReturnType(**parsed)
            


    def parse_account_balance_callback(self, callback: AccountBalanceCallback) -> ParseAccountBalanceCallbackReturnType:
        """
        Parse an account balance callback and extract balance details.

        Args:
            callback (AccountBalanceCallback): The account balance callback object.

        Returns:
            ParseAccountBalanceCallbackReturnType: Parsed account balance data.
        """
        result = callback.result
        parsed = {
            "is_success": result.result_code == 0,
            "error_message": self.get_error_message(result.result_code) if result.result_code != 0 else None,
        }
        if result.result_code == 0 and result.result_parameters:
            for param in result.result_parameters.result_parameter:
                key = param.key
                value = param.value
                if key == "WorkingAccountAvailableFunds":
                    parsed["working_balance"] = float(value)
                elif key == "AvailableBalance":
                    parsed["available_balance"] = float(value)
                elif key == "BookedBalance":
                    parsed["booked_balance"] = float(value)
        return ParseAccountBalanceCallbackReturnType(**parsed)
            

    def parse_transaction_status_callback(self, callback: TransactionStatusCallback) -> OnTransactionStatusResultType:
        """
        Parse a transaction status callback and extract status details.

        Args:
            callback (TransactionStatusCallback): The transaction status callback object.

        Returns:
            OnTransactionStatusResultType: Parsed transaction status data.
        """
        result = callback.result
        parsed = {
            "is_success": result['result_code'] == 0,
            "originator_conversation_id": self.originator_conversation_id,
            "error_message": self.get_error_message(result.result_code) if result.result_code != 0 else None,
        }
        if result.result_code == 0 and result.result_parameters:
            for param in result.result_parameters.result_parameter:
                key = param.key
                value = param.value
                if key == "ReceiptNo":
                    parsed["receipt_no"] = str(value)
                elif key == "Amount":
                    parsed["amount"] = float(value)
                elif key == "FinalisedTime":
                    parsed["completed_time"] = str(value)  # might need to use _format_date function here
                elif key == "InitiatedTime":
                    parsed["initiated_time"] = str(value)  # might need to use _format_date function here
        return OnTransactionStatusResultType(**parsed)
            

    

    def parse_reversal_callback(self, callback: ReversalCallback) -> ParseReversalCallbackReturnType:
        """
        Parse a reversal callback and extract reversal details.

        Args:
            callback (ReversalCallback): The reversal callback object.

        Returns:
            ParseReversalCallbackReturnType: Parsed reversal callback data.
        """
        result = callback.result
        return ParseReversalCallbackReturnType(
            is_success=result.result_code == 0,
            transaction_id=result.transaction_id,
            error_message=self.get_error_message(result.result_code) if result.result_code != 0 else None,
        )
            
    

    def create_callback_response(self, success: bool = True, message: Optional[str] = None) -> CreateCallbackResponseReturnType:
        """
        Create a standard callback response for M-Pesa API integrations.

        Args:
            success (bool, optional): True if the transaction was successful, False otherwise. Defaults to True.
            message (Optional[str], optional): Optional message to include in the response. Defaults to None.

        Returns:
            CreateCallbackResponseReturnType: The callback response object with result code and description.
        """
        return CreateCallbackResponseReturnType(result_code=0 if success else 1, result_desc=message or ("Accepted" if success else "Rejected"))
    


            






    

