"""Agent Registry System for Arcana Agent Framework."""

from typing import Dict, Type, List, Optional
from .interfaces import AgentInterface
from .logging_config import get_logger

logger = get_logger(__name__)

class AgentRegistry:
    """Registry for managing and accessing agents."""
    
    def __init__(self):
        self._agents: Dict[str, Type[AgentInterface]] = {}
        self._descriptions: Dict[str, str] = {}
        self._capabilities: Dict[str, List[str]] = {}
        self.logger = get_logger(self.__class__.__name__)
    
    def register(
        self,
        action: str,
        agent_cls: Type[AgentInterface],
        description: str = "",
        capabilities: Optional[List[str]] = None
    ) -> None:
        """Register an agent class for a specific action."""
        if action in self._agents:
            self.logger.warning(f"Overwriting existing agent for action: {action}")
        
        self._agents[action] = agent_cls
        self._descriptions[action] = description
        self._capabilities[action] = capabilities or []
        
        self.logger.info(f"Registered agent {agent_cls.__name__} for action: {action}")
    
    def unregister(self, action: str) -> None:
        """Unregister an agent for a specific action."""
        if action in self._agents:
            agent_cls = self._agents[action]
            del self._agents[action]
            del self._descriptions[action]
            del self._capabilities[action]
            self.logger.info(f"Unregistered agent {agent_cls.__name__} for action: {action}")
        else:
            self.logger.warning(f"No agent registered for action: {action}")
    
    def get_agent(self, action: str) -> Type[AgentInterface]:
        """Get the agent class for a specific action."""
        if action not in self._agents:
            self.logger.error(f"No agent registered for action: {action}")
            raise KeyError(f"No agent registered for action: {action}")
        
        return self._agents[action]
    
    def get_description(self, action: str) -> str:
        """Get the description for a specific action."""
        return self._descriptions.get(action, "")
    
    def get_capabilities(self, action: str) -> List[str]:
        """Get the capabilities for a specific action."""
        return self._capabilities.get(action, [])
    
    def list_actions(self) -> List[str]:
        """List all registered actions."""
        return list(self._agents.keys())
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get all actions that have a specific capability."""
        return [
            action
            for action, caps in self._capabilities.items()
            if capability in caps
        ]
    
    def create_agent(self, action: str, **kwargs) -> AgentInterface:
        """Create an instance of an agent for a specific action."""
        agent_cls = self.get_agent(action)
        try:
            agent = agent_cls(**kwargs)
            self.logger.debug(f"Created agent instance for action: {action}")
            return agent
        except Exception as e:
            self.logger.error(f"Failed to create agent for action {action}: {str(e)}")
            raise
