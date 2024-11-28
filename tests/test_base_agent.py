import pytest
import pytest_asyncio
from agents.base_agent import BaseAgent
from tools.base_tool import BaseTool

class MockTool(BaseTool):
    def __init__(self):
        self.initialized = False
        self.cleaned_up = False
        self.executed = False
        
    def initialize(self) -> None:
        self.initialized = True
        
    async def execute(self, params):
        self.executed = True
        return {'status': 'success', 'result': params}
        
    async def cleanup(self) -> None:
        self.cleaned_up = True

class TestAgent(BaseAgent):
    async def execute_task(self, task):
        tool_name = task.get('tool')
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        return await self.tools[tool_name].execute(task.get('params', {}))

class TestBaseAgent:
    @pytest.fixture
    def agent(self):
        return TestAgent()
        
    @pytest.fixture
    def mock_tool(self):
        return MockTool()
        
    def test_register_tool(self, agent, mock_tool):
        agent.register_tool('mock', mock_tool)
        assert 'mock' in agent.tools
        assert agent.tools['mock'] == mock_tool
        
    def test_register_duplicate_tool(self, agent, mock_tool):
        agent.register_tool('mock', mock_tool)
        with pytest.raises(ValueError):
            agent.register_tool('mock', mock_tool)
            
    @pytest.mark.asyncio
    async def test_initialize(self, agent, mock_tool):
        agent.register_tool('mock', mock_tool)
        await agent.initialize()
        assert mock_tool.initialized
        
    @pytest.mark.asyncio
    async def test_cleanup(self, agent, mock_tool):
        agent.register_tool('mock', mock_tool)
        await agent.cleanup()
        assert mock_tool.cleaned_up
        
    @pytest.mark.asyncio
    async def test_execute_task(self, agent, mock_tool):
        agent.register_tool('mock', mock_tool)
        task = {'tool': 'mock', 'params': {'test': 'value'}}
        result = await agent.execute_task(task)
        assert result['status'] == 'success'
        assert result['result']['test'] == 'value'
        assert mock_tool.executed
        
    @pytest.mark.asyncio
    async def test_execute_task_invalid_tool(self, agent):
        task = {'tool': 'invalid', 'params': {}}
        with pytest.raises(ValueError):
            await agent.execute_task(task)
