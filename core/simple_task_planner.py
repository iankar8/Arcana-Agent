from typing import List
from .interfaces import Intent, Task, TaskPlannerInterface
from .logging_config import get_logger

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
