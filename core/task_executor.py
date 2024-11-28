"""Task Execution Layer for Arcana Agent Framework."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import traceback

from .interfaces import Task
from .logging_config import get_logger

logger = get_logger(__name__)

class TaskStatus:
    """Represents the current status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class TaskResult:
    """Represents the result of a task execution."""
    
    def __init__(
        self,
        task: Task,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        attempts: int = 0
    ):
        self.task = task
        self.status = status
        self.result = result
        self.error = error
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.attempts = attempts
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task result to dictionary."""
        return {
            "task_action": self.task.action,
            "status": self.status,
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "attempts": self.attempts
        }

class TaskExecutor:
    """Manages the execution of tasks with retry and error handling."""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        max_concurrent_tasks: int = 5
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.logger = get_logger(self.__class__.__name__)
    
    async def execute_task(self, task: Task, agent: Any) -> TaskResult:
        """Execute a single task with retries and error handling."""
        task_result = TaskResult(task, TaskStatus.PENDING)
        
        for attempt in range(self.max_retries + 1):
            task_result.attempts = attempt + 1
            
            try:
                async with self.semaphore:
                    self.logger.info(f"Executing task {task.action} (attempt {attempt + 1}/{self.max_retries + 1})")
                    task_result.status = TaskStatus.RUNNING
                    
                    # Execute task with timeout
                    result = await asyncio.wait_for(
                        agent.execute(task),
                        timeout=self.timeout
                    )
                    
                    task_result.status = TaskStatus.COMPLETED
                    task_result.result = result
                    task_result.end_time = datetime.now()
                    
                    self.logger.info(f"Task {task.action} completed successfully")
                    return task_result
                    
            except asyncio.TimeoutError:
                error_msg = f"Task {task.action} timed out after {self.timeout} seconds"
                self.logger.error(error_msg)
                task_result.error = TimeoutError(error_msg)
                
            except Exception as e:
                error_msg = f"Task {task.action} failed: {str(e)}\n{traceback.format_exc()}"
                self.logger.error(error_msg)
                task_result.error = e
            
            # Handle retry logic
            if attempt < self.max_retries:
                task_result.status = TaskStatus.RETRYING
                self.logger.info(f"Retrying task {task.action} after {self.retry_delay} seconds")
                await asyncio.sleep(self.retry_delay)
            else:
                task_result.status = TaskStatus.FAILED
                self.logger.error(f"Task {task.action} failed after {attempt + 1} attempts")
        
        task_result.end_time = datetime.now()
        return task_result
    
    async def execute_tasks(self, tasks: List[Task], agents: Dict[str, Any]) -> List[TaskResult]:
        """Execute multiple tasks with proper dependency handling."""
        self.logger.info(f"Executing {len(tasks)} tasks")
        results = []
        
        # Group tasks by dependency level
        task_groups = self._group_tasks_by_dependencies(tasks)
        
        # Execute tasks level by level
        for task_group in task_groups:
            group_results = await asyncio.gather(
                *[
                    self.execute_task(task, agents[task.action])
                    for task in task_group
                ],
                return_exceptions=True
            )
            results.extend(group_results)
        
        return results
    
    def _group_tasks_by_dependencies(self, tasks: List[Task]) -> List[List[Task]]:
        """Group tasks by their dependency levels."""
        # Initialize groups
        groups: List[List[Task]] = []
        remaining_tasks = tasks.copy()
        processed_actions = set()
        
        while remaining_tasks:
            # Find tasks with satisfied dependencies
            current_group = [
                task for task in remaining_tasks
                if not task.dependencies or all(dep in processed_actions for dep in task.dependencies)
            ]
            
            if not current_group:
                # Circular dependency or missing dependency
                self.logger.error("Circular or missing dependency detected")
                raise ValueError("Circular or missing dependency detected in tasks")
            
            # Add current group to groups
            groups.append(current_group)
            
            # Update processed actions and remaining tasks
            processed_actions.update(task.action for task in current_group)
            remaining_tasks = [
                task for task in remaining_tasks
                if task not in current_group
            ]
        
        return groups
