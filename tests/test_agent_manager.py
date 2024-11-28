import pytest
import pytest_asyncio
from manager.agent_manager import AgentManager
from agents.task_agent import TaskAgent
from tools.browser_tool import BrowserTool

class TestAgentManager:
    @pytest.fixture
    def manager(self):
        return AgentManager()
        
    @pytest.fixture
    def agent(self, manager):
        agent = TaskAgent('test_agent', manager)
        agent.register_tool('browser', BrowserTool())
        return agent
        
    @pytest.fixture
    def other_agent(self, manager):
        agent = TaskAgent('other_agent', manager)
        agent.register_tool('browser', BrowserTool())
        return agent
        
    def test_register_agent(self, manager, agent):
        manager.register_agent(agent)
        assert 'test_agent' in manager.agents
        
    @pytest.mark.asyncio
    async def test_send_message(self, manager, agent):
        manager.register_agent(agent)
        result = await manager.send_message(
            'test_agent',
            'test_agent',
            {'intent': 'find', 'entities': {'query': 'test'}}
        )
        assert result['status'] in ['success', 'error']
        
    def test_task_decomposition(self, manager):
        actions = manager.decompose_tasks(['find'], ['test_entity'])
        assert len(actions) == 1
        assert actions[0]['intent'] == 'find'
        assert 'entities' in actions[0]
        
    @pytest.mark.asyncio
    async def test_deprecate_agent(self, manager, agent):
        manager.register_agent(agent)
        await manager.deprecate_agent('test_agent')
        assert 'test_agent' not in manager.agents
        
    @pytest.mark.asyncio
    async def test_agent_interaction(self, manager, agent, other_agent):
        manager.register_agent(agent)
        manager.register_agent(other_agent)
        result = await manager.send_message(
            'test_agent',
            'other_agent',
            {'intent': 'find', 'entities': {'query': 'test'}}
        )
        assert result['status'] in ['success', 'error']
        
    @pytest.mark.asyncio
    async def test_error_handling(self, manager, agent):
        manager.register_agent(agent)
        result = await manager.send_message(
            'test_agent',
            'test_agent',
            {'intent': 'unknown', 'entities': {}}
        )
        assert result['status'] == 'error'
        assert 'error' in result
        
    @pytest.mark.asyncio
    async def test_task_processing(self, manager, agent):
        manager.register_agent(agent)
        actions = manager.decompose_tasks(['find'], ['test_entity'])
        result = await agent.receive_message('user', actions[0])
        assert result['status'] in ['success', 'error']
