import pytest
import os
import logging
from unittest.mock import Mock, AsyncMock
from core.interfaces import Intent, Task
from core.components import AnthropicNLU, SimpleTaskPlanner, SmartResponseBuilder

class TestAnthropicNLU:
    @pytest.mark.asyncio
    async def test_parse_valid_query(self, nlu, mock_anthropic_client):
        # Mock the Anthropic response
        mock_message = Mock()
        mock_message.content = [Mock(text='{"name": "test_intent", "confidence": 0.9, "parameters": {"param1": "value1"}}')]
        
        # Use AsyncMock for async method
        mock_anthropic_client.return_value.messages.create = AsyncMock(return_value=mock_message)
        
        intent = await nlu.parse("Test query")
        
        assert isinstance(intent, Intent)
        assert intent.name == "test_intent"
        assert intent.confidence == 0.9
        assert intent.parameters == {"param1": "value1"}
    
    @pytest.mark.asyncio
    async def test_parse_invalid_response(self, nlu, mock_anthropic_client):
        # Mock an invalid response
        mock_message = Mock()
        mock_message.content = [Mock(text='invalid json')]
        mock_anthropic_client.return_value.messages.create.return_value = mock_message
        
        with pytest.raises(Exception):
            await nlu.parse("Test query")

class TestSimpleTaskPlanner:
    @pytest.mark.asyncio
    async def test_plan_simple_intent(self, task_planner):
        intent = Intent(
            name="test_action",
            confidence=0.9,
            parameters={"param1": "value1"}
        )
        
        tasks = await task_planner.plan(intent)
        
        assert len(tasks) == 1
        assert isinstance(tasks[0], Task)
        assert tasks[0].action == "test_action"
        assert tasks[0].parameters == {"param1": "value1"}
    
    @pytest.mark.asyncio
    async def test_validate_dependencies_no_deps(self, task_planner):
        tasks = [
            Task(action="task1", parameters={}, dependencies=None),
            Task(action="task2", parameters={}, dependencies=None)
        ]
        
        assert await task_planner.validate_dependencies(tasks) == True
    
    @pytest.mark.asyncio
    async def test_validate_dependencies_with_valid_deps(self, task_planner):
        tasks = [
            Task(action="task1", parameters={}, dependencies=None),
            Task(action="task2", parameters={}, dependencies=["task1"])
        ]
        
        assert await task_planner.validate_dependencies(tasks) == True
    
    @pytest.mark.asyncio
    async def test_validate_dependencies_with_invalid_deps(self, task_planner):
        tasks = [
            Task(action="task1", parameters={}, dependencies=["non_existent_task"]),
            Task(action="task2", parameters={}, dependencies=None)
        ]
        
        assert await task_planner.validate_dependencies(tasks) == False

class TestSmartResponseBuilder:
    @pytest.mark.asyncio
    async def test_build_response_empty_results(self, response_builder):
        response = await response_builder.build_response([])
        assert response == "No results to report."
    
    @pytest.mark.asyncio
    async def test_build_response_successful_results(self, response_builder):
        results = [
            {
                "action": "test_action",
                "status": "completed",
                "result": "Test completed successfully"
            }
        ]
        
        response = await response_builder.build_response(results)
        assert "Successfully test action" in response
        assert "Test completed successfully" in response
    
    @pytest.mark.asyncio
    async def test_build_error_response(self, response_builder):
        error = Exception("Test error")
        response = await response_builder.build_error_response(error)
        assert "Test error" in response

@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Set up logging for tests."""
    logging.basicConfig(level=logging.DEBUG)
    # Create a test log directory
    os.makedirs("logs", exist_ok=True)
