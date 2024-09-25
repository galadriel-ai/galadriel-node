from enum import Enum
from pydantic import BaseModel
from pydantic import Field

# TODO: Move these common protocol stuff into a shared library
class PingPongMessageType(Enum):
    PING = 1
    PONG = 2

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
    nonce: str = Field(description="The same nonce as in the request")
