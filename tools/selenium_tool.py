from typing import Dict, Any, Optional, List
import asyncio
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from .base_tool import BaseTool
import json
import base64
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    """Rate limiter implementation with domain-specific limits"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.default_rate = 2  # requests per second
        self.domain_rates = {
            'google.com': 1,
            'yelp.com': 1,
            'opentable.com': 1
        }
        
    def _clean_old_requests(self, domain: str):
        """Remove requests older than 1 second"""
        now = datetime.now()
        self.requests[domain] = [
            req_time for req_time in self.requests[domain]
            if now - req_time < timedelta(seconds=1)
        ]
        
    async def wait_if_needed(self, url: str):
        """Wait if we're exceeding rate limits"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        self._clean_old_requests(domain)
        rate_limit = self.domain_rates.get(domain, self.default_rate)
        
        if len(self.requests[domain]) >= rate_limit:
            # Wait until we're under the limit
            sleep_time = 1.0 / rate_limit
            await asyncio.sleep(sleep_time)
            
        self.requests[domain].append(datetime.now())

class SeleniumTool(BaseTool):
    """A tool for browser automation using Selenium with advanced anti-bot measures"""
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self.wait = None
        self.network_logs = []
        self.rate_limiter = RateLimiter()
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> None:
        """Initialize the Selenium WebDriver with advanced anti-detection measures"""
        options = Options()
        
        # Basic Chrome options
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        
        # Advanced anti-bot measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Randomized user agent
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Additional privacy options
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Initialize WebDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Override navigator.webdriver
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        # Set up wait and logging
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.execute_cdp_cmd('Network.enable', {})
        
        self.logger.info("SeleniumTool initialized with anti-bot measures")
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a browser automation action with rate limiting and error handling"""
        action = params.get('action')
        if not action:
            return {"status": "error", "message": "No action specified"}
            
        try:
            # Add random delay between actions
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Map actions to methods
            action_map = {
                'navigate': self._navigate,
                'extract_data': self._extract_data,
                'click': self._click,
                'type': self._type,
                'screenshot': self._screenshot,
                'get_network_data': self._get_network_data,
                'fetch': self._fetch
            }
            
            handler = action_map.get(action)
            if not handler:
                return {"status": "error", "message": f"Unsupported action: {action}"}
                
            # Log action attempt
            self.logger.debug(f"Executing action: {action}")
            
            # Execute action with retry logic
            return await self._retry_with_backoff(handler, params)
            
        except Exception as e:
            self.logger.error(f"Error executing {action}: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def _retry_with_backoff(self, handler, params: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Retry an action with exponential backoff"""
        for attempt in range(max_retries):
            try:
                result = await handler(params)
                if result.get('status') == 'success':
                    return result
                    
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                    
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                self.logger.warning(f"Attempt {attempt + 1} failed with error: {str(e)}, retrying in {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
        return {"status": "error", "message": "All retry attempts failed"}
        
    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to URL with rate limiting and stealth measures"""
        url = params.get('url')
        if not url:
            return {"status": "error", "message": "URL required"}
            
        # Apply rate limiting
        await self.rate_limiter.wait_if_needed(url)
        
        try:
            # Random initial delay
            await asyncio.sleep(random.uniform(1, 3))
            
            # Enable network logging if requested
            capture_network = params.get('capture_network', False)
            if capture_network:
                self.network_logs = []
                self.driver.execute_cdp_cmd('Network.enable', {})
                
            # Navigate to URL
            self.driver.get(url)
            
            # Simulate human-like behavior
            await self._simulate_human_behavior()
            
            return {"status": "success"}
            
        except Exception as e:
            self.logger.error(f"Navigation error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def _simulate_human_behavior(self):
        """Simulate human-like behavior to avoid detection"""
        # Random scroll
        scroll_amount = random.randint(100, 500)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Random mouse movements (via JavaScript)
        self.driver.execute_script("""
            var event = new MouseEvent('mousemove', {
                'view': window,
                'bubbles': true,
                'cancelable': true,
                'clientX': arguments[0],
                'clientY': arguments[1]
            });
            document.dispatchEvent(event);
        """, random.randint(100, 800), random.randint(100, 600))
        
    async def _extract_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data using multiple selector strategies"""
        selectors = params.get('selectors', {})
        if not selectors:
            return {"status": "error", "message": "No selectors provided"}
            
        try:
            extracted_data = {}
            for key, selector in selectors.items():
                # Try multiple selector strategies
                strategies = [
                    (By.CSS_SELECTOR, selector),
                    (By.XPATH, f"//*[contains(@class, '{selector}')]"),
                    (By.XPATH, f"//*[contains(@id, '{selector}')]"),
                    (By.XPATH, f"//*[contains(text(), '{selector}')]")
                ]
                
                for by, locator in strategies:
                    try:
                        elements = self.driver.find_elements(by, locator)
                        if elements:
                            extracted_data[key] = [el.text for el in elements]
                            break
                    except:
                        continue
                        
                if key not in extracted_data:
                    extracted_data[key] = []
                    
            return {
                "status": "success",
                "extracted_data": extracted_data
            }
            
        except Exception as e:
            self.logger.error(f"Data extraction error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click an element"""
        selector = params.get('selector')
        if not selector:
            return {"status": "error", "message": "Selector required"}
            
        try:
            element = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return {"status": "success"}
        except Exception as e:
            self.logger.error(f"Click error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def _type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into an element"""
        selector = params.get('selector')
        text = params.get('text')
        
        if not selector or not text:
            return {"status": "error", "message": "Selector and text required"}
            
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.clear()
            element.send_keys(text)
            return {"status": "success"}
        except Exception as e:
            self.logger.error(f"Typing error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot"""
        try:
            if params.get('full_page'):
                # Scroll to capture full page
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                viewport_height = self.driver.execute_script("return window.innerHeight")
                self.driver.set_window_size(1920, total_height)
                
            screenshot = self.driver.get_screenshot_as_base64()
            return {
                "status": "success",
                "data": screenshot
            }
        except Exception as e:
            self.logger.error(f"Screenshot error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def _get_network_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get captured network data"""
        try:
            filter_params = params.get('filter', {})
            filtered_logs = self.network_logs
            
            if 'type' in filter_params:
                filtered_logs = [log for log in filtered_logs 
                               if log.get('type') in filter_params['type']]
                               
            if 'status' in filter_params:
                filtered_logs = [log for log in filtered_logs 
                               if log.get('status') in filter_params['status']]
                               
            return {
                "status": "success",
                "requests": filtered_logs
            }
        except Exception as e:
            self.logger.error(f"Network data error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def _fetch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from a URL"""
        url = params.get('url')
        headers = params.get('headers', {})
        
        if not url:
            return {"status": "error", "message": "URL required"}
            
        try:
            script = f"""
            return await fetch("{url}", {{
                headers: {json.dumps(headers)}
            }}).then(r => r.json());
            """
            
            result = self.driver.execute_async_script(script)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            self.logger.error(f"Fetch error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
