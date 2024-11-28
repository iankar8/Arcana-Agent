"""Template for creating task execution agents."""

from typing import Dict, Any, Optional
from datetime import datetime

from core.interfaces import Agent
from core.protocol import Message
from core.user_profile import UserProfile, Action
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler

class TaskAgent(Agent):
    """Base template for task execution agents."""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler,
        user_profile: UserProfile,
        **kwargs
    ):
        super().__init__(metrics_collector, error_handler, **kwargs)
        self.user_profile = user_profile
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    async def on_start(self) -> None:
        """Initialize task tracking."""
        self._logger.info("Task agent starting...")
        self.metrics.record(
            name="agent_starts",
            value=1,
            metric_type="counter",
            component=self.__class__.__name__
        )

    async def on_stop(self) -> None:
        """Clean up any pending tasks."""
        self._logger.info("Task agent stopping...")
        for task_id in list(self.active_tasks.keys()):
            await self._cancel_task(task_id)

    async def on_message(self, message: Message) -> None:
        """Handle incoming task-related messages."""
        try:
            if message.intent == "create_task":
                await self._handle_create_task(message)
            elif message.intent == "cancel_task":
                await self._handle_cancel_task(message)
            elif message.intent == "get_task_status":
                await self._handle_get_status(message)
            else:
                raise ValueError(f"Unknown intent: {message.intent}")

        except Exception as e:
            self._logger.error(f"Error handling message: {str(e)}")
            await self.error_handler.handle_error(
                e,
                {
                    "component": self.__class__.__name__,
                    "operation": "on_message",
                    "message_id": message.id
                }
            )
            raise

    async def _handle_create_task(self, message: Message) -> None:
        """Handle task creation requests."""
        task_name = message.payload.get("task_name")
        if not task_name:
            raise ValueError("Task name is required")

        # Create an action in user profile
        action = Action.create(
            type="task_created",
            description=f"Created task: {task_name}",
            metadata=message.payload
        )
        self.user_profile.log_action(action)

        # Store task details
        self.active_tasks[action.id] = {
            "name": task_name,
            "status": "created",
            "created_at": datetime.now(),
            "metadata": message.payload
        }

        self.metrics.record(
            name="tasks_created",
            value=1,
            metric_type="counter",
            component=self.__class__.__name__
        )

    async def _handle_cancel_task(self, message: Message) -> None:
        """Handle task cancellation requests."""
        task_id = message.payload.get("task_id")
        if not task_id or task_id not in self.active_tasks:
            raise ValueError("Invalid task ID")

        await self._cancel_task(task_id)

    async def _handle_get_status(self, message: Message) -> None:
        """Handle task status requests."""
        task_id = message.payload.get("task_id")
        if not task_id or task_id not in self.active_tasks:
            raise ValueError("Invalid task ID")

        return {
            "task_id": task_id,
            "status": self.active_tasks[task_id]["status"]
        }

    async def _cancel_task(self, task_id: str) -> None:
        """Cancel a task and update relevant tracking."""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "cancelled"
            
            action = Action.create(
                type="task_cancelled",
                description=f"Cancelled task: {self.active_tasks[task_id]['name']}",
                metadata={"task_id": task_id}
            )
            self.user_profile.log_action(action)

            self.metrics.record(
                name="tasks_cancelled",
                value=1,
                metric_type="counter",
                component=self.__class__.__name__
            )
