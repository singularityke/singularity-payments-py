from singularity_payments.utils.auth import MpesaAuth
from singularity_payments.tests.fixtures.config import mock_config
from singularity_payments.tests.fixtures.responses import mock_token_response
import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture()
def auth():
    return MpesaAuth(config=mock_config)


class TestMpesaAuth:
    @pytest.mark.asyncio
    async def test_get_access_token(self, auth ,mocker):
        mock_get = mocker.patch("httpx.AsyncClient.get", new_callable=AsyncMock)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = mock_token_response
        mock_get.return_value = mock_response

        token = await auth.get_access_token()

        assert token == "mock_access_token_12345"
        assert mock_get.call_count == 1

        args, kwargs = mock_get.call_args
        assert "Authorization" in kwargs['headers']
