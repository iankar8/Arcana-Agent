from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime
from .base_agent import BaseAgent
from tools.selenium_tool import SeleniumTool
from tools.claude_tool import ClaudeTool

class Strategy:
    """Base class for execution strategies"""
    
    def __init__(self, name: str, handler: callable, priority: int = 1):
        self.name = name
        self.handler = handler
        self.priority = priority
        self.success_count = 0
        self.failure_count = 0
        self.last_execution = None
        self.avg_execution_time = 0
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the strategy and update metrics"""
        start_time = datetime.now()
        try:
            result = await self.handler(task)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update metrics
            if result.get('status') == 'success':
                self.success_count += 1
            else:
                self.failure_count += 1
                
            # Update average execution time
            total_executions = self.success_count + self.failure_count
            self.avg_execution_time = (
                (self.avg_execution_time * (total_executions - 1) + execution_time)
                / total_executions
            )
            
            self.last_execution = datetime.now()
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_execution = datetime.now()
            return {"status": "error", "message": str(e)}
            
    @property
    def success_rate(self) -> float:
        """Calculate success rate of the strategy"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0
        
class LastMileAgent(BaseAgent):
    """
    An intelligent agent for executing web-based tasks using parallel strategies
    and adaptive learning.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize strategies
        self.strategies = {
            'web_navigation': [
                Strategy('direct_navigation', self._direct_navigation_strategy, 1),
                Strategy('search_engine', self._search_engine_strategy, 2),
                Strategy('alternative_path', self._alternative_path_strategy, 3)
            ],
            'data_extraction': [
                Strategy('direct_selectors', self._direct_selectors_strategy, 1),
                Strategy('api_extraction', self._api_extraction_strategy, 2),
                Strategy('visual_extraction', self._visual_extraction_strategy, 3)
            ],
            'authentication': [
                Strategy('form_login', self._form_login_strategy, 1),
                Strategy('oauth_login', self._oauth_login_strategy, 2),
                Strategy('cookie_login', self._cookie_login_strategy, 3)
            ],
            'form_filling': [
                Strategy('direct_input', self._direct_input_strategy, 1),
                Strategy('iframe_input', self._iframe_input_strategy, 2),
                Strategy('dynamic_input', self._dynamic_input_strategy, 3)
            ]
        }
        
        # Performance metrics
        self.execution_history = []
        
    async def initialize(self) -> None:
        """Initialize agent with necessary tools"""
        # Initialize tools
        browser_tool = SeleniumTool()
        claude_tool = ClaudeTool()
        
        self.register_tool('browser', browser_tool)
        self.register_tool('claude', claude_tool)
        
        await super().initialize_tools()
        self.logger.info("LastMileAgent initialized with all tools")
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using multiple parallel strategies with adaptive learning.
        
        Args:
            task: Dictionary containing task details and parameters
            
        Returns:
            Best result from parallel execution strategies
        """
        if not await self.validate_task(task):
            return {"status": "error", "message": "Invalid task parameters"}
            
        task_type = task.get('type')
        if task_type not in self.strategies:
            return {"status": "error", "message": f"No strategies available for task type: {task_type}"}
            
        # Get strategies for this task type
        strategies = self.strategies[task_type]
        
        # Sort strategies by success rate and priority
        sorted_strategies = sorted(
            strategies,
            key=lambda s: (s.success_rate, -s.priority),
            reverse=True
        )
        
        # Execute strategies in parallel
        tasks = []
        for strategy in sorted_strategies:
            self.logger.debug(f"Queuing strategy: {strategy.name} (success rate: {strategy.success_rate:.2f})")
            tasks.append(strategy.execute(task))
            
        # Wait for first successful result or all failures
        results = []
        try:
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=30  # Global timeout
            )
            
            # Cancel pending tasks
            for t in pending:
                t.cancel()
                
            # Collect results
            results = []
            for t in done:
                try:
                    result = await t
                    if result['status'] == 'success':
                        # Log successful strategy
                        self.logger.info(f"Strategy {result.get('strategy')} succeeded")
                        self._update_execution_history(task_type, result)
                        return result
                    results.append(result)
                except Exception as e:
                    results.append({
                        'status': 'error',
                        'message': str(e)
                    })
                    
        except asyncio.TimeoutError:
            self.logger.error("Task execution timed out")
            return {
                'status': 'error',
                'message': 'All strategies timed out'
            }
            
        # If we get here, no strategy succeeded
        self.logger.warning(f"All strategies failed for task type: {task_type}")
        return {
            'status': 'error',
            'message': 'All strategies failed',
            'details': results
        }
        
    def _update_execution_history(self, task_type: str, result: Dict[str, Any]):
        """Update execution history for learning"""
        self.execution_history.append({
            'timestamp': datetime.now(),
            'task_type': task_type,
            'strategy': result.get('strategy'),
            'success': result.get('status') == 'success',
            'execution_time': result.get('execution_time')
        })
        
        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
            
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get statistics about strategy performance"""
        stats = {}
        for task_type, strategies in self.strategies.items():
            stats[task_type] = {}
            for strategy in strategies:
                stats[task_type][strategy.name] = {
                    'success_rate': strategy.success_rate,
                    'success_count': strategy.success_count,
                    'failure_count': strategy.failure_count,
                    'avg_execution_time': strategy.avg_execution_time,
                    'last_execution': strategy.last_execution
                }
        return stats
        
    async def validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate task parameters"""
        if not isinstance(task, dict):
            self.logger.error("Task must be a dictionary")
            return False
            
        required_fields = ['type']
        if not all(field in task for field in required_fields):
            self.logger.error(f"Missing required fields: {required_fields}")
            return False
            
        task_type = task.get('type')
        if task_type not in self.strategies:
            self.logger.error(f"Unsupported task type: {task_type}")
            return False
            
        return True
        
    async def cleanup(self) -> None:
        """Clean up agent resources"""
        self.logger.info("Cleaning up LastMileAgent resources")
        for tool in self.tools.values():
            await tool.cleanup()
            
    async def _handle_web_navigation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web navigation tasks with platform selection intelligence"""
        # Get the browser tool
        browser_tool = self.tools.get('browser')
        claude_tool = self.tools.get('claude')
        
        if not browser_tool:
            return {"status": "error", "message": "Browser tool not available"}
            
        # Define available restaurant platforms with their characteristics
        platforms = [
            {
                'name': 'Yelp',
                'url': 'https://www.yelp.com',
                'search_selectors': {
                    'search_input': 'input[id="search_description"]',
                    'location_input': 'input[id="search_location"]',
                    'submit_button': 'button[type="submit"]'
                },
                'result_selectors': {
                    'restaurant_cards': 'div[class*="businessName"]',
                    'names': 'a[class*="businessName"]',
                    'ratings': 'div[class*="rating"]',
                    'reviews': 'span[class*="reviewCount"]',
                    'categories': 'span[class*="category"]'
                }
            },
            {
                'name': 'Resy',
                'url': 'https://resy.com',
                'search_selectors': {
                    'location_input': 'input[data-test="location-input"]',
                    'search_button': 'button[data-test="location-submit"]'
                },
                'result_selectors': {
                    'restaurant_cards': 'div[data-test="venue-card"]',
                    'names': 'h2[data-test="venue-name"]',
                    'cuisines': 'span[data-test="venue-cuisine"]'
                }
            },
            {
                'name': 'GrubHub',
                'url': 'https://www.grubhub.com',
                'search_selectors': {
                    'address_input': 'input[data-testid="address-input"]',
                    'search_button': 'button[data-testid="address-submit"]'
                },
                'result_selectors': {
                    'restaurant_cards': 'div[data-testid="restaurant-card"]',
                    'names': 'h3[data-testid="restaurant-name"]',
                    'ratings': 'span[data-testid="restaurant-rating"]'
                }
            }
        ]
        
        # Try each platform until one works
        for platform in platforms:
            try:
                print(f"\nTrying {platform['name']}...")
                
                # Navigate to the platform
                nav_result = await browser_tool.execute({
                    'action': 'navigate',
                    'url': platform['url']
                })
                
                if nav_result.get('status') != 'success':
                    print(f"Failed to navigate to {platform['name']}: {nav_result.get('message')}")
                    continue
                    
                # Wait for main search input
                main_selector = list(platform['search_selectors'].values())[0]
                wait_result = await browser_tool.execute({
                    'action': 'wait',
                    'wait_type': 'element',
                    'selector': main_selector,
                    'timeout': 10000
                })
                
                if wait_result.get('status') != 'success':
                    print(f"Failed to find search elements on {platform['name']}: {wait_result.get('message')}")
                    continue
                
                print(f"Successfully connected to {platform['name']}")
                
                # If we got here, the platform is working
                location = task.get('location', 'San Francisco')
                
                # Fill search form based on platform
                for field, selector in platform['search_selectors'].items():
                    if 'location' in field.lower() or 'address' in field.lower():
                        type_result = await browser_tool.execute({
                            'action': 'type',
                            'selector': selector,
                            'text': location
                        })
                        if type_result.get('status') != 'success':
                            print(f"Failed to enter location on {platform['name']}: {type_result.get('message')}")
                            continue
                            
                    elif 'search' in field.lower():
                        type_result = await browser_tool.execute({
                            'action': 'type',
                            'selector': selector,
                            'text': 'restaurants'
                        })
                        if type_result.get('status') != 'success':
                            print(f"Failed to enter search term on {platform['name']}: {type_result.get('message')}")
                            continue
                            
                    elif 'button' in field.lower():
                        click_result = await browser_tool.execute({
                            'action': 'click',
                            'selector': selector
                        })
                        if click_result.get('status') != 'success':
                            print(f"Failed to click search on {platform['name']}: {click_result.get('message')}")
                            continue
                
                # Wait for results
                wait_result = await browser_tool.execute({
                    'action': 'wait',
                    'wait_type': 'element',
                    'selector': platform['result_selectors']['restaurant_cards'],
                    'timeout': 15000
                })
                
                if wait_result.get('status') != 'success':
                    print(f"Failed to load results on {platform['name']}: {wait_result.get('message')}")
                    continue
                
                # Extract data
                extract_result = await browser_tool.execute({
                    'action': 'extract_data',
                    'selectors': platform['result_selectors']
                })
                
                if extract_result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'platform': platform['name'],
                        'result': extract_result
                    }
                else:
                    print(f"Failed to extract data from {platform['name']}: {extract_result.get('message')}")
                    
            except Exception as e:
                print(f"Error with {platform['name']}: {str(e)}")
                continue
                
        return {
            'status': 'error',
            'message': 'Unable to access any restaurant platforms'
        }
    
    async def _handle_form_filling(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle form filling tasks"""
        form_data = task.get('form_data', {})
        
        # Use browser to fill form
        browser_result = await self.tools['browser'].execute({
            'action': 'fill_form',
            'form_data': form_data
        })
        
        return browser_result
    
    async def _handle_data_extraction(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data extraction tasks"""
        selectors = task.get('selectors', {})
        
        # Use browser to extract data
        browser_result = await self.tools['browser'].execute({
            'action': 'extract_data',
            'selectors': selectors
        })
        
        return browser_result
    
    async def _handle_file_download(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file download tasks"""
        file_url = task.get('file_url')
        
        browser_result = await self.tools['browser'].execute({
            'action': 'download_file',
            'url': file_url
        })
        
        return browser_result
    
    async def _handle_authentication(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authentication tasks"""
        credentials = task.get('credentials', {})
        
        # Use browser to perform authentication
        browser_result = await self.tools['browser'].execute({
            'action': 'authenticate',
            'credentials': credentials
        })
        
        return browser_result
        
    async def receive_message(self, sender_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming messages from other agents.
        
        Args:
            sender_id: ID of the sending agent
            message: Message content
            
        Returns:
            Response to the message
        """
        # This agent doesn't handle inter-agent messages
        return {
            'status': 'error',
            'error': 'Message handling not supported'
        }

    async def _direct_navigation_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Direct navigation to target URL"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        url = task.get('url')
        if not url:
            return {"status": "error", "message": "URL required for navigation"}
            
        return await browser.execute({
            'action': 'navigate',
            'url': url
        })

    async def _search_engine_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Use search engines to find target URL"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        search_query = task.get('search_query')
        if not search_query:
            return {"status": "error", "message": "Search query required"}
            
        # Try Google first
        await browser.execute({
            'action': 'navigate',
            'url': 'https://www.google.com'
        })
        
        # Search
        await browser.execute({
            'action': 'type',
            'selector': 'input[name="q"]',
            'text': search_query
        })
        
        await browser.execute({
            'action': 'click',
            'selector': 'input[name="btnK"]'
        })
        
        # Get first result
        result = await browser.execute({
            'action': 'get_attribute',
            'selector': 'div.g a',
            'attribute': 'href'
        })
        
        if result.get('status') == 'success':
            return await browser.execute({
                'action': 'navigate',
                'url': result['value']
            })
            
        return {"status": "error", "message": "No search results found"}

    async def _alternative_path_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Try alternative paths to reach target"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        url = task.get('url')
        if not url:
            return {"status": "error", "message": "URL required for navigation"}
            
        # Try different variations of the URL
        variations = [
            url,
            url.replace('www.', ''),
            'https://' + url if not url.startswith('http') else url,
            url + '/' if not url.endswith('/') else url[:-1]
        ]
        
        for variant in variations:
            result = await browser.execute({
                'action': 'navigate',
                'url': variant
            })
            
            if result.get('status') == 'success':
                return result
                
        return {"status": "error", "message": "All navigation attempts failed"}

    async def _direct_selectors_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Direct CSS/XPath selector based extraction"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        url = task.get('url')
        if not url:
            return {"status": "error", "message": "URL required for data extraction"}
            
        # Navigate to page
        nav_result = await browser.execute({
            'action': 'navigate',
            'url': url
        })
        
        if nav_result.get('status') != 'success':
            return nav_result
            
        # Extract data using provided selectors
        return await browser.execute({
            'action': 'extract_data',
            'selectors': task.get('selectors', {})
        })
        
    async def _api_extraction_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Try to find and use API endpoints for data extraction"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        url = task.get('url')
        if not url:
            return {"status": "error", "message": "URL required for API extraction"}
            
        # Navigate to page to capture network requests
        await browser.execute({
            'action': 'navigate',
            'url': url,
            'capture_network': True
        })
        
        # Get captured API endpoints
        network_data = await browser.execute({
            'action': 'get_network_data',
            'filter': {
                'type': ['xhr', 'fetch'],
                'status': [200]
            }
        })
        
        if network_data.get('status') != 'success':
            return network_data
            
        # Try each API endpoint
        for request in network_data.get('requests', []):
            if 'json' in request.get('response_type', ''):
                result = await browser.execute({
                    'action': 'fetch',
                    'url': request['url'],
                    'headers': request.get('headers', {})
                })
                
                if result.get('status') == 'success':
                    return result
                    
        return {"status": "error", "message": "No suitable API endpoints found"}
        
    async def _visual_extraction_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Use visual analysis to extract data when selectors fail"""
        browser = self.tools.get('browser')
        claude = self.tools.get('claude')
        
        if not browser or not claude:
            return {"status": "error", "message": "Required tools not available"}
            
        url = task.get('url')
        if not url:
            return {"status": "error", "message": "URL required for visual extraction"}
            
        # Navigate and take screenshot
        await browser.execute({
            'action': 'navigate',
            'url': url
        })
        
        screenshot = await browser.execute({
            'action': 'screenshot',
            'full_page': True
        })
        
        if screenshot.get('status') != 'success':
            return screenshot
            
        # Ask Claude to analyze the screenshot
        analysis = await claude.execute({
            'action': 'analyze_image',
            'image': screenshot['data'],
            'prompt': f"Please extract the following information: {', '.join(task.get('selectors', {}).keys())}"
        })
        
        if analysis.get('status') == 'success':
            return {
                'status': 'success',
                'strategy': 'visual',
                'extracted_data': analysis['result']
            }
            
        return {"status": "error", "message": "Visual analysis failed"}

    async def _form_login_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle form-based login"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        url = task.get('url')
        credentials = task.get('credentials', {})
        
        if not url or not credentials:
            return {"status": "error", "message": "URL and credentials required"}
            
        # Common login form selectors
        selectors = {
            'username': ['input[type="email"]', 'input[name="username"]', '#username', '#email'],
            'password': ['input[type="password"]', '#password', 'input[name="password"]'],
            'submit': ['button[type="submit"]', 'input[type="submit"]', '.login-button', '#login-button']
        }
        
        # Navigate to login page
        nav_result = await browser.execute({
            'action': 'navigate',
            'url': url
        })
        
        if nav_result.get('status') != 'success':
            return nav_result
            
        # Try each username selector
        for username_selector in selectors['username']:
            type_result = await browser.execute({
                'action': 'type',
                'selector': username_selector,
                'text': credentials.get('username', ''),
                'timeout': 5000
            })
            if type_result.get('status') == 'success':
                break
                
        if type_result.get('status') != 'success':
            return {"status": "error", "message": "Could not find username field"}
            
        # Try each password selector
        for password_selector in selectors['password']:
            type_result = await browser.execute({
                'action': 'type',
                'selector': password_selector,
                'text': credentials.get('password', ''),
                'timeout': 5000
            })
            if type_result.get('status') == 'success':
                break
                
        if type_result.get('status') != 'success':
            return {"status": "error", "message": "Could not find password field"}
            
        # Try each submit button
        for submit_selector in selectors['submit']:
            click_result = await browser.execute({
                'action': 'click',
                'selector': submit_selector,
                'timeout': 5000
            })
            if click_result.get('status') == 'success':
                break
                
        if click_result.get('status') != 'success':
            return {"status": "error", "message": "Could not find submit button"}
            
        # Wait for navigation
        await browser.execute({
            'action': 'wait',
            'wait_type': 'navigation',
            'timeout': 10000
        })
        
        return {"status": "success", "message": "Login successful"}
        
    async def _oauth_login_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle OAuth-based login"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        url = task.get('url')
        provider = task.get('oauth_provider', '').lower()
        
        if not url or not provider:
            return {"status": "error", "message": "URL and OAuth provider required"}
            
        # Common OAuth button selectors
        oauth_selectors = {
            'google': ['[aria-label*="Google"]', '.google-login', '#google-signin'],
            'facebook': ['[aria-label*="Facebook"]', '.facebook-login', '#facebook-signin'],
            'apple': ['[aria-label*="Apple"]', '.apple-login', '#apple-signin']
        }
        
        if provider not in oauth_selectors:
            return {"status": "error", "message": f"Unsupported OAuth provider: {provider}"}
            
        # Navigate to login page
        nav_result = await browser.execute({
            'action': 'navigate',
            'url': url
        })
        
        if nav_result.get('status') != 'success':
            return nav_result
            
        # Try each OAuth button selector
        for selector in oauth_selectors[provider]:
            click_result = await browser.execute({
                'action': 'click',
                'selector': selector,
                'timeout': 5000
            })
            if click_result.get('status') == 'success':
                break
                
        if click_result.get('status') != 'success':
            return {"status": "error", "message": f"Could not find {provider} login button"}
            
        # Wait for OAuth popup/redirect
        await browser.execute({
            'action': 'wait',
            'wait_type': 'navigation',
            'timeout': 15000
        })
        
        return {"status": "success", "message": f"{provider} OAuth initiated"}
        
    async def _cookie_login_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cookie-based login"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        url = task.get('url')
        cookies = task.get('cookies', [])
        
        if not url or not cookies:
            return {"status": "error", "message": "URL and cookies required"}
            
        # Set cookies
        for cookie in cookies:
            await browser.execute({
                'action': 'add_cookie',
                'cookie': cookie
            })
            
        # Navigate to verify login
        nav_result = await browser.execute({
            'action': 'navigate',
            'url': url
        })
        
        return nav_result
        
    async def _direct_input_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct form input"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        form_data = task.get('form_data', {})
        selectors = task.get('selectors', {})
        
        if not form_data or not selectors:
            return {"status": "error", "message": "Form data and selectors required"}
            
        results = []
        for field, value in form_data.items():
            selector = selectors.get(field)
            if not selector:
                continue
                
            # Handle different input types
            element_type = await browser.execute({
                'action': 'get_attribute',
                'selector': selector,
                'attribute': 'type'
            })
            
            if element_type.get('value') == 'select':
                result = await browser.execute({
                    'action': 'select',
                    'selector': selector,
                    'value': value
                })
            elif element_type.get('value') in ['checkbox', 'radio']:
                result = await browser.execute({
                    'action': 'click',
                    'selector': f"{selector}[value='{value}']"
                })
            else:
                result = await browser.execute({
                    'action': 'type',
                    'selector': selector,
                    'text': value
                })
                
            results.append(result)
            
        # Check if all inputs were successful
        if all(r.get('status') == 'success' for r in results):
            return {"status": "success", "message": "Form filled successfully"}
        else:
            return {"status": "error", "message": "Some form fields could not be filled"}
            
    async def _iframe_input_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle form input within iframes"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        iframe_selector = task.get('iframe_selector')
        form_data = task.get('form_data', {})
        selectors = task.get('selectors', {})
        
        if not iframe_selector or not form_data or not selectors:
            return {"status": "error", "message": "Iframe selector, form data, and field selectors required"}
            
        # Switch to iframe
        switch_result = await browser.execute({
            'action': 'switch_to_frame',
            'selector': iframe_selector
        })
        
        if switch_result.get('status') != 'success':
            return switch_result
            
        # Fill form using direct input strategy
        result = await self._direct_input_strategy(task)
        
        # Switch back to main frame
        await browser.execute({
            'action': 'switch_to_default'
        })
        
        return result
        
    async def _dynamic_input_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle input in dynamically loaded forms"""
        browser = self.tools.get('browser')
        if not browser:
            return {"status": "error", "message": "Browser tool not available"}
            
        form_data = task.get('form_data', {})
        selectors = task.get('selectors', {})
        
        if not form_data or not selectors:
            return {"status": "error", "message": "Form data and selectors required"}
            
        results = []
        for field, value in form_data.items():
            selector = selectors.get(field)
            if not selector:
                continue
                
            # Wait for element to be interactive
            wait_result = await browser.execute({
                'action': 'wait',
                'wait_type': 'element',
                'selector': selector,
                'condition': 'clickable',
                'timeout': 10000
            })
            
            if wait_result.get('status') != 'success':
                results.append(wait_result)
                continue
                
            # Use direct input strategy for the field
            result = await self._direct_input_strategy({
                'form_data': {field: value},
                'selectors': {field: selector}
            })
            
            results.append(result)
            
            # Wait for any dynamic updates
            await browser.execute({
                'action': 'wait',
                'wait_type': 'stability',
                'timeout': 2000
            })
            
        # Check if all inputs were successful
        if all(r.get('status') == 'success' for r in results):
            return {"status": "success", "message": "Dynamic form filled successfully"}
        else:
            return {"status": "error", "message": "Some dynamic form fields could not be filled"}
