import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from manager.agent_manager import AgentManager
from agents.task_agent import TaskAgent

class TestAgentManager(unittest.TestCase):
    def setUp(self):
        self.manager = AgentManager()
        self.agent = TaskAgent(agent_id='test_agent', manager=self.manager, knowledge_base=None)

    def test_register_agent(self):
        self.manager.register_agent(self.agent)
        self.assertIn('test_agent', self.manager.agents)

    def test_send_message(self):
        self.manager.register_agent(self.agent)
        asyncio.run(self.manager.send_message('test_agent', 'test_agent', 'Hello'))
        # Further assertions can be added to check message receipt

    def test_task_decomposition(self):
        actions = self.manager.decompose_tasks(['test_intent'], ['test_entity'])
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['intent'], 'test_intent')

    def test_deprecate_agent(self):
        self.manager.register_agent(self.agent)
        asyncio.run(self.manager.deprecate_agent('test_agent'))
        self.assertNotIn('test_agent', self.manager.agents)

    def test_agent_interaction(self):
        # Test message passing between agents
        self.manager.register_agent(self.agent)
        other_agent = TaskAgent(agent_id='other_agent', manager=self.manager, knowledge_base=None)
        self.manager.register_agent(other_agent)
        asyncio.run(self.manager.send_message('test_agent', 'other_agent', {'intent': 'find', 'entities': {}}))
        # Further assertions can be added to verify message handling

    def test_error_handling(self):
        # Test error handling for unknown intents
        self.manager.register_agent(self.agent)
        asyncio.run(self.manager.send_message('test_agent', 'test_agent', {'intent': 'unknown', 'entities': {}}))
        # Check for error messages or logs
        
    def test_task_processing(self):
        # Test task decomposition and processing
        actions = self.manager.decompose_tasks(['find'], ['entity'])
        self.assertEqual(len(actions), 1)
        asyncio.run(self.agent.receive_message('user', actions[0]))
        # Verify task processing logic

if __name__ == '__main__':
    unittest.main()
