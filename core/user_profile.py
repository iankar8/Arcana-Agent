"""User profile management for context-aware agent interactions."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from dataclasses import dataclass, asdict
import uuid

@dataclass
class Action:
    """Represents a user action or task."""
    id: str
    type: str
    description: str
    timestamp: datetime
    status: str
    metadata: Dict[str, Any]

    @classmethod
    def create(cls, type: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> 'Action':
        """Create a new action with auto-generated ID and timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            type=type,
            description=description,
            timestamp=datetime.now(),
            status="created",
            metadata=metadata or {}
        )

class UserProfile:
    """Manages user-specific data and preferences."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferences: Dict[str, Any] = {}
        self.history: List[Action] = []
        self.goals: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.last_active = datetime.now()

    def update_preference(self, key: str, value: Any) -> None:
        """Update a user preference."""
        self.preferences[key] = value
        self.last_active = datetime.now()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.preferences.get(key, default)

    def set_goal(self, goal_id: str, goal_data: Dict[str, Any]) -> None:
        """Set or update a user goal."""
        self.goals[goal_id] = {
            **goal_data,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        self.last_active = datetime.now()

    def complete_goal(self, goal_id: str) -> None:
        """Mark a goal as completed."""
        if goal_id in self.goals:
            self.goals[goal_id]["status"] = "completed"
            self.goals[goal_id]["completed_at"] = datetime.now().isoformat()
        self.last_active = datetime.now()

    def log_action(self, action: Action) -> None:
        """Log a user action."""
        self.history.append(action)
        self.last_active = datetime.now()

    def update_action_status(self, action_id: str, status: str) -> None:
        """Update the status of an action in history."""
        for action in self.history:
            if action.id == action_id:
                action.status = status
                break
        self.last_active = datetime.now()

    def get_recent_actions(self, limit: int = 10) -> List[Action]:
        """Get the most recent actions."""
        return sorted(
            self.history,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]

    def get_actions_by_type(self, action_type: str) -> List[Action]:
        """Get all actions of a specific type."""
        return [
            action for action in self.history
            if action.type == action_type
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "preferences": self.preferences,
            "history": [asdict(action) for action in self.history],
            "goals": self.goals,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create profile from dictionary."""
        profile = cls(data["user_id"])
        profile.preferences = data["preferences"]
        profile.history = [
            Action(**{
                **action_data,
                "timestamp": datetime.fromisoformat(action_data["timestamp"])
            })
            for action_data in data["history"]
        ]
        profile.goals = data["goals"]
        profile.created_at = datetime.fromisoformat(data["created_at"])
        profile.last_active = datetime.fromisoformat(data["last_active"])
        return profile

    def save_to_file(self, filepath: str) -> None:
        """Save profile to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'UserProfile':
        """Load profile from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
