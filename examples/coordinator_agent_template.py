"""Template for creating coordinator agents that manage other agents."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from core.interfaces import Agent
from core.protocol import Message
from core.user_profile import UserProfile, Action
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler

class CoordinatorAgent(Agent):
    """Base template for coordinator agents."""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler,
        user_profile: UserProfile,
        agent_registry: 'AgentRegistry',
        **kwargs
    ):
        super().__init__(metrics_collector, error_handler, **kwargs)
        self.user_profile = user_profile
        self.agent_registry = agent_registry
        self.workflows: Dict[str, Dict[str, Any]] = {}

    async def on_start(self) -> None:
        """Initialize workflow tracking."""
        self._logger.info("Coordinator agent starting...")
        self.metrics.record(
            name="agent_starts",
            value=1,
            metric_type="counter",
            component=self.__class__.__name__
        )

    async def on_stop(self) -> None:
        """Clean up any active workflows."""
        self._logger.info("Coordinator agent stopping...")
        for workflow_id in list(self.workflows.keys()):
            await self._cancel_workflow(workflow_id)

    async def on_message(self, message: Message) -> None:
        """Handle incoming workflow-related messages."""
        try:
            if message.intent == "start_workflow":
                await self._handle_start_workflow(message)
            elif message.intent == "cancel_workflow":
                await self._handle_cancel_workflow(message)
            elif message.intent == "get_workflow_status":
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

    async def _handle_start_workflow(self, message: Message) -> None:
        """Handle workflow start requests."""
        workflow_name = message.payload.get("workflow_name")
        if not workflow_name:
            raise ValueError("Workflow name is required")

        # Create workflow tracking
        action = Action.create(
            type="workflow_started",
            description=f"Started workflow: {workflow_name}",
            metadata=message.payload
        )
        self.user_profile.log_action(action)

        workflow_steps = message.payload.get("steps", [])
        self.workflows[action.id] = {
            "name": workflow_name,
            "status": "running",
            "steps": workflow_steps,
            "current_step": 0,
            "started_at": datetime.now(),
            "metadata": message.payload
        }

        # Start executing workflow steps
        asyncio.create_task(self._execute_workflow(action.id))

        self.metrics.record(
            name="workflows_started",
            value=1,
            metric_type="counter",
            component=self.__class__.__name__
        )

    async def _execute_workflow(self, workflow_id: str) -> None:
        """Execute workflow steps sequentially."""
        workflow = self.workflows[workflow_id]
        
        try:
            for i, step in enumerate(workflow["steps"]):
                if workflow["status"] != "running":
                    break

                workflow["current_step"] = i
                agent_name = step.get("agent")
                agent = self.agent_registry.get_agent(agent_name)
                
                if not agent:
                    raise ValueError(f"Agent not found: {agent_name}")

                # Create message for the agent
                message = Message.create(
                    intent=step.get("intent", "execute"),
                    agent=agent_name,
                    payload=step.get("payload", {})
                )

                # Send message and wait for completion
                await self.agent_registry.send_message(message)

            workflow["status"] = "completed"
            self._logger.info(f"Workflow {workflow_id} completed successfully")

        except Exception as e:
            workflow["status"] = "failed"
            workflow["error"] = str(e)
            self._logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            raise

    async def _handle_cancel_workflow(self, message: Message) -> None:
        """Handle workflow cancellation requests."""
        workflow_id = message.payload.get("workflow_id")
        if not workflow_id or workflow_id not in self.workflows:
            raise ValueError("Invalid workflow ID")

        await self._cancel_workflow(workflow_id)

    async def _cancel_workflow(self, workflow_id: str) -> None:
        """Cancel a workflow and update tracking."""
        if workflow_id in self.workflows:
            self.workflows[workflow_id]["status"] = "cancelled"
            
            action = Action.create(
                type="workflow_cancelled",
                description=f"Cancelled workflow: {self.workflows[workflow_id]['name']}",
                metadata={"workflow_id": workflow_id}
            )
            self.user_profile.log_action(action)

            self.metrics.record(
                name="workflows_cancelled",
                value=1,
                metric_type="counter",
                component=self.__class__.__name__
            )

    async def _handle_get_status(self, message: Message) -> None:
        """Handle workflow status requests."""
        workflow_id = message.payload.get("workflow_id")
        if not workflow_id or workflow_id not in self.workflows:
            raise ValueError("Invalid workflow ID")

        workflow = self.workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "name": workflow["name"],
            "status": workflow["status"],
            "current_step": workflow["current_step"],
            "total_steps": len(workflow["steps"])
        }
