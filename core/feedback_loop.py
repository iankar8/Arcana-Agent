"""Real-time feedback system for task execution and debugging."""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import asyncio
import json
from dataclasses import dataclass, asdict
import uuid
from enum import Enum

from core.logging_config import get_logger
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler

logger = get_logger(__name__)

class FeedbackLevel(Enum):
    """Feedback importance levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUGGESTION = "suggestion"

@dataclass
class FeedbackEvent:
    """Represents a feedback event in the system."""
    id: str
    task_id: str
    level: FeedbackLevel
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    requires_response: bool = False
    response_options: Optional[List[str]] = None
    
    @classmethod
    def create(
        cls,
        task_id: str,
        level: FeedbackLevel,
        message: str,
        details: Dict[str, Any] = None,
        requires_response: bool = False,
        response_options: Optional[List[str]] = None
    ) -> 'FeedbackEvent':
        """Create a new feedback event."""
        return cls(
            id=str(uuid.uuid4()),
            task_id=task_id,
            level=level,
            message=message,
            details=details or {},
            timestamp=datetime.now(),
            requires_response=requires_response,
            response_options=response_options
        )

class FeedbackLoop:
    """Manages real-time feedback for tasks and workflows."""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self._subscribers: Dict[str, List[Callable]] = {}
        self._task_feedback: Dict[str, List[FeedbackEvent]] = {}
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._logger = get_logger(self.__class__.__name__)

    async def emit(
        self,
        task_id: str,
        level: FeedbackLevel,
        message: str,
        details: Dict[str, Any] = None
    ) -> None:
        """Emit a feedback event."""
        event = FeedbackEvent.create(
            task_id=task_id,
            level=level,
            message=message,
            details=details
        )
        
        # Store feedback
        if task_id not in self._task_feedback:
            self._task_feedback[task_id] = []
        self._task_feedback[task_id].append(event)
        
        # Notify subscribers
        await self._notify_subscribers(event)
        
        # Record metrics
        self.metrics.record(
            name="feedback_events",
            value=1,
            metric_type="counter",
            component="feedback_loop",
            labels={"level": level.value}
        )

    async def request_user_input(
        self,
        task_id: str,
        message: str,
        options: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ) -> Optional[str]:
        """Request input from the user with optional timeout."""
        event = FeedbackEvent.create(
            task_id=task_id,
            level=FeedbackLevel.SUGGESTION,
            message=message,
            requires_response=True,
            response_options=options
        )
        
        # Create future for response
        response_future = asyncio.Future()
        self._pending_responses[event.id] = response_future
        
        # Notify subscribers
        await self._notify_subscribers(event)
        
        try:
            # Wait for response with optional timeout
            if timeout:
                response = await asyncio.wait_for(response_future, timeout)
            else:
                response = await response_future
            return response
            
        except asyncio.TimeoutError:
            self._logger.warning(f"User input request timed out for task {task_id}")
            return None
            
        finally:
            self._pending_responses.pop(event.id, None)

    def submit_response(self, event_id: str, response: str) -> None:
        """Submit a response to a pending user input request."""
        if event_id in self._pending_responses:
            future = self._pending_responses[event_id]
            if not future.done():
                future.set_result(response)

    def subscribe(
        self,
        callback: Callable[[FeedbackEvent], None],
        task_id: Optional[str] = None
    ) -> None:
        """Subscribe to feedback events."""
        key = task_id or "global"
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(callback)

    def unsubscribe(
        self,
        callback: Callable[[FeedbackEvent], None],
        task_id: Optional[str] = None
    ) -> None:
        """Unsubscribe from feedback events."""
        key = task_id or "global"
        if key in self._subscribers:
            self._subscribers[key] = [
                cb for cb in self._subscribers[key]
                if cb != callback
            ]

    async def _notify_subscribers(self, event: FeedbackEvent) -> None:
        """Notify all relevant subscribers of a feedback event."""
        # Notify task-specific subscribers
        for callback in self._subscribers.get(event.task_id, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self._logger.error(f"Error in feedback callback: {str(e)}")
        
        # Notify global subscribers
        for callback in self._subscribers.get("global", []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self._logger.error(f"Error in feedback callback: {str(e)}")

    def get_task_feedback(
        self,
        task_id: str,
        level: Optional[FeedbackLevel] = None
    ) -> List[FeedbackEvent]:
        """Get all feedback events for a task."""
        events = self._task_feedback.get(task_id, [])
        if level:
            events = [e for e in events if e.level == level]
        return sorted(events, key=lambda x: x.timestamp)

    def export_feedback(self, filepath: str) -> None:
        """Export all feedback to a JSON file."""
        data = {
            task_id: [asdict(event) for event in events]
            for task_id, events in self._task_feedback.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
