import pytest
import pytest_asyncio
from tools.browser_tool import BrowserTool

class TestBrowserTool:
    @pytest.fixture
    def browser_tool(self):
        tool = BrowserTool()
        tool.initialize()
        return tool
        
    def test_initialization(self, browser_tool):
        assert browser_tool.browser is None
        assert browser_tool.current_page is None
        
    @pytest.mark.asyncio
    async def test_navigate(self, browser_tool):
        params = {
            'action': 'navigate',
            'url': 'https://example.com'
        }
        result = await browser_tool.execute(params)
        assert result['status'] == 'success'
        assert result['url'] == 'https://example.com'
        
    @pytest.mark.asyncio
    async def test_fill_form(self, browser_tool):
        params = {
            'action': 'fill_form',
            'form_data': {
                'username': 'test_user',
                'password': 'test_pass'
            }
        }
        result = await browser_tool.execute(params)
        assert result['status'] == 'success'
        assert 'username' in result['filled_fields']
        assert 'password' in result['filled_fields']
        
    @pytest.mark.asyncio
    async def test_extract_data(self, browser_tool):
        params = {
            'action': 'extract_data',
            'selectors': {
                'title': 'h1',
                'content': '.main-content'
            }
        }
        result = await browser_tool.execute(params)
        assert result['status'] == 'success'
        
    @pytest.mark.asyncio
    async def test_click(self, browser_tool):
        params = {
            'action': 'click',
            'selector': '#submit-button'
        }
        result = await browser_tool.execute(params)
        assert result['status'] == 'success'
        assert result['clicked'] == '#submit-button'
        
    @pytest.mark.asyncio
    async def test_type(self, browser_tool):
        params = {
            'action': 'type',
            'selector': '#input-field',
            'text': 'Hello, World!'
        }
        result = await browser_tool.execute(params)
        assert result['status'] == 'success'
        assert result['selector'] == '#input-field'
        
    @pytest.mark.asyncio
    async def test_wait(self, browser_tool):
        params = {
            'action': 'wait',
            'selector': '#loading',
            'timeout': 5000
        }
        result = await browser_tool.execute(params)
        assert result['status'] == 'success'
        assert result['waited_for'] == '#loading'
        
    @pytest.mark.asyncio
    async def test_invalid_action(self, browser_tool):
        params = {
            'action': 'invalid_action'
        }
        with pytest.raises(ValueError):
            await browser_tool.execute(params)
            
    @pytest.mark.asyncio
    async def test_missing_action(self, browser_tool):
        params = {}
        with pytest.raises(ValueError):
            await browser_tool.execute(params)
            
    @pytest.mark.asyncio
    async def test_navigate_missing_url(self, browser_tool):
        params = {
            'action': 'navigate'
        }
        with pytest.raises(ValueError):
            await browser_tool.execute(params)
