import pytest
from unittest.mock import MagicMock, patch
from http import HTTPStatus
from galadriel_node.sdk.entities import AuthenticationError
from galadriel_node.sdk.system.report_hardware import _post_info


class MockResponse:
    def __init__(self, json, status):
        self._json = json
        self.status = status

    async def json(self):
        return self._json

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


async def test_post_info_unauthorized():
    with patch(
        "aiohttp.ClientSession.post",
        return_value=MockResponse({}, HTTPStatus.UNAUTHORIZED),
    ) as mock_session:
        with pytest.raises(
            AuthenticationError, match="Unauthorized to send hardware info"
        ):
            await _post_info(
                MagicMock(), "mock_api_url", "mock_api_key", "mock_node_id"
            )
