"""Message types and handling for distributed leader election."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class MessageType(Enum):
    """Types of messages in the election protocol."""
    ELECTION = "ELECTION"      # Initiates an election
    OK = "OK"                  # Response to election message
    LEADER = "LEADER"          # Announces the elected leader
    HEARTBEAT = "HEARTBEAT"    # Leader sends periodic heartbeat
    ACK = "ACK"                # Acknowledgment


@dataclass
class Message:
    """Represents a message between nodes."""

    sender_id: int
    recipient_id: int
    message_type: MessageType
    timestamp: float
    data: Optional[dict] = None

    def __repr__(self) -> str:
        return f"Message({self.message_type.value} from Node{self.sender_id} to Node{self.recipient_id})"

    def to_dict(self) -> dict:
        """Convert message to dictionary representation."""
        return {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
        }
