"""Registry for managing and coordinating agents in the system."""

from typing import Dict, Type, Optional, List, Any
import asyncio
from datetime import datetime

from core.interfaces import Agent
from core.protocol import Message, ProtocolError
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.logging_config import get_logger

logger = get_logger(__name__)

class AgentRegistry:
    """Central registry for managing agents in the system."""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self._agents: Dict[str, Agent] = {}
        self._agent_classes: Dict[str, Type[Agent]] = {}
        self._active_agents: Dict[str, bool] = {}
        self._logger = get_logger(self.__class__.__name__)

    async def register(self, name: str, agent_class: Type[Agent]) -> None:
        """Register an agent class with the registry."""
        if name in self._agent_classes:
            raise ValueError(f"Agent '{name}' is already registered")
        
        self._agent_classes[name] = agent_class
        self._logger.info(f"Registered agent class: {name}")
        
        self.metrics.record(
            name="agent_registrations",
            value=1,
            metric_type="counter",
            component="agent_registry",
            labels={"agent_type": name}
        )

    async def instantiate(self, name: str, **kwargs) -> Agent:
        """Create an instance of a registered agent."""
        if name not in self._agent_classes:
            raise ValueError(f"No agent class registered with name: {name}")

        try:
            agent_class = self._agent_classes[name]
            agent = agent_class(
                metrics_collector=self.metrics,
                error_handler=self.error_handler,
                **kwargs
            )
            self._agents[name] = agent
            self._active_agents[name] = False
            
            self._logger.info(f"Instantiated agent: {name}")
            return agent
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "agent_registry",
                    "operation": "instantiate",
                    "agent_name": name
                }
            )
            raise

    async def start_agent(self, name: str) -> None:
        """Start a registered agent."""
        if name not in self._agents:
            raise ValueError(f"No agent instance found with name: {name}")
            
        if self._active_agents[name]:
            return

        try:
            agent = self._agents[name]
            await agent.start()
            self._active_agents[name] = True
            
            self._logger.info(f"Started agent: {name}")
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "agent_registry",
                    "operation": "start",
                    "agent_name": name
                }
            )
            raise

    async def stop_agent(self, name: str) -> None:
        """Stop a registered agent."""
        if name not in self._agents:
            raise ValueError(f"No agent instance found with name: {name}")
            
        if not self._active_agents[name]:
            return

        try:
            agent = self._agents[name]
            await agent.stop()
            self._active_agents[name] = False
            
            self._logger.info(f"Stopped agent: {name}")
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "agent_registry",
                    "operation": "stop",
                    "agent_name": name
                }
            )
            raise

    async def send_message(self, message: Message) -> None:
        """Send a message to the specified agent."""
        if message.agent not in self._agents:
            raise ValueError(f"No agent instance found with name: {message.agent}")
            
        if not self._active_agents[message.agent]:
            raise RuntimeError(f"Agent '{message.agent}' is not active")

        try:
            agent = self._agents[message.agent]
            await agent.handle_message(message)
            
            self.metrics.record(
                name="messages_sent",
                value=1,
                metric_type="counter",
                component="agent_registry",
                labels={
                    "agent": message.agent,
                    "intent": message.intent
                }
            )
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "agent_registry",
                    "operation": "send_message",
                    "message_id": message.id,
                    "agent": message.agent
                }
            )
            raise

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent instance by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def get_agent_status(self, name: str) -> Dict[str, Any]:
        """Get the current status of an agent."""
        if name not in self._agents:
            raise ValueError(f"No agent instance found with name: {name}")
            
        return {
            "name": name,
            "active": self._active_agents[name],
            "type": self._agents[name].__class__.__name__
        }
