import json
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from websockets import WebSocketClientProtocol
from galadriel_node.sdk.diffusers import Diffusers
from galadriel_node.sdk.image_generation import (
    ImageGeneration,
    validate_image_generation_request,
)
from galadriel_node.sdk.protocol.entities import (
    ImageGenerationWebsocketRequest,
)


def mock_diffusers_init(self, model: str):
    self.generate_images = MagicMock(return_value=["image_data"])
    self.pipeline = MagicMock()
    pass


@pytest.fixture
@patch.object(Diffusers, "__init__", mock_diffusers_init)
def image_generation():
    return ImageGeneration(model="test_model")


@pytest.fixture
def websocket():
    return AsyncMock(spec=WebSocketClientProtocol)


@pytest.fixture
def send_lock():
    return asyncio.Lock()


@pytest.fixture
def image_request():
    return ImageGenerationWebsocketRequest(
        request_id="test_request_id", prompt="test prompt", image=None, n=1, size=None
    )


@pytest.mark.asyncio
async def test_process_request(image_generation, image_request, websocket, send_lock):
    await image_generation.process_request(image_request, websocket, send_lock)
    websocket.send.assert_called_once()
    args = websocket.send.call_args.args
    response_data = json.loads(args[0])
    assert response_data["request_id"] == image_request.request_id
    assert response_data["images"] == ["image_data"]


def test_validate_request(image_generation):
    data = {
        "request_id": "test_request_id",
        "prompt": "test prompt",
        "image": None,
        "n": 1,
        "size": None,
    }
    request = validate_image_generation_request(data)
    assert request is not None
    assert request.request_id == data["request_id"]
    assert request.prompt == data["prompt"]
    assert request.image == data["image"]
    assert request.n == data["n"]
    assert request.size == data["size"]


def test_validate_request_invalid_data(image_generation):
    data = {"invalid_key": "invalid_value"}
    request = validate_image_generation_request(data)
    assert request is None


@pytest.mark.asyncio
async def test_is_idle(image_generation):
    assert await image_generation.no_pending_requests() is True
    await image_generation.counter.increment()
    assert await image_generation.no_pending_requests() is False
