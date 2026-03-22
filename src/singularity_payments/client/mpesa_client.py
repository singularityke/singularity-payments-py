
from ..types.config import MpesaConfig, MpesaPlugin
from ..utils.auth import MpesaAuth
from ..utils.callback import MpesaCallbackHandler,CallbackHandlerOptions, ParsedCallbackData
from ..types.mpesa import (
    STKPushRequest,
    STKPushResponse,
    TransactionStatusRequest,
    TransactionStatusResponse,
    C2BRegisterRequest,
    C2BRegisterResponse,
    STKCallback,
    C2BCallback,
    B2CRequest,B2CResponse,
    B2BRequest,B2BResponse,
    AccountBalanceRequest,
    AccountBalanceResponse,
    GeneralTransactionStatusRequest,
    GeneralTransactionStatusResponse,
    ReversalRequest,ReversalResponse,
    DynamicQRRequest,DynamicQRResponse,
    ReversalCallback,
    TransactionStatusCallback,
    AccountBalanceCallback,
    B2BCallback,
    B2CCallback,C2BSimulateRequest,
    C2BSimulateResponse
)
from ..utils.errors import MpesaValidationError,MpesaNetworkError
from ..utils.retry import RetryOptions 
from ..utils.ratelimiter import RateLimiter, RedisRateLimiter, RedisLike
from ..types.base import MpesaBaseModel
from typing import Optional, Any, Union
from tenacity import stop_after_attempt, AsyncRetrying, wait_exponential, retry_if_exception_type, before_sleep_log
import httpx
import logging
import math
import re


logger = logging.getLogger(__name__)

class RateLimitOptions(MpesaBaseModel):
    """
    Configuration options for rate limiting in the MpesaClient.

    Attributes:
        enabled (Optional[bool]): Whether rate limiting is enabled.
        max_requests (Optional[float]): Maximum number of requests allowed per window.
        window_ms (Optional[float]): Time window in milliseconds.
        redis (Optional[RedisLike]): Redis-like backend for distributed rate limiting.
    """
    enabled: Optional[bool] = None
    max_requests: Optional[float] = None
    window_ms: Optional[float] = None
    redis: Optional[RedisLike] = None


class MpesaClientOptions(MpesaBaseModel):
    """
    Options for configuring the MpesaClient instance.

    Attributes:
        callback_options (Optional[CallbackHandlerOptions]): Options for callback handling.
        retry_options (Optional[RetryOptions]): Options for retry logic.
        rate_limit_options (Optional[RateLimitOptions]): Options for rate limiting.
        request_timeout (Optional[float]): Request timeout in milliseconds.
    """
    callback_options: Optional[CallbackHandlerOptions] = None
    retry_options: Optional[RetryOptions] = None
    rate_limit_options: Optional[RateLimitOptions] = None
    request_timeout: Optional[float] = None


