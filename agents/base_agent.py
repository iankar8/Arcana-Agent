# agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging
from contextlib import asynccontextmanager

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the framework.
    Provides core functionality for tool management and message handling.
    """
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.is_running = False
        self._cleanup_tasks = []
        self._logger = logging.getLogger(self.__class__.__name__)
        
    def register_tool(self, tool_name: str, tool: Any) -> None:
        """Register a tool with this agent."""
        if tool_name in self.tools:
            self._logger.warning(f"Tool {tool_name} already registered, replacing")
        self.tools[tool_name] = tool
        
    async def initialize_tools(self) -> None:
        """Initialize all registered tools."""
        for name, tool in self.tools.items():
            try:
                self._logger.info(f"Initializing tool: {name}")
                await tool.initialize()
                self._logger.info(f"Initialized tool: {name}")
            except Exception as e:
                self._logger.error(f"Failed to initialize tool {name}: {str(e)}")
                raise
                
    async def cleanup_tools(self) -> None:
        """Clean up all registered tools."""
        for name, tool in self.tools.items():
            try:
                self._logger.info(f"Cleaning up tool: {name}")
                await tool.cleanup()
                self._logger.info(f"Cleaned up tool: {name}")
            except Exception as e:
                self._logger.error(f"Error cleaning up tool {name}: {str(e)}")
                
    @asynccontextmanager
    async def managed_execution(self):
        """Context manager for handling tool lifecycle."""
        try:
            await self.initialize_tools()
            yield
        finally:
            await self.cleanup_tools()
            
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using the registered tools.
        
        Args:
            task: Dictionary containing task details
            
        Returns:
            Dictionary containing execution results
        """
        pass
        
    @abstractmethod
    async def receive_message(self, sender_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming messages from other agents.
        
        Args:
            sender_id: ID of the sending agent
            message: Message content
            
        Returns:
            Response to the message
        """
        pass
        
    async def start(self) -> None:
        """Start the agent and initialize its tools."""
        if self.is_running:
            return
            
        self.is_running = True
        await self.initialize_tools()
        
    async def stop(self) -> None:
        """Stop the agent and clean up its resources."""
        if not self.is_running:
            return
            
        self.is_running = False
        await self.cleanup_tools()
        
        # Clean up any remaining tasks
        for task in self._cleanup_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        self._cleanup_tasks.clear()
        
    def add_cleanup_task(self, task: asyncio.Task) -> None:
        """Add a task to be cleaned up when the agent stops."""
        self._cleanup_tasks.append(task)
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()