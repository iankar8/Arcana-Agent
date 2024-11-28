"""Core interfaces for the Arcana Agent Framework."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import asyncio
from datetime import datetime

from core.protocol import Message
from core.monitoring import MetricsCollector
from core.error_types import ErrorHandler
from core.feedback_loop import FeedbackLoop, FeedbackLevel

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

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler,
        feedback_loop: FeedbackLoop,
        **kwargs
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.feedback_loop = feedback_loop
        self._running = False
        self._last_active = None
        self._initialization_params = kwargs
        self._current_task: Optional[str] = None

    @abstractmethod
    async def start(self) -> None:
        """Initialize and start the agent."""
        self._running = True
        self._last_active = datetime.now()
        
        await self.feedback_loop.emit(
            task_id="system",
            level=FeedbackLevel.INFO,
            message=f"Agent {self.__class__.__name__} started",
            details={"agent_type": self.__class__.__name__}
        )
        
        await self.on_start()

    @abstractmethod
    async def stop(self) -> None:
        """Stop and cleanup the agent."""
        self._running = False
        
        await self.feedback_loop.emit(
            task_id="system",
            level=FeedbackLevel.INFO,
            message=f"Agent {self.__class__.__name__} stopped",
            details={"agent_type": self.__class__.__name__}
        )
        
        await self.on_stop()

    @abstractmethod
    async def handle_message(self, message: Message) -> None:
        """Process an incoming message."""
        try:
            self._last_active = datetime.now()
            self._current_task = message.id
            
            await self.feedback_loop.emit(
                task_id=message.id,
                level=FeedbackLevel.INFO,
                message=f"Processing message in {self.__class__.__name__}",
                details={
                    "agent_type": self.__class__.__name__,
                    "intent": message.intent
                }
            )
            
            await self.on_message(message)
            
        except Exception as e:
            await self.feedback_loop.emit(
                task_id=message.id,
                level=FeedbackLevel.ERROR,
                message=f"Error in {self.__class__.__name__}: {str(e)}",
                details={
                    "agent_type": self.__class__.__name__,
                    "error": str(e)
                }
            )
            
            await self.error_handler.handle_error(
                e,
                {
                    "component": self.__class__.__name__,
                    "operation": "handle_message",
                    "message_id": message.id
                }
            )
            raise
            
        finally:
            self._current_task = None

    async def request_user_input(
        self,
        message: str,
        options: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ) -> Optional[str]:
        """Request input from the user."""
        if not self._current_task:
            raise RuntimeError("No active task for user input request")
            
        return await self.feedback_loop.request_user_input(
            task_id=self._current_task,
            message=message,
            options=options,
            timeout=timeout
        )

    async def emit_feedback(
        self,
        level: FeedbackLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit feedback for the current task."""
        if not self._current_task:
            raise RuntimeError("No active task for feedback emission")
            
        await self.feedback_loop.emit(
            task_id=self._current_task,
            level=level,
            message=message,
            details=details
        )

    async def on_start(self) -> None:
        """Hook called when agent starts."""
        pass

    async def on_stop(self) -> None:
        """Hook called when agent stops."""
        pass

    async def on_message(self, message: Message) -> None:
        """Hook called when a message is received."""
        pass

    async def on_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Hook called when an error occurs."""
        pass

    @property
    def is_running(self) -> bool:
        """Check if the agent is currently running."""
        return self._running

    @property
    def last_active(self) -> Optional[datetime]:
        """Get the timestamp of the last activity."""
        return self._last_active

    @property
    def current_task(self) -> Optional[str]:
        """Get the current task ID."""
        return self._current_task

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "running": self._running,
            "last_active": self._last_active,
            "current_task": self._current_task,
            "type": self.__class__.__name__
        }

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
