from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class CreateAgentAction(Action):

    def name(self) -> Text:
        return "create_agent_action"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        agent_name = tracker.get_slot("agent_name")
        # Logic to create agent using your framework
        dispatcher.utter_message(text=f"Agent {agent_name} has been created.")
        
        return []
