import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import Optional

from dataclasses_json import dataclass_json
from openai.types.chat import ChatCompletionChunk


class SdkError(Exception):
    pass


class AuthenticationError(SdkError):
    pass


class LLMEngine(Enum):
    VLLM = "vllm"
    LMDEPLOY = "lmdeploy"


class InferenceStatusCodes(Enum):
    BAD_REQUEST = 400
    AUTHENTICATION_ERROR = 401
    PERMISSION_DENIED = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    RATE_LIMIT = 429
    UNKNOWN_ERROR = 500


@dataclass
class InferenceError:
    status_code: InferenceStatusCodes
    message: str

    def to_dict(self):
        return {
            "status_code": self.status_code.value,
            "message": self.message,
        }


@dataclass_json
@dataclass
class InferenceRequest:
    id: str
    chat_request: Dict
    type: Optional[str] = None

    # pylint: disable=too-many-boolean-expressions, no-else-return
    @staticmethod
    def get_inference_request(parsed_data):
        if (
            parsed_data.get("id") is not None
            and parsed_data.get("chat_request") is not None
        ):
            type_field = None
            if "type" in parsed_data:
                type_field = parsed_data["type"]
            return InferenceRequest(
                id=parsed_data["id"],
                type=type_field,
                chat_request=parsed_data["chat_request"],
            )
        else:
            return None


@dataclass
class InferenceResponse:
    request_id: str
    chunk: Optional[ChatCompletionChunk] = None
    error: Optional[InferenceError] = None

    def to_json(self):
        return json.dumps(
            {
                "request_id": self.request_id,
                "error": self.error.to_dict() if self.error else None,
                "chunk": self.chunk.to_dict() if self.chunk else None,
            }
        )
