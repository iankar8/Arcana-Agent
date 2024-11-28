import asyncio
import os
from manager.agent_manager import AgentManager
from agents.task_agent import TaskAgent

# Your actual Claude API key (starts with "sk-")
CLAUDE_API_KEY = "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"  # Replace this with your actual API key

async def main():
    # Set the API key
    os.environ['CLAUDE_API_KEY'] = CLAUDE_API_KEY
    
    # Initialize the manager and agents
    manager = AgentManager()
    
    # Create booking agent
    booking_agent = TaskAgent(agent_id='booking_agent', manager=manager, knowledge_base=None)
    
    # Register the agent
    manager.register_agent(booking_agent)
    
    # Create a specific booking request for Hayes Valley
    booking_request = {
        'intent': 'book',
        'entities': {
            'location': 'Hayes Valley',
            'people': 4,
            'date': '2023-12-12',
            'time': '20:00',
            'neighborhood': 'Hayes Valley, San Francisco',
            'user_details': {
                'name': 'John Doe',  # Replace with actual user details
                'email': 'john.doe@example.com',
                'phone': '555-0123'
            }
        }
    }
    
    # Send booking request
    print("\nSending booking request to OpenTable:")
    print(f"Request details: {booking_request}")
    
    try:
        result = await manager.send_message('user', 'booking_agent', booking_request)
        print(f"\nBooking result: {result}")
    except Exception as e:
        print(f"Error during booking: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
