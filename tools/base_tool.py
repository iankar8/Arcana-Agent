from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseTool(ABC):
    """
    Abstract base class for all tools in the framework.
    Tools are the building blocks that agents use to execute tasks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    async def initialize(self) -> None:
        """
        Initialize the tool with any necessary setup.
        Override this method if your tool needs initialization.
        """
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool's main functionality.
        
        Args:
            params: Dictionary of parameters needed for execution
            
        Returns:
            Dictionary containing the results of the execution
        """
        pass
    
    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate the parameters before execution.
        Override this method to add custom validation.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        return True
    
    async def cleanup(self) -> None:
        """
        Cleanup any resources used by the tool.
        Override this method if your tool needs cleanup.
        """
        pass
