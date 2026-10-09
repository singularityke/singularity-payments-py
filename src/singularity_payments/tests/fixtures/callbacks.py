from singularity_payments.types.mpesa import STKCallback, C2BCallback, B2CCallback

def successfull_stk_callback():
    return STKCallback.model_validate({
        "Body":{
              "stkCallback": {
                "MerchantRequestID": "mock-merchant-123",
                "CheckoutRequestID": "mock-checkout-456",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                  "Item": [
                    { "Name": "Amount", "Value": 1000 },
                    { "Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV" },
                    { "Name": "TransactionDate", "Value": 20251222144900 },
                    { "Name": "PhoneNumber", "Value": 254712345678 },
                  ],
                },
              },
            },}
    )


def failed_stk_callback():
    return STKCallback.model_validate({
    "Body":{
    "stkCallback": {
      "MerchantRequestID": "mock-merchant-789",
      "CheckoutRequestID": "mock-checkout-012",
      "ResultCode": 1,
      "ResultDesc": "Insufficient funds in M-Pesa account",
    },
  },
})


def cancelled_stk_callback():
    return STKCallback.model_validate({
    "Body":{
    "stkCallback": {
      "MerchantRequestID": "mock-merchant-789",
      "CheckoutRequestID": "mock-checkout-012",
      "ResultCode": 1032,
      "ResultDesc": "Request cancelled by user",
    },
  },
})


def mock_c2b_callback():
    result = {
      "TransactionType":"Pay Bill",
      "TransID":"RI704KI9RW",
      "TransTime":"20190629102111",
      "TransAmount":"1000",
      "BusinessShortCode":"600000",
      "BillRefNumber":"account123",
      "MSISDN":"254708374149",
      "FirstName":"John",
      "MiddleName":"K",
      "LastName":"Doe"

    }
    return C2BCallback(**result)

def mock_b2c_callback():
  return B2CCallback.model_validate({
    "Result":{
        "ResultType": 0,
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "OriginatorConversationID": "orig-123",
        "ConversationID": "conv-456",
        "TransactionID": "trans-789",
        "ResultParameters": {
        "ResultParameter": [
        { "Key": "TransactionReceipt", "Value": "NLJ7RT61SV" },
        { "Key": "TransactionAmount", "Value": 5000 },
        { "Key": "ReceiverPartyPublicName", "Value": "254712345678 - John Doe" },
        { "Key": "B2CChargesPaidAccountAvailableFunds", "Value": 50 },
      ],
    },
    }
  }
)
