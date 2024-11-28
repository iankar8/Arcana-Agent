import pytest
import pytest_asyncio
import os
from tools.claude_tool import ClaudeTool

class TestClaudeTool:
    @pytest.fixture
    def claude_tool(self, monkeypatch):
        # Mock environment variable
        monkeypatch.setenv('CLAUDE_API_KEY', 'test_api_key')
        tool = ClaudeTool()
        tool.initialize()  # Initialize after environment variable is set
        return tool
        
    def test_initialization(self, claude_tool):
        assert claude_tool.api_key == 'test_api_key'
        assert claude_tool.api_url == "https://api.anthropic.com/v1/messages"
        assert 'x-api-key' in claude_tool.headers
        
    def test_initialization_missing_api_key(self, monkeypatch):
        monkeypatch.delenv('CLAUDE_API_KEY', raising=False)
        tool = ClaudeTool()
        with pytest.raises(ValueError):
            tool.initialize()
            
    @pytest.mark.asyncio
    async def test_analyze_page(self, claude_tool, monkeypatch):
        async def mock_api_request(*args, **kwargs):
            return {'analysis': 'mocked'}
            
        monkeypatch.setattr(claude_tool, '_make_api_request', mock_api_request)
        
        params = {
            'action': 'analyze_page',
            'url': 'https://example.com'
        }
        result = await claude_tool.execute(params)
        assert isinstance(result, dict)
        assert 'analysis' in result
        
    @pytest.mark.asyncio
    async def test_analyze_form(self, claude_tool, monkeypatch):
        async def mock_api_request(*args, **kwargs):
            return {'form_analysis': 'mocked'}
            
        monkeypatch.setattr(claude_tool, '_make_api_request', mock_api_request)
        
        params = {
            'action': 'analyze_form',
            'form_data': {
                'username': 'field1',
                'password': 'field2'
            }
        }
        result = await claude_tool.execute(params)
        assert isinstance(result, dict)
        assert 'form_analysis' in result
        
    @pytest.mark.asyncio
    async def test_analyze_data(self, claude_tool, monkeypatch):
        async def mock_api_request(*args, **kwargs):
            return {'data_analysis': 'mocked'}
            
        monkeypatch.setattr(claude_tool, '_make_api_request', mock_api_request)
        
        params = {
            'action': 'analyze_data',
            'selectors': {
                'title': 'h1',
                'content': '.content'
            }
        }
        result = await claude_tool.execute(params)
        assert isinstance(result, dict)
        assert 'data_analysis' in result
        
    @pytest.mark.asyncio
    async def test_generate_script(self, claude_tool, monkeypatch):
        async def mock_api_request(*args, **kwargs):
            return {'script': 'mocked'}
            
        monkeypatch.setattr(claude_tool, '_make_api_request', mock_api_request)
        
        params = {
            'action': 'generate_script',
            'task': 'Login to a website'
        }
        result = await claude_tool.execute(params)
        assert isinstance(result, dict)
        assert 'script' in result
        
    @pytest.mark.asyncio
    async def test_extract_info(self, claude_tool, monkeypatch):
        async def mock_api_request(*args, **kwargs):
            return {'extracted_info': 'mocked'}
            
        monkeypatch.setattr(claude_tool, '_make_api_request', mock_api_request)
        
        params = {
            'action': 'extract_info',
            'target_info': 'Find all prices on the page'
        }
        result = await claude_tool.execute(params)
        assert isinstance(result, dict)
        assert 'extracted_info' in result
        
    @pytest.mark.asyncio
    async def test_invalid_action(self, claude_tool):
        params = {
            'action': 'invalid_action'
        }
        with pytest.raises(ValueError):
            await claude_tool.execute(params)
            
    @pytest.mark.asyncio
    async def test_missing_action(self, claude_tool):
        params = {}
        with pytest.raises(ValueError):
            await claude_tool.execute(params)