class MpesaClient(MpesaBaseModel):
    """
    Main client for interacting with the M-Pesa API.

    This class provides methods for initiating payments, querying transactions, handling callbacks, and more.

    Attributes:
        config (MpesaConfig): M-Pesa API configuration.
        _auth (MpesaAuth): Handles authentication with the M-Pesa API.
        _plugins (list[MpesaPlugin]): List of registered plugins.
        _callback_handler (MpesaCallbackHandler): Handles callback processing.
        _retry_options (RetryOptions): Retry configuration options.
        _rate_limiter (Optional[Union[RateLimiter, RedisRateLimiter]]): Rate limiter instance.
        _REQUEST_TIMEOUT (float): Request timeout in milliseconds.
    """
    config: MpesaConfig
    _auth: MpesaAuth
    _plugins: list[MpesaPlugin]
    _callback_handler: MpesaCallbackHandler
    _retry_options: RetryOptions
    _rate_limiter: Optional[Union[RateLimiter, RedisRateLimiter]] = None
    _REQUEST_TIMEOUT: float

    def __init__(self, config:MpesaConfig, options:MpesaClientOptions):
        self.config = config
        self._auth=MpesaAuth(config=config)
        self._callback_handler=MpesaCallbackHandler(options=options.callback_options)
        self._retry_options=options.retry_options or {}
        self._REQUEST_TIMEOUT=options.request_timeout or 30000
       

        rate_limit_opts = getattr(options, 'rate_limit_options', None)
        if options.rate_limit_options.enabled is None:
            rate_limit_opts = {
                'max_requests':getattr(rate_limit_opts,'max_requests', 100) or 100,
                'window_ms':getattr(rate_limit_opts, 'window_ms', 60000) or 60000,
            }

            if getattr(rate_limit_opts, "redis", None) is not None:
                self._rate_limiter = RedisRateLimiter(
                    options=rate_limit_opts.redis,
                    rate_limit_options=rate_limit_opts
                )
            else:
                self._rate_limiter = RateLimiter(options=rate_limit_opts)



    async def _make_request(
        self,
        endpoint:str,
        pay_load:Any,
        rate_limit_key:Optional[str]=None
    ):
        retrier = AsyncRetrying(
            stop=stop_after_attempt(self._retry_options.get('max_retries', 3)),
            wait=wait_exponential(multiplier=1, min=1, max=10), # Exponential backoff
            retry=retry_if_exception_type((MpesaNetworkError, httpx.TimeoutException)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True # Ensures the final error is thrown after all attempts fail
        )
        async for attempt in retrier:
            with attempt:
                if self._rate_limiter and rate_limit_key:
                    await self._rate_limiter.check_limit(rate_limit_key)

                token = await self.auth.get_access_token()
                base_url = self.auth.get_base_url()

                async with httpx.AsyncClient(timeout=self._REQUEST_TIMEOUT/1000) as client:
                    response = await client.post(
                        f"{base_url}{endpoint}",
                        json=pay_load,
                        headers={"Authorization":f"Bearer {token}"}
                    )

                    if response.status_code != 200:
                        try:
                            error_body = await response.json()
                        except Exception:
                            error_body = {}
                        raise self.parse_mpesa_api_error(
                            response.status_code,
                            error_body
                    )

                    return response.json()
    


    def _validate_and_format_phone(self, phone:str)->str:
            """
            Validate phone number format
            Args:
                phone(str):phone number to be validated

            Returns:
                formatted(str): Validated phone number
            """

            formatted = re.sub(r'[^\d]', '', phone)
            if formatted.startswith('0'):
                formatted = "254"+formatted[1:]
            elif not formatted.startswith('0'):
                formatted = "254"+formatted
            

            if not re.match(r'^254[17]\d{8}$'):
                raise MpesaValidationError(f"Invalid phone number format: {phone}. Must be a valid Kenyan number.")
            

            return formatted



    def use(self, plugin:MpesaPlugin)->"MpesaClient":
            """
            Added plugin to extend functionality.
            Args:
                plugin(MpesaPlugin): Plugin to be added

            Returns:
                self(Self): MpesaClient instance
            """

            self._plugins.append(plugin)
            plugin.init(self)
            return self
        


    async def stk_push(self, request:STKPushRequest)->STKPushResponse:
            """
                Initiate STK Push (Lipa na Mpesa Online)
                Args:
                    request(STKPushRequest): STK Push request object
                Returns:
                    response_data(STKPushResponse): STK Push response object
            """
            if request.amount < 1:
                raise MpesaValidationError("Amount must be at least 1 KES.")
            if request.account_reference is None or len(request.account_reference) > 13:
                raise MpesaValidationError("Account reference is required and must be 13 characters or less.")
            if request.transaction_desc is None:
                raise MpesaValidationError("Transaction description is required.")
            
            phone = self._validate_and_format_phone(request.phone_number)
            payload = {
                "BusinessShortCode": self.config.short_code,
                "Password": self.auth.get_password(),
                "Timestamp": self.auth.timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": math.floor(request.amount),
                "PartyA": phone,
                "PartyB":self.config.short_code,
                "PhoneNumber": phone,
                "CallBackURL": request.callback_url or self.config.callback_url,
                "AccountReference": request.account_reference,
                "TransactionDesc": request.transaction_desc
            }

            response_data = await self._make_request(
                endpoint="/mpesa/stkpush/v1/processrequest",
                pay_load=payload,
                rate_limit_key=f"stk:{phone}"
            )


            return STKPushResponse(**response_data)
        


    async def stk_query(self, request:TransactionStatusRequest)->TransactionStatusResponse:
            """
            Query STK Push transaction status
            Args:
                request(TransactionStatusRequest):request object containing checkout request id

            Returns:
                response_data(TransactionStatusResponse):response object containing transaction status details
            
            """
            if request.checkout_request_id is None:
                raise MpesaValidationError("CheckoutRequestID is required.")
            
            payload = {
                "BusinessShortCode": self.config.short_code,
                "Password": self.auth.get_password(),
                "Timestamp": self.auth.get_timestamp(),
                "CheckoutRequestID":request.checkout_request_id
            }

            response_data = self._make_request(
                endpoint="/mpesa/stkpushquery/v1/query",
                pay_load=payload,
                rate_limit_key=f"query:{request.checkout_request_id}"
            )

            return TransactionStatusResponse(**response_data)
        

    async def register_c2b_url(self, request:C2BRegisterRequest)->C2BRegisterResponse:
            """
            Register C2B URLs for validation and confirmation
            Args:
                request(C2BRegisterRequest):request object containing C2B URLs
            Returns:
                response_data(C2BRegisterResponse):response object containing success message

            """
            if request.confirmation_url is None or request.validation_url is None:
                raise MpesaValidationError("Both Confirmation URL and ValidationURL is required.")



            payload = {
                "ShortCode": request.short_code,
                "ResponseType": request.response_type,
                "ConfirmationURL": request.confirmation_url,
                "ValidationURL": request.validation_url
            }

            response_data = await self._make_request(
                  "/mpesa/c2b/v1/registerurl",
                  payload,
                  "c2b:register"
              )

            return C2BRegisterResponse(**response_data)
        


    def get_callback_handler(self)->MpesaCallbackHandler:
            """
            Get callback handler instance
            Returns:
                callback_handler(MpesaCallbackHandler): Callback handler instance
            """
            return self._callback_handler
        


    async def handle_stk_callback(
                self,
                callback:STKCallback,
                ip_address:Optional[str]=None
        )->dict:
            """
            Handle an incoming STK Push callback.
            Args:
                callback(STKCallback): STK Push callback object
                ip_address(str): IP address of the request
            Returns:
                parsed_data(ParsedCallbackData): Mpesa compliant response

            """

            try:
                await self._callback_handler.handle_callback(callback, ip_address)
                return self._callback_handler.create_callback_response(True)
            except Exception as e:
                logger.exception(f"Error handling STK callback: {e}")
                return self._callback_handler.create_callback_response(False, "Internal Error.")
            

    async def handle_c2b_validation(self, callback:C2BCallback):
            """
            Handle C2B validation request.
            Args:
                callback(C2BCallback): C2B callback object
            Returns:
                response(CreateCallbackResponseReturnType): Mpesa compliant response
            
            """
            
            try:
                is_valid= await self._callback_handler.handle_c2b_validation(callback)
                return self._callback_handler.create_callback_response(
                    is_valid,
                    "Accepted" if is_valid else "Rejected"
                )
            except Exception as e:
                logger.exception(f"C2B Validation Error: {e}")
                return self._callback_handler.create_callback_response(False, "Internal Error.")
            


    async def b2c(self, request:B2CRequest)->B2CResponse:
            """
            B2C send money from business to customer
            Args:
                request(B2CRequest): B2C request object

            Returns:
                response_data(B2CResponse): B2C response object
            
            """
            if request.amount < 10:
                raise MpesaValidationError("B2C amount must be greater than 10 KES.")
            
            if request.remarks is None or len(request.remarks) > 100:
                raise MpesaValidationError("B2C remarks must be between 1 and 100 characters.")

            phone = self.validate_and_format_phone(request.phone_number)
            payload = {
                "InitiatorName": self.config.initiator_name,
                "SecurityCredential": self.config.security_credential,
                "CommandID": request.command_id,
                "Amount": math.floor(request.amount),
                "PartyA": self.config.short_code,
                "PartyB": phone,
                "Remarks": request.remarks,
                "QueueTimeOutURL": request.timeout_url or self.config.timeout_url,
                "ResultURL":request.result_url or self.config.result_url,
                "Occasion":request.occasion or ""
            }

            response_data= await self._make_request(
                "/mpesa/b2c/v1/paymentrequest",
                payload,
                f"b2c:{phone}"
            )

            return B2CResponse(**response_data)
        


    async def b2b(self, request:B2BRequest)->B2BResponse:
            """
            B2B send money from business to business
            Args:
                request(B2BRequest): B2B request object
            Returns:
                response_data(B2BResponse): B2B response object
            """

            if request.amount < 1:
                raise MpesaValidationError("B2B amount must be greater than 0.")

            if request.remarks is None or len(request.remarks) > 100:
                raise MpesaValidationError("B2B remarks must be between 1 and 100 characters.")

            if request.account_reference is None or len(request.account_reference) > 13:
                raise MpesaValidationError("B2B account reference must be 13 characters or less.")
            

            payload = {
                "Initiator":self.config.initiator_name,
                "SecurityCredential":self.config.security_credential,
                "CommandID":request.command_id,
                "Amount":math.floor(request.amount),
                "PartyA":self.config.short_code,
                "PartyB":request.party_b,
                "SenderIdentifierType":request.sender_identifier_type,
                "ReceiverIdentifierType":request.receiver_identifier_type,
                "AccountReference":request.account_reference,
                "Remarks":request.remarks,
                "QueueTimeOutURL":request.timeout_url or self.config.timeout_url,
                "ResultURL":request.result_url or self.config.result_url
            }

            response_data = await self._make_request(
                '/mpesa/b2b/v1/paymentrequest',
                payload,
                f'b2b:{request.party_b}'
            )

            return B2BResponse(**response_data)

    async def account_balance(self, request:AccountBalanceRequest)->AccountBalanceResponse:  
                """
                Check account balance
                Args:
                    request(AccountBalanceRequest): Account balance request object
                Returns:
                    response_data(AccountBalanceResponse): Account balance response object
                """         
                payload = {
                    "Initiator":self.config.initiator_name,
                    "SecurityCredential":self.config.security_credential,
                    "CommandID":"AccountBalance",
                    "PartyA":request.party_a or self.config.short_code,
                    "IdentifierType":request.identifier_type or "4",
                    "Remarks":request.remarks or "Account balance query",
                    "QueueTimeOutURL":request.timeout_url or self.config.timeout_url,
                    "ResultURL":request.result_url or self.config.result_url,
                }

                response_data = await self._make_request(
                    "/mpesa/accountbalance/v1/query",
                    payload,
                    "balance"
                )

                return AccountBalanceResponse(**response_data)
        

    async def transaction_status(self, request:GeneralTransactionStatusRequest)->GeneralTransactionStatusResponse:
            """
            Query general transaction status
            Args:
                request(GeneralTransactionStatusRequest): General transaction status request object
            Returns:
                response_data(GeneralTransactionStatusResponse): General transaction status response object
            
            """
            if request.transaction_id is None:
                raise MpesaValidationError("Transaction ID is required.")

            payload = {
                "Initiator":self.config.initiator_name,
                "SecurityCredential":self.config.security_credential,
                "CommandID":"TransactionStatusQuery",
                "TransactionID":request.transaction_id,
                "PartyA":request.party_a or self.config.short_code,
                "IdentifierType":request.identifier_type or "4",
                "Remarks":request.remarks or "Transaction status query",
                "Occasion":request.occasion or "",
                "QueueTimeOutURL":request.timeout_url or self.config.timeout_url,
                "ResultURL":request.result_url or self.config.result_url,
            }

            response_data = await self._make_request(
                '/mpesa/transactionstatus/v1/query',
                payload,
                f"status:{request.transaction_id}"
            )

            return GeneralTransactionStatusResponse(**response_data)
        


    async def reversal(self, request:ReversalRequest)->ReversalResponse:
            if request.transaction_id is None:
                raise MpesaValidationError("Transaction ID is required.")

            if request.amount < 1:
                raise MpesaValidationError("Amount must be greater than 0.")
            
            payload = {
                "Initiator":self.config.initiator_name,
                "SecurityCredential":self.config.security_credential,
                "CommandID":"TransactionReversal",
                "TransactionID":request.transaction_id,
                "Amount":math.floor(request.amount),
                "ReceiverParty":request.receiver_party or self.config.short_code,
                "ReceiverIdentifierType":request.receiver_identifier_type or "11",
                "Remarks":request.remarks or "Transaction reversal",
                "QueueTimeOutURL":request.timeout_url or self.config.timeout_url,
                "ResultURL":request.result_url or self.config.result_url,
            }

            response_data = await self._make_request(
                '/mpesa/reversal/v1/request',
                payload,
                f"reversal:{request.transaction_id}"
            )

            return ReversalResponse(**response_data)
        


    async def generate_dynamic_qr(self, request:DynamicQRRequest)->DynamicQRResponse:
            """
            Generate dynamic QR code
            Args:
                request(DynamicQRRequest): Dynamic QR request object
            Returns:
                response_data(DynamicQRResponse): Dynamic QR response object
            
            """
            if request.merchant_name is None or len(request.merchant_name)>26:
                raise MpesaValidationError("Merchant name is required and must be 26 characters or less.")
            if request.ref_no is None or len(request.ref_no)>12:
                raise MpesaValidationError("Reference number is required and must be 12 characters or less.")
            if request.amount < 1 or request.amount>999999:
                raise MpesaValidationError("Amount must be between 1 and 999999 KES.")
            
            payload = {
                "MerchantName":request.merchant_name,
                "RefNo":request.ref_no,
                "Amount":math.floor(request.amount),
                "TrxCode":request.transaction_type,
                "CPI":request.credit_party_identifier,
                "Size":request.size or "300",
            }

            response_data = await self._make_request(
                "/mpesa/qrcode/v1/generate",
                payload,
                f'qr:{request.ref_no}'
            )

            return DynamicQRResponse(**response_data)
        

    async def handle_c2b_confirmation(self, callback:C2BCallback)->dict:
            """
            Handle C2B confirmation request.
            Args:
                callback(C2BCallback): C2B callback object
            Returns:
                response(CreateCallbackResponseReturnType): Mpesa compliant response
            
            """
            
            try:
                await self._callback_handler.handle_c2b_confirmation(callback)
                return self._callback_handler.create_callback_response(True)
            except Exception as e:
                logger.exception(f"C2B Confirmation Error: {e}")
                return self._callback_handler.create_callback_response(False, "Processing failed.")
            


    async def parse_stk_callback(self, callback:STKCallback)->ParsedCallbackData:
            """
            Parse STK callback without handling (for testing)
            Args:
                callback(STKCallback): STK callback object
            Returns:
                parsed_data(ParsedCallbackData): Mpesa compliant response
            """
            return self._callback_handler.parse_callback(callback)



    async def parse_c2b_callback(self, callback:C2BCallback)->ParsedCallbackData:
            """
            Parse C2B callback without handling (for testing)
            Args:
                callback(C2BCallback): C2B callback object
            Returns:
                parsed_data(ParsedCallbackData): Mpesa compliant response
            """
            return self._callback_handler.parse_c2b_callback(callback)



    def get_config(self)->MpesaConfig:
            """
            Get configuration (for plugins)
            Returns:
                config(MpesaConfig): Mpesa configuration object
            """
            return self.config
        

    def get_rate_limit_usage(self, key:str):
            """
            Get rate limit usage for a given key
            Args:
                key(str): Rate limit key
            Returns:
                usage(int): Usage count for the given key. None if rate limiter is not set.
            
            """
            if isinstance(self._rate_limiter, RateLimiter):
                return self._rate_limiter.get_usage(key)
            return None
        

    async def handle_b2c_callback(self, callback:B2CCallback):
            """
            Handle B2C callback.
            Args:
                callback(B2CCallback): B2C callback object
            Returns:
                response_data(CreateCallbackResponseReturnType): Mpesa compliant response
            
            """
            try:
                parsed = self._callback_handler.parse_b2c_callback(callback)

                if self._callback_handler.options.on_b2c_result:
                    await self._callback_handler.options.on_b2c_result(parsed)
                
                return self._callback_handler.create_callback_response(parsed.is_success)
            
            except Exception as e:
                logger.exception(f"B2C Callback Error: {e}")
                return self._callback_handler.create_callback_response(False, "Processing failed.")
            

        
    async def simulate_c2b(self, request:C2BSimulateRequest)->C2BSimulateResponse:
            if self.config.environment == 'production':
                raise MpesaValidationError(
                    "C2B simulation is only available in sandbox environment. " +
                    "In production, C2B transactions come from real customer payments.",)
            
            if request.amount < 1:
                raise MpesaValidationError("Amount must be at least 1 KES.")
            
            if request.bill_ref_number is None:
                raise MpesaValidationError("Bill reference number is required.")
            
            phone = self._validate_and_format_phone(request.phone_number)
            payload = {
                "ShortCode": self.config.short_code,
                "CommandID": request.command_id or "CustomerPayBillOnline",
                "Amount": math.floor(request.amount),
                "Msisdn": phone,
                "BillRefNumber": request.bill_ref_number
            }

            response_data = await self._make_request(
                '/mpesa/c2b/v1/simulate',
                payload,
                f"c2b:simulate:{phone}"
            )
            
            return C2BSimulateResponse(**response_data)
        


        # NOTE MIGHT NEED TO ADD AWAIT BEFORE self._make_request IN ALL THE ABOVE FUNCTIONS


    async def handle_b2b_callback(self, callback:B2BCallback):
        """
        Handle B2B callback.
        Args:
            callback(B2BCallback): B2B callback object
        Returns:
            response_data(CreateCallbackResponseReturnType): Mpesa compliant response

        """
        try:
            parsed = self._callback_handler.parse_b2b_callback(callback)
            if self._callback_handler.options.on_b2b_result:
                 await self._callback_handler.options.on_b2b_result(parsed)
            return self._callback_handler.create_callback_response(parsed.is_success)
        except Exception as e:
            logger.exception(f"B2B Callback Error: {e}")
            return self._callback_handler.create_callback_response(False, "Processing failed.")
        
    async def handle_account_balance_callback(self, callback:AccountBalanceCallback):
        """
        Handle account balance callback.
        Args:
            callback(AccountBalanceCallback): Account balance callback object
        Returns:
            response_data(CreateCallbackResponseReturnType): Mpesa compliant response
        """

        try:
            parsed = self._callback_handler.parse_account_balance_callback(callback)
            if self._callback_handler.options.on_account_balance_result:
                await self._callback_handler.options.on_account_balance_result(parsed)
            return self._callback_handler.create_callback_response(parsed.is_success)
        except Exception as e:
            logger.exception(f"Account Balance Callback Error: {e}")
            return self._callback_handler.create_callback_response(False, "Processing failed.")

    async def handle_transaction_status_callback(self, callback:TransactionStatusCallback):
        """
        Handle transaction status callback.
        Args:
            callback(TransactionStatusCallback): Transaction status callback object
        Returns:
            response_data(CreateCallbackResponseReturnType): Mpesa compliant response
        """

        try:
            parsed = self._callback_handler.parse_transaction_status_callback(callback)
            if self._callback_handler.options.on_transaction_status_result:
                await self._callback_handler.options.on_transaction_status_result(parsed)
            return self._callback_handler.create_callback_response(parsed.is_success)
        except Exception as e:
            logger.exception(f"Transaction Status Callback Error: {e}")
            return self._callback_handler.create_callback_response(False, "Processing failed.")


    async def handle_reversal_callback(self, callback:ReversalCallback):
         """
        Handle reversal callback.
        Args:
            callback(ReversalCallback): Reversal callback object
        Returns:
            response_data(CreateCallbackResponseReturnType): Mpesa compliant response
        """
         try:
            parsed = self._callback_handler.parse_reversal_callback(callback)
            if self._callback_handler.options.on_reversal_result:
                await self._callback_handler.options.on_reversal_result(parsed)
            return self._callback_handler.create_callback_response(parsed.is_success)
         except Exception as e:
            logger.exception(f"Reversal Callback Error: {e}")
            return self._callback_handler.create_callback_response(False, "Processing failed.")
         


    def destroy(self):
        """
        Cleanup process
        """
        if isinstance(self._rate_limiter, RateLimiter):
            self._rate_limiter.destroy()
        
        


         



