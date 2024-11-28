from typing import Dict, Any, Optional
from .base_tool import BaseTool
from playwright.async_api import async_playwright, Browser, Page

class BrowserTool(BaseTool):
    """
    Tool for browser automation using Playwright.
    """
    
    def __init__(self):
        super().__init__()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.current_page: Optional[Page] = None
    
    async def initialize(self) -> None:
        """Initialize browser instance"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        self.current_page = await self.browser.new_page(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Set extra headers to look more like a real browser
        await self.current_page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
    
    async def cleanup(self) -> None:
        """Cleanup browser resources"""
        if self.current_page:
            await self.current_page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute browser actions.
        
        Args:
            params: Dictionary containing:
                - action: Type of browser action
                - Additional parameters specific to the action
                
        Returns:
            Dictionary containing the results of the browser action
        """
        if not self.browser:
            await self.initialize()
            
        action = params.get('action')
        if not action:
            raise ValueError("Action is required")
            
        # Map actions to methods
        action_map = {
            'navigate': self._navigate,
            'fill_form': self._fill_form,
            'extract_data': self._extract_data,
            'click': self._click,
            'type': self._type,
            'wait': self._wait
        }
        
        handler = action_map.get(action)
        if not handler:
            raise ValueError(f"Unsupported browser action: {action}")
            
        return await handler(params)
    
    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to URL"""
        url = params.get('url')
        if not url:
            raise ValueError("URL is required for navigation")
            
        await self.current_page.goto(url)
        return {"status": "success", "url": url}
    
    async def _fill_form(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill form fields"""
        form_data = params.get('form_data', {})
        results = {}
        
        for field, value in form_data.items():
            try:
                # Try common selectors for form fields
                selectors = [
                    f'input[name="{field}"]',
                    f'input[placeholder*="{field}"]',
                    f'input[aria-label*="{field}"]',
                    f'textarea[name="{field}"]',
                    f'select[name="{field}"]'
                ]
                
                for selector in selectors:
                    try:
                        await self.current_page.fill(selector, str(value))
                        results[field] = "success"
                        break
                    except:
                        continue
                        
                if field not in results:
                    results[field] = "failed"
            except Exception as e:
                results[field] = f"error: {str(e)}"
                
        return {"status": "success", "results": results}
    
    async def _extract_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from page using selectors"""
        selectors = params.get('selectors', {})
        results = {}
        
        for key, selector in selectors.items():
            try:
                elements = await self.current_page.query_selector_all(selector)
                results[key] = [
                    await element.text_content() 
                    for element in elements
                ]
            except Exception as e:
                results[key] = f"error: {str(e)}"
                
        return {"status": "success", "extracted_data": results}
    
    async def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click an element"""
        selector = params.get('selector')
        if not selector:
            raise ValueError("Selector is required for clicking")
            
        await self.current_page.click(selector)
        return {"status": "success", "clicked": selector}
    
    async def _type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into an element"""
        selector = params.get('selector')
        text = params.get('text')
        
        if not selector or not text:
            raise ValueError("Selector and text are required for typing")
            
        await self.current_page.type(selector, text)
        return {"status": "success", "selector": selector}
    
    async def _wait(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for various conditions"""
        wait_type = params.get('wait_type', 'selector')
        target = params.get('target')
        timeout = params.get('timeout', 30000)  # 30 seconds default
        
        if not target:
            raise ValueError("Target is required for waiting")
            
        if wait_type == 'selector':
            await self.current_page.wait_for_selector(target, timeout=timeout)
        elif wait_type == 'navigation':
            await self.current_page.wait_for_navigation(timeout=timeout)
        elif wait_type == 'load':
            await self.current_page.wait_for_load_state(target, timeout=timeout)
        else:
            raise ValueError(f"Unsupported wait type: {wait_type}")
            
        return {"status": "success", "wait_type": wait_type, "target": target}
