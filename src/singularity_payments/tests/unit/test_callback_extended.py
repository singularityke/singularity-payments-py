import pytest
from singularity_payments.tests.fixtures.callbacks import successfull_stk_callback
from singularity_payments.utils.callback import MpesaCallbackHandler
from singularity_payments.types.mpesa import B2BCallback, AccountBalanceCallback, TransactionStatusCallback, ReversalCallback


class TestB2CCallbackHandlers:
    def setup_method(self):
        self.handler = MpesaCallbackHandler()

    def test_failed_b2c_callback(self):
        failed_callback = {
            "Result": {
                "ResultType": 0,
                "ResultCode": 1,
                "ResultDesc": "Insufficient funds",
                "OriginatorConversationID": "orig-123",
                "ConversationID": "conv-456",
                "TransactionID": "trans-789",
            }
        }

        parsed = self.handler.parse_b2c_callback(failed_callback)

        assert parsed.is_success == False
        assert parsed.error_message


class TestB2BCallbacks:
    def setup_method(self):
        self.handler = MpesaCallbackHandler()

    def test_successful_b2b_callback(self):
        callback = {
            "Result": {
                "ResultType": 0,
                "ResultCode": 0,
                "ResultDesc": "Success",
                "OriginatorConversationID": "orig-123",
                "ConversationID": "conv-456",
                "TransactionID": "trans-789",
                "ResultParameters": {
                    "ResultParameter": [
                        {"Key": "Amount", "Value": 1000},
                        {"Key": "DebitAccountBalance", "Value": "5000.00"},
                        {"Key": "TransCompletedTime", "Value": "20231201120000"},
                        {"Key": "ReceiverPartyPublicName", "Value": "Test Business"},
                        {"Key": "Currency", "Value": "KES"},
                    ],
                },
            },
        }

        parsed = self.handler.parse_b2b_callback(callback)

        assert parsed.is_success
        assert parsed.amount == 1000
        assert parsed.debit_account_balance == "5000.00"
        assert parsed.currency == "KES"

    def test_failed_b2b_callback(self):
        callback = {
            "Result": {
                "ResultType": 0,
                "ResultCode": 1,
                "ResultDesc": "Failed",
                "OriginatorConversationID": "orig-123",
                "ConversationID": "conv-456",
                "TransactionID": "trans-789",
            }
        }

        parsed = self.handler.parse_b2b_callback(callback)

        assert parsed.is_success == False
        assert parsed.error_message

    def test_parse_successfull_account_balance(self):
        callback = {
            "Result": {
          "ResultType": 0,
          "ResultCode": 0,
          "ResultDesc": "Success",
          "OriginatorConversationID": "orig-123",
          "ConversationID": "conv-456",
          "TransactionID": "trans-789",
          "ResultParameters": {
            "ResultParameter": [
              { "Key": "WorkingAccountAvailableFunds", "Value": 10000 },
              { "Key": "AvailableBalance", "Value": 9500 },
              { "Key": "BookedBalance", "Value": 10500 },
            ],
          },
        },
        }
        parsed = self.handler.parse_account_balance_callback(callback)
        assert parsed.is_success
        assert parsed.working_balance == 10000
        assert parsed.available_balance == 9500
        assert parsed.booked_balance == 10500

    def parse_failed_account_balance(self):
        callback = {
          "Result": {
            "ResultType": 0,
            "ResultCode": 1,
            "ResultDesc": "Failed",
            "OriginatorConversationID": "orig-123",
            "ConversationID": "conv-456",
            "TransactionID": "trans-789",
          },
        }

        parsed = self.handler.parse_account_balance_callback(callback)
        assert parsed.is_success == False
        assert parsed.error_message


    def transatcion_status_callbacks(self):
        callback = {
          "Result": {
            "ResultType": 0,
            "ResultCode": 0,
            "ResultDesc": "Success",
            "OriginatorConversationID": "orig-123",
            "ConversationID": "conv-456",
            "TransactionID": "trans-789",
            "ResultParameters": {
              "ResultParameter": [
                { "Key": "ReceiptNo", "Value": "NLJ7RT61SV" },
                { "Key": "Amount", "Value": 1000 },
                { "Key": "FinalisedTime", "Value": "20231201120000" },
              ],
            },
          },
        }

        parsed = self.handler.parse_transaction_status_callback(callback)
        assert parsed.is_success
        assert parsed.receipt_no == "NLJ7RT61SV"
        assert parsed.amount == 1000
        assert parsed.completed_time == "20231201120000"


    def parse_failed_transaction_status(self):
        callback = {
            "Result": {
              "ResultType": 0,
              "ResultCode": 1,
              "ResultDesc": "Transaction not found",
              "OriginatorConversationID": "orig-123",
              "ConversationID": "conv-456",
              "TransactionID": "trans-789",
            },
        }

        parsed = self.handler.parse_transaction_status_callback(callback)
        assert parsed.is_success == False
        assert parsed.error_message


class ReversalCallbacks:
    def setup_method(self):
        self.handler = MpesaCallbackHandler()


    def parse_successfull_reversal_callback(self):
        callback = {
            "Result": {
              "ResultType": 0,
              "ResultCode": 0,
              "ResultDesc": "Success",
              "OriginatorConversationID": "orig-123",
              "ConversationID": "conv-456",
              "TransactionID": "trans-789",
            },
        }

        parsed = self.handler.parse_reversal_callback(callback)
        assert parsed.is_success
        assert parsed.transaction_id == "trans-789"

    def parse_failed_reversal_callback(self):
        callback = {
            "Result": {
              "ResultType": 0,
              "ResultCode": 1,
              "ResultDesc": "Reversal failed",
              "OriginatorConversationID": "orig-123",
              "ConversationID": "conv-456",
              "TransactionID": "trans-789",
            },
        }
        parsed = self.handler.parse_reversal_callback(callback)
        assert parsed.is_success == False
        assert parsed.error_message


    @pytest.mark.asyncio
    async def custom_logger(self):
        logger = {
            "info":callable,
            'error':callable,
            'warn':callable
        }

        handler = MpesaCallbackHandler(logger=logger)
        await handler.handle_callback(successfull_stk_callback())
        # TODO: Add assert to check if logger['info'] was called
