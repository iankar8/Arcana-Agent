# agents/base_agent.py

import asyncio

class BaseAgent:
    def __init__(self, agent_id, manager, knowledge_base):
        self.agent_id = agent_id
        self.manager = manager
        self.knowledge_base = knowledge_base

    async def run(self):
        raise NotImplementedError("This method should be overridden by subclasses.")

    async def send_message(self, recipient_id, message):
        await self.manager.send_message(self.agent_id, recipient_id, message)

    async def receive_message(self, sender_id, message):
        raise NotImplementedError("This method should be overridden by subclasses.")