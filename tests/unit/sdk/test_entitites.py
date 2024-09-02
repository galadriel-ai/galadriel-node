import json

from dataclasses import asdict
from unittest.mock import MagicMock
from openai.types.chat import ChatCompletionChunk

from galadriel_node.sdk.entities import InferenceError
from galadriel_node.sdk.entities import InferenceResponse
from galadriel_node.sdk.entities import InferenceStatusCodes


def test_inference_response_no_chunk():
    response = InferenceResponse(
        request_id="123",
        chunk=None,
        error=InferenceError(InferenceStatusCodes.BAD_REQUEST, "error"),
    )

    response_json = response.to_json()
    deserialized_response = json.loads(response_json)

    assert deserialized_response["request_id"] == response.request_id
    assert deserialized_response["error"] == response.error.to_dict()
    assert deserialized_response["chunk"] == None


def test_inference_response_no_error():
    response = InferenceResponse(
        request_id="123",
        chunk=ChatCompletionChunk(
            id="123",
            choices=[],
            created=0,
            model="mock_model",
            object="chat.completion.chunk",
        ),
        error=None,
    )

    response_json = response.to_json()
    deserialized_response = json.loads(response_json)

    assert deserialized_response["request_id"] == response.request_id
    assert deserialized_response["error"] == None
    assert deserialized_response["chunk"] == response.chunk.to_dict()
