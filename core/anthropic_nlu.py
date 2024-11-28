import json
import anthropic
from typing import Dict, Any
from .interfaces import Intent, NLUInterface
from .logging_config import get_logger

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
