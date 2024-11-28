# agents/task_agent.py

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent

class TaskAgent(BaseAgent):
    """
    A concrete implementation of BaseAgent for executing web automation tasks.
    """
    
    def __init__(self, agent_id: str, manager: Any, knowledge_base: Optional[Any] = None):
        """
        Initialize the task agent.
        
        Args:
            agent_id: Unique identifier for this agent
            manager: Reference to the agent manager
            knowledge_base: Optional knowledge base for the agent
        """
        super().__init__()
        self.agent_id = agent_id
        self.manager = manager
        self.knowledge_base = knowledge_base
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using the registered tools.
        
        Args:
            task: Dictionary containing:
                - intent: Type of task to execute
                - entities: Parameters for the task
                
        Returns:
            Dictionary containing:
                - status: 'success' or 'error'
                - result: Task result if successful
                - error: Error message if failed
        """
        intent = task.get('intent')
        entities = task.get('entities', {})
        
        try:
            if intent == 'book':
                return await self._handle_booking(entities)
            elif intent == 'find':
                return await self._handle_search(entities)
            else:
                return {
                    'status': 'error',
                    'error': f'Unknown intent: {intent}'
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def receive_message(self, sender_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming messages from other agents.
        
        Args:
            sender_id: ID of the sending agent
            message: Message content
            
        Returns:
            Response to the message
        """
        return await self.execute_task(message)
        
    async def _handle_booking(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a booking task."""
        # Get the browser tool
        browser = self.tools.get('browser')
        if not browser:
            raise ValueError("Browser tool is required for booking")
            
        # Extract booking details
        location = entities.get('location', '')
        date = entities.get('date', '')
        time = entities.get('time', '')
        party_size = entities.get('party_size', 2)
        
        # Navigate to booking site
        await browser.execute({
            'action': 'navigate',
            'url': 'https://www.opentable.com'
        })
        
        # Fill search form
        await browser.execute({
            'action': 'fill_form',
            'form_data': {
                'location': location,
                'date': date,
                'time': time,
                'party_size': str(party_size)
            }
        })
        
        # Extract results
        results = await browser.execute({
            'action': 'extract_data',
            'selectors': {
                'restaurants': '.restaurant-card',
                'names': '.restaurant-name',
                'cuisines': '.cuisine-type',
                'ratings': '.rating-score'
            }
        })
        
        return {
            'status': 'success',
            'result': results
        }
        
    async def _handle_search(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a search task."""
        # Get the browser tool
        browser = self.tools.get('browser')
        if not browser:
            raise ValueError("Browser tool is required for search")
            
        # Extract search parameters
        query = entities.get('query', '')
        filters = entities.get('filters', {})
        
        # Navigate to search site
        await browser.execute({
            'action': 'navigate',
            'url': f'https://www.google.com/search?q={query}'
        })
        
        # Apply filters if any
        if filters:
            await browser.execute({
                'action': 'fill_form',
                'form_data': filters
            })
        
        # Extract results
        results = await browser.execute({
            'action': 'extract_data',
            'selectors': {
                'titles': 'h3',
                'links': 'a',
                'snippets': '.snippet'
            }
        })
        
        return {
            'status': 'success',
            'result': results
        }