import os
import json
import aiohttp
from typing import Dict, Any, Optional
from .base_tool import BaseTool

class ClaudeTool(BaseTool):
    """
    Tool for interacting with Claude's Computer Use API.
    """
    
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.api_url = None
        self.headers = None
    
    async def initialize(self) -> None:
        """Initialize Claude API client"""
        self.api_key = os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required")
            
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "accept": "application/json",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Claude API actions.
        
        Args:
            params: Dictionary containing:
                - action: Type of Claude action
                - Additional parameters specific to the action
                
        Returns:
            Dictionary containing the results of the Claude action
        """
        action = params.get('action')
        if not action:
            raise ValueError("Action is required")
            
        # Map actions to methods
        action_map = {
            'analyze_page': self._analyze_page,
            'analyze_form': self._analyze_form,
            'analyze_data': self._analyze_data,
            'generate_script': self._generate_script,
            'extract_info': self._extract_info
        }
        
        handler = action_map.get(action)
        if not handler:
            raise ValueError(f"Unsupported Claude action: {action}")
            
        return await handler(params)
    
    async def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """Make request to Claude API"""
        payload = {
            "model": "claude-3-opus-20240229",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "system": "You are Claude, an AI assistant using a web browser to help users automate web tasks.",
            "max_tokens": 4096
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"API request failed with status {response.status}")
                    
                response_data = await response.json()
                return self._extract_json_from_response(response_data)
    
    def _extract_json_from_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract JSON data from Claude's response"""
        try:
            content = response_data.get('content', [])
            if not content:
                raise ValueError("No content in response")
                
            text_content = next((item['text'] for item in content if item['type'] == 'text'), None)
            if not text_content:
                raise ValueError("No text content found")
            
            # Find the JSON part within the text
            start_idx = text_content.find('{')
            end_idx = text_content.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON content found in response")
                
            json_str = text_content[start_idx:end_idx]
            return json.loads(json_str)
            
        except Exception as e:
            print(f"Error extracting JSON from response: {e}")
            return {}
    
    async def _analyze_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze webpage content and structure"""
        url = params.get('url')
        if not url:
            raise ValueError("URL is required for page analysis")
            
        prompt = f"""
        Task: Analyze the webpage at {url}
        
        Steps:
        1. Navigate to the URL
        2. Analyze the page structure and content
        3. Identify key interactive elements
        4. Return the analysis in the following JSON format:
        {{
            "title": "Page Title",
            "main_content": "Description of main content",
            "interactive_elements": [
                {{
                    "type": "button/form/link",
                    "selector": "CSS selector",
                    "purpose": "Element purpose"
                }}
            ],
            "navigation": [
                {{
                    "text": "Link text",
                    "url": "Target URL"
                }}
            ]
        }}
        """
        
        return await self._make_api_request(prompt)
    
    async def _analyze_form(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze form structure and fields"""
        form_data = params.get('form_data', {})
        
        prompt = f"""
        Task: Analyze the form with the following data: {json.dumps(form_data)}
        
        Steps:
        1. Identify form fields and their types
        2. Determine required vs optional fields
        3. Return the analysis in the following JSON format:
        {{
            "fields": [
                {{
                    "name": "Field name",
                    "type": "text/select/checkbox/etc",
                    "required": true/false,
                    "selector": "CSS selector"
                }}
            ],
            "submit_button": "CSS selector",
            "validation_rules": [
                {{
                    "field": "Field name",
                    "rule": "Rule description"
                }}
            ]
        }}
        """
        
        return await self._make_api_request(prompt)
    
    async def _analyze_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data structure and patterns"""
        selectors = params.get('selectors', {})
        
        prompt = f"""
        Task: Analyze the data structure using selectors: {json.dumps(selectors)}
        
        Steps:
        1. Identify data patterns and relationships
        2. Determine data types and formats
        3. Return the analysis in the following JSON format:
        {{
            "data_structure": [
                {{
                    "name": "Data field name",
                    "type": "Data type",
                    "format": "Expected format",
                    "selector": "CSS selector"
                }}
            ],
            "relationships": [
                {{
                    "from": "Field name",
                    "to": "Related field",
                    "type": "Relationship type"
                }}
            ]
        }}
        """
        
        return await self._make_api_request(prompt)
    
    async def _generate_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate automation script based on task"""
        task_description = params.get('task')
        if not task_description:
            raise ValueError("Task description is required")
            
        prompt = f"""
        Task: Generate a browser automation script for: {task_description}
        
        Steps:
        1. Break down the task into steps
        2. Generate appropriate selectors and actions
        3. Return the script in the following JSON format:
        {{
            "steps": [
                {{
                    "action": "Action type",
                    "selector": "CSS selector",
                    "value": "Input value if needed",
                    "wait_for": "Element to wait for"
                }}
            ],
            "error_handling": [
                {{
                    "condition": "Error condition",
                    "action": "Recovery action"
                }}
            ]
        }}
        """
        
        return await self._make_api_request(prompt)
    
    async def _extract_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific information from webpage"""
        target_info = params.get('target_info')
        if not target_info:
            raise ValueError("Target information description is required")
            
        prompt = f"""
        Task: Extract the following information: {target_info}
        
        Steps:
        1. Locate the target information
        2. Extract and format the data
        3. Return the information in the following JSON format:
        {{
            "extracted_data": {{
                "field_name": "Extracted value",
                "source": "CSS selector or location"
            }},
            "confidence": 0.95,
            "context": "Surrounding context"
        }}
        """
        
        return await self._make_api_request(prompt)
