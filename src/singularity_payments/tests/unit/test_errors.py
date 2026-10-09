from pydantic import InstanceOf
import pytest
from singularity_payments.utils.errors import (
    MpesaError,
    MpesaAuthError,
    MpesaValidationError,
    MpesaNetworkError,
    MpesaTimeoutError,
    MpesaRateLimitError,
    MpesaApiError,
    parse_mpesa_api_error,
)

class TestMpesaErrors:
    def test_mpesa_error(self):
        error = MpesaError(
            'Test error', "TEST_CODE", 400, {
                "detail":"test"
            }
        )

        assert isinstance(error, Exception)
        assert error.message == "Test error"
        assert error.code == 'TEST_CODE'
        assert error.status_code == 400
        assert error.details == {"detail":"test"}
        assert error.name=="MpesaError"


    def test_mpesa_auth_error(self):
        error = MpesaAuthError(
            message="Invalid credentials",
        )

        assert isinstance(error, MpesaError)
        assert error.code == 'AUTH_ERROR'
        assert error.status_code == 401
        assert error.name=="MpesaAuthError"


    def test_mpesa_validation_error(self):
        error = MpesaValidationError(
            "Invalid phone number"
        )

        assert isinstance(error, MpesaError)
        assert error.code == 'VALIDATION_ERROR'
        assert error.status_code == 400
        assert error.name=="MpesaValidationError"


    def test_mpesa_network_error(self):
        error = MpesaNetworkError(
            "Connection failed",
            True
        )

        assert isinstance(error, MpesaError)
        assert error.code == 'NETWORK_ERROR'
        assert error.status_code == 503
        assert error.name=="MpesaNetworkError"

    def test_mpesa_timeout_error(self):
        error = MpesaTimeoutError(
            "Request timed out"
        )

        assert isinstance(error, MpesaError)
        assert error.code == 'TIMEOUT_ERROR'
        assert error.status_code == 408
        assert error.name=="MpesaTimeoutError"


    def test_mpesa_rate_limmit_error(self):
        error = MpesaRateLimitError(
            "Rate limit exceeded",
            60
        )

        assert isinstance(error, MpesaError)
        assert error.code == 'RATE_LIMIT_ERROR'
        assert error.status_code == 429
        assert error.name=="MpesaRateLimitError"


    def test_parse_mpesa_api_auth_error(self):
        error = parse_mpesa_api_error(
            401,
            {'errorMessage':"Unauthorized"}
        )

        assert isinstance(error, MpesaAuthError)
        assert error.message == 'Unauthorized'


    def test_parse_mpesa_api_validation_error(self):
        error = parse_mpesa_api_error(
            400,
            {'errorMessage':"Bad request"}
        )

        assert isinstance(error, MpesaValidationError)
        assert error.message == 'Bad request'


    def test_parse_mpesa_api_rate_limit_error(self):
        error = parse_mpesa_api_error(
            429,
            {
                'errorMessage':"Too many requests",
                "retryAfter":30

            },
        )

        assert isinstance(error, MpesaRateLimitError)
        assert error.message == 'Too many requests'
        assert error.retry_after == 30


    def test_parse_mpesa_api_network_error(self):
        error = parse_mpesa_api_error(
            500,
            {'errorMessage':"Service unavailable"}
        )

        assert isinstance(error, MpesaNetworkError)
        assert error.message == 'Service unavailable'
        assert error.is_retryable

    def test_missing_error_message(self):
        error  = parse_mpesa_api_error(400, {})
        assert error.message == 'Unknown API error'


    def test_parse_mpesa_api_response_description(self):
        error = parse_mpesa_api_error(
            400,
            {'errorMessage':"Bad request"}
        )
        assert error.message == 'Bad request'
