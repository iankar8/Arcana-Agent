# manager/agent_manager.py

import asyncio
from agents.task_agent import TaskAgent
from utils.nlp_utils import NLPUtils

class AgentManager:
    def __init__(self):
        self.agents = {}
        self.message_queue = asyncio.Queue()
        self.agent_counter = 0  # To assign unique IDs to agents
        self.knowledge_base = None  # Will be set externally

    def register_agent(self, agent):
        self.agents[agent.agent_id] = agent

    async def send_message(self, sender_id, recipient_id, message):
        if recipient_id in self.agents:
            await self.agents[recipient_id].receive_message(sender_id, message)
        else:
            print(f"Agent {recipient_id} not found.")

    async def run_agents(self):
        tasks = [agent.run() for agent in self.agents.values()]
        if tasks:
            await asyncio.gather(*tasks)

    async def handle_user_request(self, user_input):
        nlp = NLPUtils()
        intents = nlp.parse_intent(user_input)
        entities = nlp.extract_entities(user_input)

        # Decompose tasks into general actions
        actions = self.decompose_tasks(intents, entities)

        for action in actions:
            self.agent_counter += 1
            agent_id = f"specialized_agent_{self.agent_counter}"
            specialized_agent = TaskAgent(agent_id=agent_id, manager=self, knowledge_base=self.knowledge_base)
            self.register_agent(specialized_agent)
            # Assign the action to the specialized agent
            await specialized_agent.receive_message('user', {'action': action})

            # After task completion, deprecate the agent and retain knowledge
            await self.deprecate_agent(agent_id)

    def decompose_tasks(self, intents, entities):
        # Example task decomposition logic
        actions = []
        for intent in intents:
            # Break down each intent into smaller actions
            actions.append({'intent': intent, 'entities': entities})
        return actions

    async def deprecate_agent(self, agent_id):
        # Logic to deprecate the agent and retain workflow knowledge
        if agent_id in self.agents:
            del self.agents[agent_id]
        print(f"Agent {agent_id} deprecated and knowledge retained.")