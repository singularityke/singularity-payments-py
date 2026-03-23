import pytest
from singularity_payments.tests.fixtures.callback import (
    successfull_stk_callback, failed_stk_callback, cancelled_stk_callback,
    mock_b2c_callback, mock_c2b_callback
)
from singularity_payments.utils.callback import MpesaCallbackHandler, CallbackHandlerOptions

@pytest.fixture
def handler():
    return MpesaCallbackHandler()

class TestSTKCallback:
    @pytest.mark.parametrize(
        "callback_func,expected",
        [
            (
                successfull_stk_callback,
                {
                    "is_success": True,
                    "result_code": 0,
                    "amount": 1000.0,
                    "mpesa_receipt_number": "NLJ7RT61SV",
                    "phone_number": "254712345678",
                    "transaction_date": "2025-12-22T14:49:00",
                    "error_message": None,
                },
            ),
            (
                failed_stk_callback,
                {
                    "is_success": False,
                    "result_code": 1,
                    "amount": None,
                    "mpesa_receipt_number": None,
                    "phone_number": None,
                    "transaction_date": None,
                    "error_message": "Insufficient funds in M-Pesa account",
                },
            ),
            (
                cancelled_stk_callback,
                {
                    "is_success": False,
                    "result_code": 1032,
                    "amount": None,
                    "mpesa_receipt_number": None,
                    "phone_number": None,
                    "transaction_date": None,
                    "error_message": "cancelled",
                },
            ),
        ],
    )
    def test_parse_stk_callback(self, handler, callback_func, expected):
        parsed = handler.parse_callback(callback_func())
        assert parsed.is_success == expected["is_success"]
        assert parsed.result_code == expected["result_code"]
        if expected["amount"] is not None:
            assert parsed.amount == pytest.approx(expected["amount"])
        else:
            assert parsed.amount is None
        assert parsed.mpesa_receipt_number == expected["mpesa_receipt_number"]
        assert parsed.phone_number == expected["phone_number"]
        assert parsed.transaction_date == expected["transaction_date"]
        if expected["error_message"] is not None:
            assert expected["error_message"].lower() in (parsed.error_message or '').lower()
        else:
            assert parsed.error_message is None

class TestIPValidation:
    @pytest.mark.parametrize("valid_ip", [
        "196.201.214.200",
        "196.201.214.206",
        "196.201.213.114",
    ])
    def test_ip_validation(self, valid_ip):
        options = CallbackHandlerOptions(validate_ip=True)
        handler = MpesaCallbackHandler(options)
        
        assert handler.validate_callback_ip(valid_ip)

    @pytest.mark.parametrize("ip", [
        "192.168.1.1", 
        "10.0.0.1", 
        "172.16.0.1", 
        "8.8.8.8"
    ])
    def test_ip_invalidation(self, ip):
        handler = MpesaCallbackHandler(CallbackHandlerOptions(validate_ip=True))
        assert not handler.validate_callback_ip(ip)

    def test_accept_when_validation_disabled(self):
        options = CallbackHandlerOptions(validate_ip=False)
        handler = MpesaCallbackHandler(options=options)
        assert handler.validate_callback_ip("192.168.1.1")
        assert handler.validate_callback_ip("10.0.0.1")

    def test_accept_custom_allowed_ips(self):
        options = CallbackHandlerOptions(validate_ip=True, allowed_ips=["192.168.1.1", "10.0.0.1"])
        handler = MpesaCallbackHandler(options=options)
        assert handler.validate_callback_ip("192.168.1.1")
        assert handler.validate_callback_ip("10.0.0.1")

class TestCallbackHandlers:
    @pytest.mark.asyncio
    async def test_successful_callback_handler(self):
        called = {"success": False}
        async def on_success(parsed):
            called["success"] = True
        options = CallbackHandlerOptions(on_success=on_success)
        handler = MpesaCallbackHandler(options=options)
        await handler.handle_callback(successfull_stk_callback())
        assert called["success"]

    @pytest.mark.asyncio
    async def test_failed_callback_handler(self):
        called = {"failure": False}
        async def on_failure(parsed):
            called["failure"] = True
        options = CallbackHandlerOptions(on_failure=on_failure)
        handler = MpesaCallbackHandler(options=options)
        await handler.handle_callback(failed_stk_callback())
        assert called["failure"]

    @pytest.mark.asyncio
    async def test_on_callback_handler(self):
        called = {"count": 0}
        async def on_callback(parsed):
            called["count"] += 1
        options = CallbackHandlerOptions(on_callback=on_callback)
        handler = MpesaCallbackHandler(options=options)
        await handler.handle_callback(successfull_stk_callback())
        await handler.handle_callback(failed_stk_callback())
        assert called["count"] == 2

    @pytest.mark.asyncio
    async def test_duplicate_check(self):
        called_duplicate = {"called": False}
        async def is_duplicate(parsed):
            called_duplicate["called"] = True
        called_success = {"called": False}
        async def on_success(parsed):
            called_success
        options = CallbackHandlerOptions(on_success=on_success, is_duplicate=is_duplicate)
        handler = MpesaCallbackHandler(options=options)
        await handler.handle_callback(successfull_stk_callback())
        assert called_duplicate["called"] is True
        assert called_success["called"] is False

    @pytest.mark.asyncio
    async def test_reject_callback_from_invalid_ip(self):
        handler = MpesaCallbackHandler(CallbackHandlerOptions(validate_ip=True))
        with pytest.raises(Exception):
            await handler.handle_callback(successfull_stk_callback(), ip_address="192.168.1.1")

class TestC2BAndB2C:
    def test_c2b_callback(self):
        handler = MpesaCallbackHandler()
        parsed = handler.parse_c2b_callback(mock_c2b_callback())
        assert parsed.transaction_id == "RI704KI9RW"
        assert parsed.amount == 1000
        assert parsed.msisdn == "254708374149"
        assert parsed.first_name == "John"
        assert parsed.last_name == "Doe"

    @pytest.mark.asyncio
    async def test_default_c2b_callback(self):
        handler = MpesaCallbackHandler()
        result = await handler.handle_c2b_validation(mock_c2b_callback())
        assert result

    def test_b2c_callback(self):
        handler = MpesaCallbackHandler()
        parsed = handler.parse_b2c_callback(mock_b2c_callback())
        assert parsed.is_success
        assert parsed.transaction_id == "NLJ7RT61SV"
        assert parsed.amount == 5000
        assert parsed.charges == 50

class TestErrorMessages:
    @pytest.mark.parametrize("code,expected", [
        (0, "Success"),
        (1, "Insufficient"),
        (17, "cancelled"),
        (1032, "cancelled"),
        (2001, "Wrong"),
    ])
    def test_error_messages(self, code, expected):
        handler = MpesaCallbackHandler()
        message = handler.get_error_message(code)
        assert expected.lower() in message.lower()


class TestResponseCreation:
    def test_successfull_response(self, handler):
        response = handler.create_callback_response(success=True)
        assert response.result_code == 0
        assert response.result_desc == "Accepted"


    def test_failed_response(self, handler):
        response = handler.create_callback_response(success=False, message="Custom Error")
        assert response.result_code == 1
        assert response.result_desc == "Custom Error"
