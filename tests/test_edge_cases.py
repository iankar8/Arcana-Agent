import pytest
import pytest_asyncio
from agents.last_mile_agent import LastMileAgent
from tools.browser_tool import BrowserTool
from tools.claude_tool import ClaudeTool
import asyncio
import json

class TestEdgeCases:
    @pytest.fixture
    async def agent(self):
        agent = LastMileAgent()
        agent.register_tool('browser', BrowserTool())
        agent.register_tool('claude', ClaudeTool())
        await agent.initialize()
        yield agent
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_malformed_html(self, agent, html_fixtures, monkeypatch):
        """Test handling of malformed HTML"""
        html = "<div>Unclosed div"
        
        async def mock_browser_execute(*args, **kwargs):
            return {'status': 'success', 'html': html}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        task = {
            'type': 'data_extraction',
            'url': 'https://example.com',
            'selectors': {'content': 'div'}
        }
        
        result = await agent.execute_task(task)
        assert result['status'] == 'success'
        assert 'extracted_data' in result

    @pytest.mark.asyncio
    async def test_network_timeout(self, agent, monkeypatch):
        """Test handling of network timeouts"""
        async def mock_browser_execute(*args, **kwargs):
            await asyncio.sleep(2)  # Simulate delay
            raise TimeoutError("Request timed out")
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        task = {
            'type': 'form_filling',
            'url': 'https://example.com/form',
            'data': {'field': 'value'}
        }
        
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(agent.execute_task(task), timeout=1)

    @pytest.mark.asyncio
    async def test_invalid_selectors(self, agent, monkeypatch):
        """Test handling of invalid CSS selectors"""
        async def mock_browser_execute(*args, **kwargs):
            if 'selector' in kwargs and kwargs['selector'] == '###invalid':
                raise ValueError("Invalid selector")
            return {'status': 'success'}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        task = {
            'type': 'data_extraction',
            'url': 'https://example.com',
            'selectors': {'content': '###invalid'}
        }
        
        with pytest.raises(ValueError):
            await agent.execute_task(task)

    @pytest.mark.asyncio
    async def test_concurrent_limit(self, agent, monkeypatch, performance_config):
        """Test handling of concurrent task limits"""
        async def mock_browser_execute(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate work
            return {'status': 'success'}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        tasks = [
            {
                'type': 'data_extraction',
                'url': f'https://example.com/page{i}'
            }
            for i in range(performance_config['concurrent_tasks'] * 2)
        ]
        
        start_time = asyncio.get_event_loop().time()
        results = await agent.execute_parallel(tasks)
        end_time = asyncio.get_event_loop().time()
        
        assert len(results) == len(tasks)
        assert end_time - start_time >= 0.2  # Should take at least 2 batches

    @pytest.mark.asyncio
    async def test_large_response(self, agent, monkeypatch):
        """Test handling of large response data"""
        large_data = {'data': 'x' * 1024 * 1024}  # 1MB of data
        
        async def mock_browser_execute(*args, **kwargs):
            return {'status': 'success', 'data': large_data}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        task = {
            'type': 'data_extraction',
            'url': 'https://example.com'
        }
        
        result = await agent.execute_task(task)
        assert result['status'] == 'success'
        assert len(json.dumps(result)) > 1024 * 1024

    @pytest.mark.asyncio
    async def test_unicode_handling(self, agent, monkeypatch):
        """Test handling of unicode characters"""
        unicode_data = {
            'restaurant': '🍜 Rāmen Shop',
            'special': '特別なメニュー',
            'price': '€20.00'
        }
        
        async def mock_browser_execute(*args, **kwargs):
            return {'status': 'success', 'data': unicode_data}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        task = {
            'type': 'data_extraction',
            'url': 'https://example.com'
        }
        
        result = await agent.execute_task(task)
        assert result['status'] == 'success'
        assert result['data']['restaurant'] == '🍜 Rāmen Shop'
        assert result['data']['special'] == '特別なメニュー'
