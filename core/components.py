import json
from typing import Any, Dict, List
import anthropic
from .interfaces import (
    Intent,
    Task,
    NLUInterface,
    TaskPlannerInterface,
    ResponseBuilderInterface
)
from .logging_config import get_logger

logger = get_logger(__name__)

class AnthropicNLU(NLUInterface):
    """NLU implementation using Anthropic's Claude."""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.logger = get_logger(self.__class__.__name__)
    
    async def parse(self, query: str) -> Intent:
        """Parse user query into structured intent using Claude."""
        try:
            self.logger.info(f"Parsing query: {query}")
            
            # Create system prompt for intent parsing
            system_prompt = """
            Parse the user query into a structured intent. Return a JSON object with:
            - name: The main intent/action
            - confidence: Confidence score between 0 and 1
            - parameters: Dictionary of relevant parameters
            Example: {"name": "book_flight", "confidence": 0.95, "parameters": {"destination": "NYC", "date": "2024-03-15"}}
            """
            
            message = await self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": query}]
            )
            
            # Parse the response
            response_content = message.content[0].text
            intent_dict = json.loads(response_content)
            
            self.logger.debug(f"Parsed intent: {intent_dict}")
            return Intent(**intent_dict)
            
        except Exception as e:
            self.logger.error(f"Error parsing query: {str(e)}")
            raise

class SimpleTaskPlanner(TaskPlannerInterface):
    """Basic implementation of task planning."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    async def plan(self, intent: Intent) -> List[Task]:
        """Convert intent into a list of tasks."""
        try:
            self.logger.info(f"Planning tasks for intent: {intent.name}")
            
            # Simple 1:1 mapping from intent to task for basic cases
            task = Task(
                action=intent.name,
                parameters=intent.parameters,
                dependencies=None,
                priority=1
            )
            
            self.logger.debug(f"Created task: {task}")
            return [task]
            
        except Exception as e:
            self.logger.error(f"Error planning tasks: {str(e)}")
            raise
    
    async def validate_dependencies(self, tasks: List[Task]) -> bool:
        """Validate task dependencies."""
        try:
            self.logger.info("Validating task dependencies")
            
            # Create a set of all task actions
            available_actions = {task.action for task in tasks}
            
            # Check if all dependencies are satisfied
            for task in tasks:
                if task.dependencies:
                    if not all(dep in available_actions for dep in task.dependencies):
                        self.logger.warning(f"Unsatisfied dependencies for task: {task.action}")
                        return False
            
            self.logger.debug("All dependencies validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating dependencies: {str(e)}")
            raise

class SmartResponseBuilder(ResponseBuilderInterface):
    """Intelligent response builder with context awareness."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    async def build_response(self, results: List[Dict[str, Any]]) -> str:
        """Build a user-friendly response from task results."""
        try:
            self.logger.info("Building response from results")
            
            # Handle empty results
            if not results:
                return "No results to report."
            
            # Build a context-aware response
            response_parts = []
            for result in results:
                status = result.get("status", "unknown")
                action = result.get("action", "unknown action")
                
                if status == "completed":
                    response_parts.append(f"Successfully {action.replace('_', ' ')}")
                    if "result" in result:
                        response_parts.append(str(result["result"]))
                else:
                    response_parts.append(f"Could not complete {action}")
            
            response = ". ".join(response_parts)
            self.logger.debug(f"Built response: {response}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error building response: {str(e)}")
            raise
    
    async def build_error_response(self, error: Exception) -> str:
        """Build an error response."""
        try:
            self.logger.error(f"Building error response for: {str(error)}")
            
            # Create a user-friendly error message
            error_msg = f"I encountered an error: {str(error)}"
            if hasattr(error, "details"):
                error_msg += f"\nDetails: {error.details}"
            
            return error_msg
            
        except Exception as e:
            self.logger.error(f"Error building error response: {str(e)}")
            return "An unexpected error occurred while processing your request."
