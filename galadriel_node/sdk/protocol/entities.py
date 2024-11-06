from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from pydantic import Field


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
    protocol_version: str = Field(description="Protocol version of the ping-pong protocol")
    message_type: PingPongMessageType = Field(description="Message type")
    node_id: str = Field(description="Node ID")
    nonce: str = Field(description="A random number to prevent replay attacks")
    reconnect_request: bool = Field(description="True if the node is requested to reconnect")


class HealthCheckMessageType(Enum):
    HEALTH_CHECK_REQUEST = 1
    HEALTH_CHECK_RESPONSE = 2


class HealthCheckRequest(BaseModel):
    protocol_version: str = Field(
        description="Protocol version of the health-check protocol"
    )
    message_type: HealthCheckMessageType = Field(
        description="Message type",
        default=HealthCheckMessageType.HEALTH_CHECK_REQUEST.value,
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
        default=HealthCheckMessageType.HEALTH_CHECK_RESPONSE.value,
    )
    node_id: str = Field(description="Node ID")
    nonce: str = Field(description="The same nonce as in the request")

    cpu_percent: int = Field(description="CPU utilization, percent")
    ram_percent: int = Field(description="RAM utilization, percent")
    disk_percent: int = Field(description="Disk utilization, percent")
    gpus: List[HealthCheckGPUUtilization] = Field(description="GPU utilization")
