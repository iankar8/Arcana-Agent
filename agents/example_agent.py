from typing import Dict, Any
from ..core.interfaces import AgentInterface, Task

class ExampleAgent(AgentInterface):
    """Example agent that demonstrates the basic agent structure."""
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the task and return results."""
        # This is a simple example implementation
        return {
            "action": task.action,
            "status": "completed",
            "result": f"Processed task with parameters: {task.parameters}"
        }
    
    async def validate(self, task: Task) -> bool:
        """Validate that the task can be handled by this agent."""
        # Example validation logic
        required_params = ["param1", "param2"]
        return all(param in task.parameters for param in required_params)
