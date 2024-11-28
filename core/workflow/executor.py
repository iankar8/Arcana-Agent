"""Workflow execution and state tracking for the Arcana Agent Framework."""

from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
import json

from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.feedback_loop import FeedbackLoop

@dataclass
class WorkflowState:
    """Represents the current state of a workflow."""
    
    workflow_id: str
    status: str
    start_time: datetime
    agents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "agents": self.agents,
            "steps": self.steps,
            "interactions": self.interactions,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Create state from dictionary."""
        return cls(
            workflow_id=data["workflow_id"],
            status=data["status"],
            start_time=datetime.fromisoformat(data["start_time"]),
            agents=data.get("agents", {}),
            steps=data.get("steps", []),
            interactions=data.get("interactions", []),
            metadata=data.get("metadata", {}),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        )

class WorkflowExecutor:
    """Manages workflow execution and state tracking."""
    
    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        error_handler: Optional[ErrorHandler] = None,
        feedback_loop: Optional[FeedbackLoop] = None
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.feedback_loop = feedback_loop
        self._active_workflows: Dict[str, WorkflowState] = {}
        self._state_listeners: List[Callable[[str, WorkflowState], Awaitable[None]]] = []
        
    def on_state_change(
        self,
        callback: Callable[[str, WorkflowState], Awaitable[None]]
    ) -> None:
        """Register a state change listener."""
        self._state_listeners.append(callback)
        
    async def _notify_state_change(self, workflow_id: str) -> None:
        """Notify listeners of state change."""
        if workflow_id not in self._active_workflows:
            return
            
        state = self._active_workflows[workflow_id]
        for listener in self._state_listeners:
            try:
                await listener(workflow_id, state)
            except Exception as e:
                if self.error_handler:
                    await self.error_handler.handle_error(
                        e,
                        {
                            "component": "WorkflowExecutor",
                            "operation": "notify_state_change",
                            "workflow_id": workflow_id
                        }
                    )
                    
    async def start_workflow(
        self,
        workflow_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Start a new workflow."""
        state = WorkflowState(
            workflow_id=workflow_id,
            status="started",
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self._active_workflows[workflow_id] = state
        
        if self.metrics:
            self.metrics.increment_counter(
                "workflows_started",
                {"workflow_id": workflow_id}
            )
            
        await self._notify_state_change(workflow_id)
        
    async def update_workflow(
        self,
        workflow_id: str,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update workflow state."""
        if workflow_id not in self._active_workflows:
            return
            
        state = self._active_workflows[workflow_id]
        
        if status:
            state.status = status
            
        if metadata:
            state.metadata.update(metadata)
            
        if status == "completed":
            state.end_time = datetime.now()
            
            if self.metrics:
                duration = (state.end_time - state.start_time).total_seconds()
                self.metrics.record_value(
                    "workflow_duration_seconds",
                    duration,
                    {"workflow_id": workflow_id}
                )
                
        await self._notify_state_change(workflow_id)
        
    async def record_interaction(
        self,
        workflow_id: str,
        from_agent: str,
        to_agent: str,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an interaction between agents."""
        if workflow_id not in self._active_workflows:
            return
            
        state = self._active_workflows[workflow_id]
        
        interaction = {
            "from": from_agent,
            "to": to_agent,
            "type": interaction_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        state.interactions.append(interaction)
        await self._notify_state_change(workflow_id)
        
    async def update_agent_state(
        self,
        workflow_id: str,
        agent_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update agent state within a workflow."""
        if workflow_id not in self._active_workflows:
            return
            
        state = self._active_workflows[workflow_id]
        
        if agent_id not in state.agents:
            state.agents[agent_id] = {}
            
        state.agents[agent_id].update({
            "status": status,
            **(metadata or {})
        })
        
        await self._notify_state_change(workflow_id)
        
    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get current state of a workflow."""
        return self._active_workflows.get(workflow_id)
        
    def get_active_workflows(self) -> List[str]:
        """Get IDs of all active workflows."""
        return list(self._active_workflows.keys())
