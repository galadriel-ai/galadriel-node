import pytest
from unittest.mock import MagicMock, patch
from http import HTTPStatus
from galadriel_node.sdk.entities import AuthenticationError
from galadriel_node.sdk.system.report_performance import _post_benchmark


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


async def test_post_benchmark_unauthorized():
    with patch(
        "aiohttp.ClientSession.post",
        return_value=MockResponse({}, HTTPStatus.UNAUTHORIZED),
    ) as mock_session:
        with pytest.raises(
            AuthenticationError, match="Unauthorized to save benchmark results"
        ):
            await _post_benchmark(
                "mock_model_name", 100.0, "mock_api_url", "mock_api_key", "mock_node_id"
            )
