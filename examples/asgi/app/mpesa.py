import os

from dotenv import load_dotenv

load_dotenv()  # load ./.env before reading any MPESA_* variables

from singularity_payments import (
    CallbackHandlerOptions,
    MpesaClient,
    MpesaClientOptions,
    MpesaConfig,
    ParsedCallbackData,
)


async def on_success(data: ParsedCallbackData) -> None:
    # Persist the payment against your own order/record.
    print("Payment received", data.mpesa_receipt_number, data.amount)


async def on_failure(data: ParsedCallbackData) -> None:
    print("Payment failed", data.result_code, data.result_description)


mpesa = MpesaClient(
    MpesaConfig(
        consumer_key=os.environ["MPESA_CONSUMER_KEY"],
        consumer_secret=os.environ["MPESA_CONSUMER_SECRET"],
        passkey=os.environ["MPESA_PASSKEY"],
        shortcode=os.environ["MPESA_SHORTCODE"],
        environment=os.environ.get("MPESA_ENVIRONMENT", "sandbox"),
        callback_url=os.environ["MPESA_CALLBACK_URL"],
        # Required for B2C, B2B, Reversal, Transaction Status and Account Balance
        initiator_name=os.environ.get("MPESA_INITIATOR_NAME"),
        security_credential=os.environ.get("MPESA_SECURITY_CREDENTIAL"),
        result_url=os.environ.get("MPESA_RESULT_URL"),
        timeout_url=os.environ.get("MPESA_TIMEOUT_URL"),
    ),
    MpesaClientOptions(
        callback_options=CallbackHandlerOptions(
            on_success=on_success,
            on_failure=on_failure,
        ),
    ),
)