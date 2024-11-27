import json
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass

from pydantic import BaseModel
from pydantic import Field

from dataclasses_json import dataclass_json
from openai.types.chat import ChatCompletionChunk


# TODO: Move these common protocol stuff into a shared library
class PingPongMessageType(Enum):
    PING = 1
    PONG = 2
    RECONNECT_REQUEST = 3


class PingRequest(BaseModel):
    protocol_version: str = Field(
        description="Protocol version of the ping-pong protocol"
    )
    message_type: PingPongMessageType = Field(description="Message type")
    node_id: str = Field(description="Node ID")
    nonce: str = Field(description="A random number to prevent replay attacks")
    rtt: int = Field(description="RTT as observed by the server in milliseconds")
    ping_streak: int = Field(
        description="Number of consecutive pings as observed by the server"
    )
    miss_streak: int = Field(
        description="Number of consecutive pings misses as observed by the server"
    )


class PongResponse(BaseModel):
    protocol_version: str = Field(
        description="Protocol version of the ping-pong protocol"
    )
    message_type: PingPongMessageType = Field(description="Message type")
    node_id: str = Field(description="Node ID")
    nonce: str = Field(description="The same nonce as in the request")
    api_ping_time: List[Optional[int]] = Field(
        description="Ping time to Galadriel API in milliseconds"
    )


class NodeReconnectRequest(BaseModel):
    protocol_version: str = Field(
        description="Protocol version of the ping-pong protocol"
    )
    message_type: PingPongMessageType = Field(description="Message type")
    node_id: str = Field(description="Node ID")
    nonce: str = Field(description="A random number to prevent replay attacks")
    reconnect_request: bool = Field(
        description="True if the node is requested to reconnect to a better performing server"
    )


class HealthCheckMessageType(Enum):
    HEALTH_CHECK_REQUEST = 1
    HEALTH_CHECK_RESPONSE = 2


class HealthCheckRequest(BaseModel):
    protocol_version: str = Field(
        description="Protocol version of the health-check protocol"
    )
    message_type: HealthCheckMessageType = Field(
        description="Message type",
        default=HealthCheckMessageType.HEALTH_CHECK_REQUEST,
    )
    node_id: str = Field(description="Node ID")
    nonce: str = Field(description="A random number to prevent replay attacks")


class HealthCheckGPUUtilization(BaseModel):
    gpu_percent: int = Field(description="GPU utilization, percent")
    vram_percent: int = Field(description="VRAM utilization, percent")


class HealthCheckResponse(BaseModel):
    protocol_version: str = Field(
        description="Protocol version of the ping-pong protocol"
    )
    message_type: HealthCheckMessageType = Field(
        description="Message type",
        default=HealthCheckMessageType.HEALTH_CHECK_RESPONSE,
    )
    node_id: str = Field(description="Node ID")
    nonce: str = Field(description="The same nonce as in the request")

    cpu_percent: int = Field(description="CPU utilization, percent")
    ram_percent: int = Field(description="RAM utilization, percent")
    disk_percent: int = Field(description="Disk utilization, percent")
    gpus: List[HealthCheckGPUUtilization] = Field(description="GPU utilization")


class InferenceStatusCodes(Enum):
    RUNNING = 1
    DONE = 2
    ERROR = 3


class InferenceErrorStatusCodes(Enum):
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
    status_code: InferenceErrorStatusCodes
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
    status: Optional[InferenceStatusCodes] = None
    chunk: Optional[ChatCompletionChunk] = None
    error: Optional[InferenceError] = None

    def to_json(self):
        return json.dumps(
            {
                "request_id": self.request_id,
                "error": self.error.to_dict() if self.error else None,
                "chunk": self.chunk.to_dict() if self.chunk else None,
                "status": self.status.value if self.status else None,
            }
        )


class ImageGenerationWebsocketRequest(BaseModel):
    request_id: str = Field(description="Unique ID for the request")
    prompt: str = Field(description="Prompt for the image generation")
    image: Optional[str] = Field(description="Base64 encoded image as input")
    n: int = Field(description="Number of images to generate")
    size: Optional[str] = Field(description="The size of the generated images.")


class ImageGenerationWebsocketResponse(BaseModel):
    request_id: str = Field(description="Unique ID for the request")
    images: List[str] = Field(description="Base64 encoded images as output")
    error: Optional[str] = Field(description="Error message if the request failed")
