import json
from dataclasses import dataclass
from typing import Dict

from dataclasses_json import dataclass_json
from openai.types.chat import ChatCompletionChunk


@dataclass
class Error:
    error_code: int
    message: str
    raw_log: str


@dataclass_json
@dataclass
class InferenceContent:
    type: str
    value: str


@dataclass_json
@dataclass
class InferenceMessage:
    role: str
    content: InferenceContent


@dataclass_json
@dataclass
class InferenceRequest:
    id: str
    chat_request: Dict

    @staticmethod
    def from_json(message):
        try:
            data = json.loads(message)
            return InferenceRequest(id=data["id"], chat_request=data["chat_request"])
        except:
            return None


@dataclass
class InferenceResponse:
    request_id: str
    chunk: ChatCompletionChunk

    def to_json(self):
        return json.dumps(
            {"request_id": self.request_id, "chunk": self.chunk.to_dict()}
        )
