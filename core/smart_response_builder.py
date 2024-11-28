from typing import Any, Dict, List
from .interfaces import ResponseBuilderInterface
from .logging_config import get_logger

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
