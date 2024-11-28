"""Core interfaces for the Arcana framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Intent:
    """Represents a parsed user intent with associated metadata."""
    name: str
    confidence: float
    parameters: Dict[str, Any]

@dataclass
class Task:
    """Represents a single task to be executed by an agent."""
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    priority: int = 0

class NLUInterface(ABC):
    """Natural Language Understanding interface for parsing user queries."""
    
    @abstractmethod
    async def parse(self, query: str) -> Intent:
        """Parse raw user input into structured intent."""
        pass

class TaskPlannerInterface(ABC):
    """Interface for planning and organizing tasks."""
    
    @abstractmethod
    async def plan(self, intent: Intent) -> List[Task]:
        """Convert an intent into a list of executable tasks."""
        pass

    @abstractmethod
    async def validate_dependencies(self, tasks: List[Task]) -> bool:
        """Validate that task dependencies can be satisfied."""
        pass

class AgentInterface(ABC):
    """Base interface for all task-specific agents."""
    
    @abstractmethod
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the given task and return results."""
        pass

    @abstractmethod
    async def validate(self, task: Task) -> bool:
        """Validate that the agent can handle the given task."""
        pass

class Agent(ABC):
    """Base interface for all agents in the system."""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the agent."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the agent."""
        pass

class ResponseBuilderInterface(ABC):
    """Interface for building user-friendly responses."""
    
    @abstractmethod
    async def build_response(self, results: List[Dict[str, Any]]) -> str:
        """Convert task results into a user-friendly response."""
        pass

    @abstractmethod
    async def build_error_response(self, error: Exception) -> str:
        """Build an error response when task execution fails."""
        pass
