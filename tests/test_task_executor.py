"""Tests for the Task Executor component."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
import asyncio

from core.interfaces import Task
from core.task_executor import TaskExecutor, TaskStatus, TaskResult

@pytest.fixture
def mock_agent():
    agent = Mock()
    agent.execute = AsyncMock()
    return agent

@pytest.fixture
def task_executor():
    return TaskExecutor(
        max_retries=2,
        retry_delay=0.1,
        timeout=1.0,
        max_concurrent_tasks=2
    )

@pytest.fixture
def sample_task():
    return Task(
        action="test_action",
        parameters={"param": "value"},
        dependencies=None,
        priority=1
    )

class TestTaskExecutor:
    @pytest.mark.asyncio
    async def test_successful_task_execution(self, task_executor, mock_agent, sample_task):
        # Setup
        expected_result = {"status": "success"}
        mock_agent.execute.return_value = expected_result
        
        # Execute
        result = await task_executor.execute_task(sample_task, mock_agent)
        
        # Assert
        assert result.status == TaskStatus.COMPLETED
        assert result.result == expected_result
        assert result.attempts == 1
        assert result.error is None
        assert isinstance(result.start_time, datetime)
        assert isinstance(result.end_time, datetime)
        assert result.duration >= 0
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, task_executor, mock_agent, sample_task):
        # Setup - fail twice, succeed on third try
        mock_agent.execute.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            {"status": "success"}
        ]
        
        # Execute
        result = await task_executor.execute_task(sample_task, mock_agent)
        
        # Assert
        assert result.status == TaskStatus.COMPLETED
        assert result.attempts == 3
        assert mock_agent.execute.call_count == 3
    
    @pytest.mark.asyncio
    async def test_task_timeout(self, task_executor, mock_agent, sample_task):
        # Setup - simulate timeout
        async def slow_execution(*args):
            await asyncio.sleep(2)  # Longer than timeout
            return {"status": "success"}
        
        mock_agent.execute.side_effect = slow_execution
        
        # Execute
        result = await task_executor.execute_task(sample_task, mock_agent)
        
        # Assert
        assert result.status == TaskStatus.FAILED
        assert isinstance(result.error, TimeoutError)
    
    @pytest.mark.asyncio
    async def test_execute_multiple_tasks(self, task_executor, mock_agent):
        # Setup
        tasks = [
            Task(action="task1", parameters={}, dependencies=None),
            Task(action="task2", parameters={}, dependencies=["task1"])
        ]
        
        agents = {
            "task1": mock_agent,
            "task2": mock_agent
        }
        
        mock_agent.execute.return_value = {"status": "success"}
        
        # Execute
        results = await task_executor.execute_tasks(tasks, agents)
        
        # Assert
        assert len(results) == 2
        assert all(r.status == TaskStatus.COMPLETED for r in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self, task_executor, mock_agent):
        # Setup
        async def delayed_execution(*args):
            await asyncio.sleep(0.1)
            return {"status": "success"}
        
        mock_agent.execute.side_effect = delayed_execution
        
        tasks = [
            Task(action="task1", parameters={}, dependencies=None),
            Task(action="task2", parameters={}, dependencies=None),
            Task(action="task3", parameters={}, dependencies=None)
        ]
        
        agents = {f"task{i+1}": mock_agent for i in range(3)}
        
        # Execute
        start_time = datetime.now()
        results = await task_executor.execute_tasks(tasks, agents)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Assert
        assert len(results) == 3
        assert all(r.status == TaskStatus.COMPLETED for r in results)
        # With max_concurrent_tasks=2, it should take at least 2 rounds
        assert duration >= 0.2  # Two rounds of 0.1 seconds each
