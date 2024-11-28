# agents/task_agent.py

from agents.base_agent import BaseAgent

class TaskAgent(BaseAgent):
    async def run(self):
        # Task execution logic
        pass

    async def receive_message(self, sender_id, message):
        intent = message.get('intent')
        entities = message.get('entities')

        if intent == 'book':
            await self.handle_booking(entities)
        elif intent == 'find':
            await self.handle_search(entities)
        else:
            print(f"Agent {self.agent_id} received unknown intent.")

    async def handle_booking(self, entities):
        # Implement booking logic
        print(f"Agent {self.agent_id} is handling booking with entities: {entities}")

    async def handle_search(self, entities):
        # Implement search logic
        print(f"Agent {self.agent_id} is handling search with entities: {entities}")

        # agents/task_agent.py (Update the handle_booking method)

from interface_layer.interface_layer import InterfaceLayer

class TaskAgent(BaseAgent):
    # Existing methods...

    async def handle_booking(self, entities):
        interface = InterfaceLayer()
        # Simulate API call
        location = entities.get('GPE', 'your area')
        num_people = entities.get('NUMBER', '2')
        date_time = entities.get('DATE', 'today')

        # Mock API interaction
        print(f"Agent {self.agent_id} is booking a table for {num_people} people on {date_time} at an Italian restaurant in {location}.")

        # Here you can add real API calls to reservation services
        # For example:
        # response = await interface.book_restaurant(location, num_people, date_time, cuisine='Italian')