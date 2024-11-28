"""Protocol for structured communication between LLM and agents."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import uuid

@dataclass
class Intent:
    """Represents the intended action for an agent to perform."""
    name: str
    description: Optional[str] = None

@dataclass
class Message:
    """Structured message for LLM-to-agent communication."""
    id: str
    intent: str
    agent: str
    payload: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def create(cls, intent: str, agent: str, payload: Dict[str, Any], 
               metadata: Optional[Dict[str, Any]] = None) -> 'Message':
        """Create a new message with auto-generated ID and timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            intent=intent,
            agent=agent,
            payload=payload,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

    def to_json(self) -> str:
        """Convert message to JSON string."""
        data = {
            "id": self.id,
            "intent": self.intent,
            "agent": self.agent,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string."""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class ProtocolError(Exception):
    """Base exception for protocol-related errors."""
    pass

class InvalidMessageError(ProtocolError):
    """Raised when a message is malformed or invalid."""
    pass

class UnknownIntentError(ProtocolError):
    """Raised when an intent is not recognized."""
    pass
