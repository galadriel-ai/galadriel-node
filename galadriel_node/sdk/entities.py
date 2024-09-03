import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import Optional

from dataclasses_json import dataclass_json
from openai.types.chat import ChatCompletionChunk


class SdkError(Exception):
    pass


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

    @staticmethod
    def from_json(message):
        try:
            data = json.loads(message)
            return InferenceRequest(
                id=data["id"], type=data["type"], chat_request=data["chat_request"]
            )
        except:
            return None


@dataclass
class InferenceResponse:
    request_id: str
    chunk: Optional[ChatCompletionChunk] = None
    error: Optional[InferenceStatusCodes] = None

    def to_json(self):
        return json.dumps(
            {
                "request_id": self.request_id,
                "error": self.error.to_dict() if self.error else None,
                "chunk": self.chunk.to_dict() if self.chunk else None,
            }
        )
