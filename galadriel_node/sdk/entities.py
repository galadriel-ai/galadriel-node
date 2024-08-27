from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List
from typing import Optional


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


@dataclass_json
@dataclass
class InferenceResponse:
    request_id: str
    content: str
    finish_reason: Optional[str] = None
