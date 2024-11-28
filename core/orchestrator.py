import asyncio
from typing import Dict, List, Type
from .interfaces import (
    AgentInterface,
    Intent,
    NLUInterface,
    ResponseBuilderInterface,
    Task,
    TaskPlannerInterface,
)

class AgentRegistry:
    """Registry for managing available agents."""
    
    def __init__(self):
        self._agents: Dict[str, Type[AgentInterface]] = {}
    
    def register(self, action: str, agent_cls: Type[AgentInterface]):
        """Register an agent class for a specific action."""
        self._agents[action] = agent_cls
    
    def get_agent(self, action: str) -> Type[AgentInterface]:
        """Get the appropriate agent for an action."""
        if action not in self._agents:
            raise KeyError(f"No agent registered for action: {action}")
        return self._agents[action]

class Orchestrator:
    """Main orchestrator for the Arcana Agent Framework."""
    
    def __init__(
        self,
        nlu: NLUInterface,
        task_planner: TaskPlannerInterface,
        response_builder: ResponseBuilderInterface,
        agent_registry: AgentRegistry
    ):
        self.nlu = nlu
        self.task_planner = task_planner
        self.response_builder = response_builder
        self.agent_registry = agent_registry
    
    async def process_query(self, query: str) -> str:
        """Process a user query and return a response."""
        try:
            # Parse the query into an intent
            intent = await self.nlu.parse(query)
            
            # Convert intent into tasks
            tasks = await self.task_planner.plan(intent)
            
            # Validate task dependencies
            if not await self.task_planner.validate_dependencies(tasks):
                return await self.response_builder.build_error_response(
                    Exception("Invalid task dependencies")
                )
            
            # Execute tasks
            results = await self._execute_tasks(tasks)
            
            # Build response
            return await self.response_builder.build_response(results)
            
        except Exception as e:
            return await self.response_builder.build_error_response(e)
    
    async def _execute_tasks(self, tasks: List[Task]) -> List[Dict]:
        """Execute a list of tasks with proper dependency handling."""
        results = []
        
        # Group tasks by dependency level
        dependency_groups = self._group_tasks_by_dependencies(tasks)
        
        # Execute tasks level by level
        for task_group in dependency_groups:
            # Tasks in the same group can be executed in parallel
            group_results = await asyncio.gather(
                *[self._execute_single_task(task) for task in task_group]
            )
            results.extend(group_results)
        
        return results
    
    async def _execute_single_task(self, task: Task) -> Dict:
        """Execute a single task using the appropriate agent."""
        agent_cls = self.agent_registry.get_agent(task.action)
        agent = agent_cls()
        
        if not await agent.validate(task):
            raise ValueError(f"Task validation failed for action: {task.action}")
        
        return await agent.execute(task)
    
    def _group_tasks_by_dependencies(self, tasks: List[Task]) -> List[List[Task]]:
        """Group tasks by their dependency levels."""
        # Simple implementation - can be enhanced for more complex dependency graphs
        no_deps = [task for task in tasks if not task.dependencies]
        with_deps = [task for task in tasks if task.dependencies]
        
        if not with_deps:
            return [no_deps]
        
        return [no_deps, with_deps]  # This is a simplified version
