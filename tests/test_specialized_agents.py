"""Tests for specialized agents in the Arcana framework."""

import pytest
import asyncio
import psutil
from datetime import timedelta
from typing import Dict, Any

from agents.memory_agent import MemoryAgent
from agents.resource_agent import ResourceAgent, ResourceThresholds
from agents.coordinator_agent import CoordinatorAgent, TaskStatus
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler

@pytest.fixture
async def metrics_collector():
    collector = MetricsCollector()
    await collector.start()
    yield collector
    await collector.stop()

@pytest.fixture
async def error_handler():
    handler = ErrorHandler()
    await handler.start()
    yield handler
    await handler.stop()

@pytest.fixture
async def memory_agent(metrics_collector, error_handler):
    agent = MemoryAgent(metrics_collector, error_handler)
    await agent.start()
    yield agent
    await agent.stop()

@pytest.fixture
async def resource_agent(metrics_collector, error_handler):
    agent = ResourceAgent(metrics_collector, error_handler)
    await agent.start()
    yield agent
    await agent.stop()

@pytest.fixture
async def coordinator_agent(metrics_collector, error_handler):
    agent = CoordinatorAgent(metrics_collector, error_handler)
    await agent.start()
    yield agent
    await agent.stop()

# Memory Agent Tests
async def test_memory_store_retrieve(memory_agent):
    """Test basic memory storage and retrieval."""
    test_data = {"key": "value", "number": 42}
    await memory_agent.store_memory("test_key", test_data)
    
    retrieved = await memory_agent.retrieve_memory("test_key")
    assert retrieved == test_data

async def test_memory_long_term_storage(memory_agent):
    """Test long-term memory storage."""
    test_data = {"important": "data"}
    await memory_agent.store_memory("long_term_key", test_data, long_term=True)
    
    retrieved = await memory_agent.retrieve_memory("long_term_key", long_term=True)
    assert retrieved == test_data

async def test_memory_consolidation(memory_agent):
    """Test memory consolidation process."""
    # Store and access memory multiple times to increase hit count
    test_data = {"consolidate": "me"}
    key = "consolidate_key"
    
    await memory_agent.store_memory(key, test_data)
    for _ in range(6):  # Ensure enough hits for consolidation
        await memory_agent.retrieve_memory(key)
    
    await memory_agent.consolidate_memories()
    
    # Should now be in long-term memory
    long_term_data = await memory_agent.retrieve_memory(key, long_term=True)
    assert long_term_data == test_data

async def test_memory_search(memory_agent):
    """Test memory search functionality."""
    await memory_agent.store_memory("key1", {"content": "apple"})
    await memory_agent.store_memory("key2", {"content": "banana"})
    await memory_agent.store_memory("key3", {"content": "apple pie"})
    
    results = await memory_agent.search_memories("apple")
    assert len(results) == 2

# Resource Agent Tests
async def test_resource_monitoring(resource_agent):
    """Test resource monitoring functionality."""
    # Force a resource check
    await resource_agent._check_resources()
    
    # Get resource report
    report = await resource_agent.get_resource_report()
    
    assert "cpu" in report
    assert "memory" in report
    assert "disk" in report
    assert "process" in report

async def test_resource_thresholds(resource_agent, monkeypatch):
    """Test resource threshold detection."""
    # Mock high CPU usage
    def mock_cpu_percent(*args, **kwargs):
        return 95.0
    
    monkeypatch.setattr(psutil, "cpu_percent", mock_cpu_percent)
    
    # Trigger resource check
    await resource_agent._check_resources()
    await resource_agent._handle_resource_issues()
    
    # Check if critical CPU was detected (through aggregator)
    stats = resource_agent.metrics.aggregator.get_statistics("system_cpu_percent")
    assert stats.get("max", 0) >= 95.0

# Coordinator Agent Tests
async def test_task_submission_execution(coordinator_agent):
    """Test basic task submission and execution."""
    async def sample_task():
        await asyncio.sleep(0.1)
        return "completed"
    
    task_id = await coordinator_agent.submit_task(
        name="test_task",
        coroutine=sample_task()
    )
    
    # Wait for task completion
    await asyncio.sleep(0.2)
    
    status = await coordinator_agent.get_task_status(task_id)
    assert status["status"] == TaskStatus.COMPLETED
    assert status["result"] == "completed"

async def test_task_dependencies(coordinator_agent):
    """Test task dependency management."""
    results = []
    
    async def task1():
        await asyncio.sleep(0.1)
        results.append(1)
        return "task1"
    
    async def task2():
        results.append(2)
        return "task2"
    
    # Submit task2 with task1 as dependency
    task1_id = await coordinator_agent.submit_task(
        name="task1",
        coroutine=task1()
    )
    
    await coordinator_agent.submit_task(
        name="task2",
        coroutine=task2(),
        dependencies={task1_id}
    )
    
    # Wait for both tasks
    await asyncio.sleep(0.3)
    
    # Check execution order
    assert results == [1, 2]

async def test_task_cancellation(coordinator_agent):
    """Test task cancellation."""
    async def long_task():
        await asyncio.sleep(10)
        return "never_complete"
    
    task_id = await coordinator_agent.submit_task(
        name="long_task",
        coroutine=long_task()
    )
    
    # Cancel the task
    success = await coordinator_agent.cancel_task(task_id)
    assert success
    
    status = await coordinator_agent.get_task_status(task_id)
    assert status["status"] == TaskStatus.CANCELLED

async def test_task_timeout(coordinator_agent):
    """Test task timeout handling."""
    async def slow_task():
        await asyncio.sleep(1)
        return "too_late"
    
    task_id = await coordinator_agent.submit_task(
        name="slow_task",
        coroutine=slow_task(),
        timeout=0.1
    )
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    status = await coordinator_agent.get_task_status(task_id)
    assert status["status"] == TaskStatus.FAILED
    assert "TimeoutError" in status["error"]

# Integration Tests
async def test_agent_integration(memory_agent, resource_agent, coordinator_agent):
    """Test integration between agents."""
    # Create a task that stores resource info in memory
    async def monitor_and_store():
        report = await resource_agent.get_resource_report()
        key = f"resource_report_{report['timestamp']}"
        await memory_agent.store_memory(
            key,
            report,
            long_term=True
        )
        return report

    # Submit the task
    task_id = await coordinator_agent.submit_task(
        name="monitor_resources",
        coroutine=monitor_and_store()
    )

    # Wait for completion
    await asyncio.sleep(0.2)

    # Verify task completion
    status = await coordinator_agent.get_task_status(task_id)
    assert status["status"] == TaskStatus.COMPLETED

    # Wait for memory consolidation
    await asyncio.sleep(0.1)  # Give time for memory operations to complete
    
    # Search for the stored report
    results = await memory_agent.search_memories("resource_report", long_term=True)
    assert len(results) > 0
