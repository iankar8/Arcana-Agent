"""Tests for the Agent Registry component."""

import pytest
from unittest.mock import Mock
from typing import Dict, Any

from core.interfaces import AgentInterface, Task
from core.agent_registry import AgentRegistry

class MockAgent(AgentInterface):
    """Mock agent for testing."""
    async def execute(self, task: Task) -> Dict[str, Any]:
        return {"status": "success"}
    
    async def validate(self, task: Task) -> bool:
        return True

class SpecializedAgent(MockAgent):
    """Specialized mock agent for testing."""
    pass

@pytest.fixture
def registry():
    return AgentRegistry()

class TestAgentRegistry:
    def test_register_agent(self, registry):
        # Register agent
        registry.register(
            "test_action",
            MockAgent,
            "Test agent description",
            ["capability1", "capability2"]
        )
        
        # Assert
        assert "test_action" in registry.list_actions()
        assert registry.get_description("test_action") == "Test agent description"
        assert registry.get_capabilities("test_action") == ["capability1", "capability2"]
    
    def test_unregister_agent(self, registry):
        # Setup
        registry.register("test_action", MockAgent)
        
        # Unregister
        registry.unregister("test_action")
        
        # Assert
        assert "test_action" not in registry.list_actions()
        with pytest.raises(KeyError):
            registry.get_agent("test_action")
    
    def test_get_agent(self, registry):
        # Setup
        registry.register("test_action", MockAgent)
        
        # Get agent
        agent_cls = registry.get_agent("test_action")
        
        # Assert
        assert agent_cls == MockAgent
        with pytest.raises(KeyError):
            registry.get_agent("nonexistent_action")
    
    def test_create_agent(self, registry):
        # Setup
        registry.register("test_action", MockAgent)
        
        # Create agent
        agent = registry.create_agent("test_action")
        
        # Assert
        assert isinstance(agent, MockAgent)
    
    def test_get_agents_by_capability(self, registry):
        # Setup
        registry.register("action1", MockAgent, capabilities=["cap1", "cap2"])
        registry.register("action2", SpecializedAgent, capabilities=["cap2", "cap3"])
        
        # Get agents
        agents_with_cap2 = registry.get_agents_by_capability("cap2")
        agents_with_cap1 = registry.get_agents_by_capability("cap1")
        
        # Assert
        assert set(agents_with_cap2) == {"action1", "action2"}
        assert set(agents_with_cap1) == {"action1"}
    
    def test_overwrite_agent(self, registry):
        # Setup
        registry.register("test_action", MockAgent, "Original description")
        
        # Overwrite
        registry.register("test_action", SpecializedAgent, "New description")
        
        # Assert
        agent_cls = registry.get_agent("test_action")
        assert agent_cls == SpecializedAgent
        assert registry.get_description("test_action") == "New description"
    
    def test_create_agent_with_kwargs(self, registry):
        # Setup
        class ConfigurableAgent(MockAgent):
            def __init__(self, config_value: str):
                self.config_value = config_value
        
        registry.register("configurable_action", ConfigurableAgent)
        
        # Create agent with config
        agent = registry.create_agent("configurable_action", config_value="test_config")
        
        # Assert
        assert isinstance(agent, ConfigurableAgent)
        assert agent.config_value == "test_config"
