import json
from dataclasses import dataclass
from typing import List

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
    model: str
    messages: List[InferenceMessage]


@dataclass
class InferenceResponse:
    request_id: str
    chunk: ChatCompletionChunk

    def to_json(self):
        return json.dumps(
            {"request_id": self.request_id, "chunk": self.chunk.to_dict()}
        )
