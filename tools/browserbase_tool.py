from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
from dateutil.parser import parse as parse_date
from browserbase import BrowserBase
from .base_tool import BaseTool

class BrowserBaseTool(BaseTool):
    """
    Tool for browser automation using BrowserBase.
    """
    
    def __init__(self):
        super().__init__()
        self.browser = None
        self.current_page = None
        
    async def initialize(self) -> None:
        """Initialize BrowserBase instance"""
        self.browser = BrowserBase()
        await self.browser.connect()
        
    async def cleanup(self) -> None:
        """Cleanup browser resources"""
        if self.browser:
            await self.browser.disconnect()
            
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
            
        await self.browser.navigate(url)
        return {"status": "success", "url": url}
        
    async def _fill_form(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill form fields"""
        form_data = params.get('form_data', {})
        results = {}
        
        for field, value in form_data.items():
            try:
                # Format date if needed
                if 'date' in field.lower() and isinstance(value, str):
                    try:
                        date_obj = parse_date(value)
                        value = date_obj.strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Try common selectors for form fields
                selectors = [
                    f'input[name*="{field}"]',
                    f'input[placeholder*="{field}"]',
                    f'input[aria-label*="{field}"]',
                    f'textarea[name*="{field}"]',
                    f'select[name*="{field}"]',
                    f'[data-test*="{field}"]',
                    f'[data-testid*="{field}"]',
                    f'[id*="{field}"]'
                ]
                
                success = False
                for selector in selectors:
                    try:
                        element = await self.browser.find_element(selector)
                        if element:
                            await element.fill(str(value))
                            results[field] = "success"
                            success = True
                            break
                    except:
                        continue
                        
                if not success:
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
                elements = await self.browser.find_elements(selector)
                results[key] = []
                for element in elements:
                    text = await element.text()
                    if text:
                        results[key].append(text.strip())
            except Exception as e:
                results[key] = f"error: {str(e)}"
                
        return {"status": "success", "extracted_data": results}
        
    async def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click an element"""
        selector = params.get('selector')
        if not selector:
            raise ValueError("Selector is required for clicking")
            
        element = await self.browser.find_element(selector)
        await element.click()
        return {"status": "success", "clicked": selector}
        
    async def _type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into an element"""
        selector = params.get('selector')
        text = params.get('text')
        
        if not selector or not text:
            raise ValueError("Selector and text are required for typing")
            
        element = await self.browser.find_element(selector)
        await element.type(text)
        return {"status": "success", "typed": text}
        
    async def _wait(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for various conditions"""
        wait_type = params.get('type', 'element')
        timeout = params.get('timeout', 30000)
        
        if wait_type == 'element':
            selector = params.get('selector')
            if not selector:
                raise ValueError("Selector is required for element wait")
            await self.browser.wait_for_element(selector, timeout=timeout)
        elif wait_type == 'navigation':
            await self.browser.wait_for_navigation(timeout=timeout)
        else:
            raise ValueError(f"Unsupported wait type: {wait_type}")
            
        return {"status": "success", "wait_type": wait_type}
