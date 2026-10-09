from singularity_payments.types.config import MpesaConfig


mock_config = MpesaConfig.model_validate(
    {
        "consumerKey": "test_consumer_key",
        "consumerSecret": "test_consumer_secret",
        "passkey": "test_passkey_1234567890",
        "shortcode": "174379",
        "environment": "sandbox",
        "callbackUrl": "https://example.com/callback",
        "timeoutUrl": "https://example.com/timeout",
        "resultUrl": "https://example.com/result",
        "initiatorName": "testapi",
        "securityCredential": "test_credential",
    }
)


mock_production_config = mock_config.model_copy(update={"environment": "production"})
