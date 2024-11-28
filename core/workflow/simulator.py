"""Workflow simulation and testing framework for Arcana."""

from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime
import asyncio
import json
import yaml
from dataclasses import dataclass
from pathlib import Path

from core.workflow.executor import WorkflowExecutor, WorkflowState
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.feedback_loop import FeedbackLoop, FeedbackLevel

@dataclass
class SimulationConfig:
    """Configuration for workflow simulation."""
    
    mock_data: Dict[str, Any]
    delay_factor: float = 1.0  # Multiplier for simulated task duration
    failure_scenarios: Dict[str, List[Dict[str, Any]]] = None
    validation_rules: Dict[str, Callable[[Any], bool]] = None
    breakpoints: List[str] = None  # Step IDs to pause at

class SimulationResult:
    """Results from a workflow simulation."""
    
    def __init__(self):
        self.steps: List[Dict[str, Any]] = []
        self.anomalies: List[Dict[str, Any]] = []
        self.validation_failures: List[Dict[str, Any]] = []
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        
    def add_step_result(self, step_id: str, result: Dict[str, Any]) -> None:
        """Record a step execution result."""
        self.steps.append({
            "step_id": step_id,
            "timestamp": datetime.now().isoformat(),
            "result": result
        })
        
    def add_anomaly(self, step_id: str, description: str, data: Dict[str, Any]) -> None:
        """Record an anomaly in execution."""
        self.anomalies.append({
            "step_id": step_id,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "data": data
        })
        
    def add_validation_failure(
        self,
        step_id: str,
        expected: Any,
        actual: Any,
        rule_name: str
    ) -> None:
        """Record a validation rule failure."""
        self.validation_failures.append({
            "step_id": step_id,
            "timestamp": datetime.now().isoformat(),
            "rule_name": rule_name,
            "expected": expected,
            "actual": actual
        })
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary."""
        return {
            "steps": self.steps,
            "anomalies": self.anomalies,
            "validation_failures": self.validation_failures,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": (
                (self.end_time - self.start_time).total_seconds()
                if self.end_time
                else None
            )
        }

class WorkflowSimulator(WorkflowExecutor):
    """Simulates workflow execution with mock data and controlled progression."""
    
    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        error_handler: Optional[ErrorHandler] = None,
        feedback_loop: Optional[FeedbackLoop] = None
    ):
        super().__init__(metrics_collector, error_handler, feedback_loop)
        self._simulation_results: Dict[str, SimulationResult] = {}
        self._breakpoint_handlers: Dict[str, Callable[[], Awaitable[None]]] = {}
        self._paused_workflows: Dict[str, asyncio.Event] = {}
        
    async def simulate_workflow(
        self,
        workflow_id: str,
        config: SimulationConfig
    ) -> SimulationResult:
        """Run a workflow in simulation mode."""
        result = SimulationResult()
        self._simulation_results[workflow_id] = result
        
        try:
            # Start workflow with simulation flag
            await self.start_workflow(
                workflow_id,
                {"simulation_mode": True, **config.mock_data}
            )
            
            state = self._active_workflows[workflow_id]
            
            # Process each step with simulated data
            for step in state.steps:
                step_id = step["id"]
                
                # Check for breakpoint
                if config.breakpoints and step_id in config.breakpoints:
                    await self._handle_breakpoint(workflow_id, step_id)
                
                # Inject mock data
                mock_data = config.mock_data.get(step_id, {})
                step["payload"].update(mock_data)
                
                # Simulate execution delay
                await asyncio.sleep(
                    step.get("estimated_duration", 1.0) * config.delay_factor
                )
                
                # Execute step
                try:
                    step_result = await self._execute_simulated_step(
                        workflow_id,
                        step,
                        config
                    )
                    result.add_step_result(step_id, step_result)
                    
                except Exception as e:
                    if self.error_handler:
                        await self.error_handler.handle_error(
                            e,
                            {
                                "component": "WorkflowSimulator",
                                "operation": "simulate_step",
                                "workflow_id": workflow_id,
                                "step_id": step_id
                            }
                        )
                    raise
                
                # Validate step output
                if config.validation_rules and step_id in config.validation_rules:
                    rule = config.validation_rules[step_id]
                    if not rule(step_result):
                        result.add_validation_failure(
                            step_id,
                            "Expected validation rule to pass",
                            step_result,
                            rule.__name__
                        )
                
            await self.update_workflow(workflow_id, "completed")
            
        except Exception as e:
            await self.update_workflow(
                workflow_id,
                "failed",
                {"error": str(e)}
            )
            raise
            
        finally:
            result.end_time = datetime.now()
            
        return result
    
    async def _execute_simulated_step(
        self,
        workflow_id: str,
        step: Dict[str, Any],
        config: SimulationConfig
    ) -> Dict[str, Any]:
        """Execute a single step in simulation mode."""
        step_id = step["id"]
        
        # Check for failure scenario
        if (
            config.failure_scenarios
            and step_id in config.failure_scenarios
        ):
            scenario = config.failure_scenarios[step_id]
            if scenario["type"] == "error":
                raise Exception(scenario["message"])
            elif scenario["type"] == "delay":
                await asyncio.sleep(scenario["duration"])
            
        # Simulate step execution
        result = {
            "status": "completed",
            "output": step["payload"],
            "timestamp": datetime.now().isoformat()
        }
        
        await self.update_agent_state(
            workflow_id,
            step["agent"],
            "completed",
            {"step_result": result}
        )
        
        return result
    
    async def _handle_breakpoint(self, workflow_id: str, step_id: str) -> None:
        """Handle a workflow breakpoint."""
        if workflow_id not in self._paused_workflows:
            self._paused_workflows[workflow_id] = asyncio.Event()
            
        if self.feedback_loop:
            await self.feedback_loop.emit(
                task_id=workflow_id,
                level=FeedbackLevel.INFO,
                message=f"Simulation paused at step {step_id}",
                details={"step_id": step_id}
            )
            
        # Wait for resume signal
        await self._paused_workflows[workflow_id].wait()
        self._paused_workflows[workflow_id].clear()
        
    async def resume_workflow(self, workflow_id: str) -> None:
        """Resume a paused workflow simulation."""
        if workflow_id in self._paused_workflows:
            self._paused_workflows[workflow_id].set()
            
    def get_simulation_result(self, workflow_id: str) -> Optional[SimulationResult]:
        """Get results from a simulation run."""
        return self._simulation_results.get(workflow_id)
        
    @staticmethod
    def load_mock_data(path: Path) -> Dict[str, Any]:
        """Load mock data from a YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)
