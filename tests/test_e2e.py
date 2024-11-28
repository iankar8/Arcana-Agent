import pytest
import pytest_asyncio
from agents.last_mile_agent import LastMileAgent
from tools.browser_tool import BrowserTool
from tools.claude_tool import ClaudeTool
import asyncio
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket
from pathlib import Path

class TestServer(HTTPServer):
    def __init__(self, base_dir, *args, **kwargs):
        self.base_dir = base_dir
        super().__init__(*args, **kwargs)

class TestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        return str(Path(self.server.base_dir) / path.lstrip('/'))

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

class TestE2E:
    @pytest.fixture(scope="class")
    def test_server(self, test_data_dir):
        port = get_free_port()
        server = TestServer(
            test_data_dir,
            ('localhost', port),
            TestHandler
        )
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        yield f'http://localhost:{port}'
        server.shutdown()
        server.server_close()

    @pytest.fixture
    async def real_agent(self):
        agent = LastMileAgent()
        browser_tool = BrowserTool()
        claude_tool = ClaudeTool()
        
        agent.register_tool('browser', browser_tool)
        agent.register_tool('claude', claude_tool)
        
        await agent.initialize()
        yield agent
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_form_filling_e2e(self, real_agent, test_server):
        """Test form filling with a real browser instance"""
        task = {
            'type': 'form_filling',
            'url': f'{test_server}/html/restaurant_form.html',
            'data': {
                'restaurant': 'Test Restaurant',
                'date': '2024-03-20',
                'time': '19:00',
                'guests': '2'
            }
        }
        
        result = await real_agent.execute_task(task)
        assert result['status'] == 'success'
        assert 'confirmation' in result.get('data', {})

    @pytest.mark.asyncio
    async def test_data_extraction_e2e(self, real_agent, test_server):
        """Test data extraction with a real browser instance"""
        task = {
            'type': 'data_extraction',
            'url': f'{test_server}/html/restaurant_form.html',
            'selectors': {
                'form': '#booking-form',
                'fields': 'input, select'
            }
        }
        
        result = await real_agent.execute_task(task)
        assert result['status'] == 'success'
        assert 'form' in result.get('data', {})
        assert len(result['data'].get('fields', [])) > 0

    @pytest.mark.asyncio
    async def test_navigation_e2e(self, real_agent, test_server):
        """Test browser navigation with a real browser instance"""
        urls = [
            f'{test_server}/html/restaurant_form.html',
            f'{test_server}/html/confirmation.html'
        ]
        
        for url in urls:
            task = {
                'type': 'navigation',
                'url': url
            }
            result = await real_agent.execute_task(task)
            assert result['status'] == 'success'
            assert result.get('data', {}).get('loaded', False)

    @pytest.mark.asyncio
    async def test_screenshot_e2e(self, real_agent, test_server):
        """Test screenshot capture with a real browser instance"""
        task = {
            'type': 'screenshot',
            'url': f'{test_server}/html/restaurant_form.html',
            'output_path': 'test_screenshot.png'
        }
        
        result = await real_agent.execute_task(task)
        assert result['status'] == 'success'
        assert os.path.exists('test_screenshot.png')
        
        # Cleanup
        os.remove('test_screenshot.png')

    @pytest.mark.asyncio
    async def test_form_validation_e2e(self, real_agent, test_server):
        """Test form validation with a real browser instance"""
        # Test with invalid data
        task = {
            'type': 'form_filling',
            'url': f'{test_server}/html/restaurant_form.html',
            'data': {
                'restaurant': '',  # Required field left empty
                'date': 'invalid-date',
                'time': '25:00',  # Invalid time
                'guests': '999'  # Invalid guest count
            }
        }
        
        result = await real_agent.execute_task(task)
        assert result['status'] == 'error'
        assert 'validation_errors' in result.get('data', {})
