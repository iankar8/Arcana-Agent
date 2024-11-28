"""Task Coordination Agent for managing task execution and dependencies."""

from typing import Dict, Any, Optional, List, Set
import asyncio
from datetime import datetime, timedelta
import uuid

from core.interfaces import Agent
from core.monitoring import MetricsCollector, MetricType, Timer
from core.error_handling import ErrorHandler, ErrorCategory, RecoveryStrategy
from core.caching import Cache, CacheStrategy
from core.logging_config import get_logger

logger = get_logger(__name__)

class TaskStatus:
    """Task execution status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Task:
    """Represents a task in the system."""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        coroutine: Any,
        dependencies: Set[str],
        priority: int = 1,
        timeout: Optional[float] = None
    ):
        self.task_id = task_id
        self.name = name
        self.coroutine = coroutine
        self.dependencies = dependencies
        self.priority = priority
        self.timeout = timeout
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Optional[Any] = None

class CoordinatorAgent(Agent):
    """Agent responsible for coordinating task execution."""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler,
        max_concurrent_tasks: int = 10,
        task_history_size: int = 1000
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Task tracking
        self.pending_tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks = Cache[Task](
            max_size=task_history_size,
            strategy=CacheStrategy.LRU,
            default_ttl=timedelta(hours=24)
        )
        
        # Semaphore for controlling concurrent tasks
        self._task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Configure error handling
        self.error_handler.set_recovery_strategy(
            ErrorCategory.TASK,
            RecoveryStrategy.RETRY
        )
        
        self.logger = get_logger(self.__class__.__name__)
    
    async def start(self) -> None:
        """Start the coordinator."""
        await self.completed_tasks.start()
        self.logger.info("Task coordinator started")
    
    async def stop(self) -> None:
        """Stop the coordinator."""
        # Cancel all running tasks
        for task_id in list(self.running_tasks.keys()):
            await self.cancel_task(task_id)
        
        await self.completed_tasks.stop()
        self.logger.info("Task coordinator stopped")
    
    async def submit_task(
        self,
        name: str,
        coroutine: Any,
        dependencies: Optional[Set[str]] = None,
        priority: int = 1,
        timeout: Optional[float] = None
    ) -> str:
        """Submit a new task for execution."""
        try:
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                name=name,
                coroutine=coroutine,
                dependencies=dependencies or set(),
                priority=priority,
                timeout=timeout
            )
            
            self.pending_tasks[task_id] = task
            
            # Record metrics
            self.metrics.record(
                name="task_submissions",
                value=1,
                metric_type=MetricType.COUNTER,
                component="coordinator_agent",
                labels={"priority": str(priority)}
            )
            
            # Start task if dependencies are met
            if not task.dependencies:
                asyncio.create_task(self._execute_task(task_id))
            
            return task_id
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "coordinator_agent",
                    "operation": "submit_task",
                    "task_name": name
                }
            )
            raise
    
    async def _execute_task(self, task_id: str) -> None:
        """Execute a task with proper monitoring and error handling."""
        task = self.pending_tasks.pop(task_id)
        self.running_tasks[task_id] = task
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            async with Timer(
                "task_execution",
                "coordinator_agent",
                self.metrics,
                {"task_name": task.name}
            ):
                async with self._task_semaphore:
                    if task.timeout:
                        result = await asyncio.wait_for(task.coroutine, task.timeout)
                    else:
                        result = await task.coroutine
                    
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    
                    # Record success metrics
                    self.metrics.record(
                        name="task_completions",
                        value=1,
                        metric_type=MetricType.COUNTER,
                        component="coordinator_agent",
                        labels={"task_name": task.name}
                    )
                    
        except asyncio.TimeoutError as e:
            task.status = TaskStatus.FAILED
            task.error = "TimeoutError: Task execution exceeded timeout limit"
            await self.error_handler.handle_error(
                e,
                {
                    "component": "coordinator_agent",
                    "operation": "execute_task",
                    "task_id": task_id,
                    "task_name": task.name,
                    "error_type": "timeout"
                }
            )
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await self.error_handler.handle_error(
                e,
                {
                    "component": "coordinator_agent",
                    "operation": "execute_task",
                    "task_id": task_id,
                    "task_name": task.name
                }
            )
            
        finally:
            task.completed_at = datetime.now()
            self.running_tasks.pop(task_id)
            await self.completed_tasks.set(task_id, task)
            
            # Check for dependent tasks
            await self._check_dependent_tasks(task_id)
    
    async def _check_dependent_tasks(self, completed_task_id: str) -> None:
        """Check and start tasks that were waiting on the completed task."""
        for task_id, task in list(self.pending_tasks.items()):
            if completed_task_id in task.dependencies:
                task.dependencies.remove(completed_task_id)
                if not task.dependencies:
                    # All dependencies met, start the task
                    asyncio.create_task(self._execute_task(task_id))
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task by ID."""
        try:
            if task_id in self.pending_tasks:
                task = self.pending_tasks.pop(task_id)
                task.status = TaskStatus.CANCELLED
                await self.completed_tasks.set(task_id, task)
                return True
                
            elif task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                self.running_tasks.pop(task_id)
                await self.completed_tasks.set(task_id, task)
                return True
                
            return False
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "coordinator_agent",
                    "operation": "cancel_task",
                    "task_id": task_id
                }
            )
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a task."""
        try:
            task = (
                self.pending_tasks.get(task_id) or
                self.running_tasks.get(task_id) or
                await self.completed_tasks.get(task_id)
            )
            
            if not task:
                return None
            
            status = {
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.error,
                "dependencies": list(task.dependencies),
                "result": task.result
            }
            
            return status
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "coordinator_agent",
                    "operation": "get_task_status",
                    "task_id": task_id
                }
            )
            return None
    
    async def get_task_metrics(self) -> Dict[str, Any]:
        """Get current task execution metrics."""
        try:
            metrics = {
                "pending_tasks": len(self.pending_tasks),
                "running_tasks": len(self.running_tasks),
                "completed_tasks": len(self.completed_tasks._cache),
                "task_semaphore_value": self._task_semaphore._value,
            }
            
            # Record metrics
            for name, value in metrics.items():
                self.metrics.record(
                    name=f"task_{name}",
                    value=value,
                    metric_type=MetricType.GAUGE,
                    component="coordinator_agent"
                )
            
            return metrics
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "coordinator_agent",
                    "operation": "get_task_metrics"
                }
            )
            return {}
