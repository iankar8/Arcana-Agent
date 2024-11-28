import pytest
import pytest_asyncio
from agents.last_mile_agent import LastMileAgent
from tools.browser_tool import BrowserTool
from tools.claude_tool import ClaudeTool

class TestIntegration:
    @pytest.fixture
    async def agent(self):
        agent = LastMileAgent()
        agent.register_tool('browser', BrowserTool())
        agent.register_tool('claude', ClaudeTool())
        await agent.initialize()
        yield agent
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_restaurant_booking_flow(self, agent, monkeypatch):
        # Mock browser interactions
        async def mock_browser_execute(*args, **kwargs):
            return {'status': 'success', 'data': {'reservation_confirmed': True}}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        # Mock Claude analysis
        async def mock_claude_execute(*args, **kwargs):
            return {'status': 'success', 'analysis': 'Booking form identified'}
        monkeypatch.setattr(ClaudeTool, 'execute', mock_claude_execute)
        
        task = {
            'type': 'restaurant_booking',
            'restaurant': 'Test Restaurant',
            'date': '2024-03-20',
            'time': '19:00',
            'guests': 2
        }
        
        result = await agent.execute_task(task)
        assert result['status'] == 'success'
        assert result['data']['reservation_confirmed']

    @pytest.mark.asyncio
    async def test_form_filling_flow(self, agent, monkeypatch):
        # Mock browser interactions
        async def mock_browser_execute(*args, **kwargs):
            return {'status': 'success', 'data': {'form_submitted': True}}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        # Mock Claude analysis
        async def mock_claude_execute(*args, **kwargs):
            return {
                'status': 'success',
                'form_analysis': {
                    'fields': [
                        {'name': 'username', 'type': 'text'},
                        {'name': 'password', 'type': 'password'}
                    ]
                }
            }
        monkeypatch.setattr(ClaudeTool, 'execute', mock_claude_execute)
        
        task = {
            'type': 'form_filling',
            'url': 'https://example.com/form',
            'data': {
                'username': 'testuser',
                'password': 'testpass'
            }
        }
        
        result = await agent.execute_task(task)
        assert result['status'] == 'success'
        assert result['data']['form_submitted']

    @pytest.mark.asyncio
    async def test_error_handling(self, agent, monkeypatch):
        # Mock browser failure
        async def mock_browser_execute(*args, **kwargs):
            raise Exception("Network error")
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        task = {
            'type': 'form_filling',
            'url': 'https://example.com/form',
            'data': {'field': 'value'}
        }
        
        with pytest.raises(Exception) as exc_info:
            await agent.execute_task(task)
        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parallel_execution(self, agent, monkeypatch):
        # Mock browser interactions
        async def mock_browser_execute(*args, **kwargs):
            return {'status': 'success', 'data': {'completed': True}}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        tasks = [
            {
                'type': 'data_extraction',
                'url': f'https://example.com/page{i}'
            }
            for i in range(3)
        ]
        
        results = await agent.execute_parallel(tasks)
        assert len(results) == 3
        assert all(r['status'] == 'success' for r in results)
        assert all(r['data']['completed'] for r in results)
