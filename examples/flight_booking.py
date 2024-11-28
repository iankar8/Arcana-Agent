import asyncio
import os
from dotenv import load_dotenv
from agents.last_mile_agent import LastMileAgent
from tools.browser_tool import BrowserTool
from tools.claude_tool import ClaudeTool

async def book_flight():
    # Load environment variables
    load_dotenv()
    
    # Initialize agent with tools
    agent = LastMileAgent()
    agent.register_tool('browser', BrowserTool())
    agent.register_tool('claude', ClaudeTool())
    
    # Define flight booking task
    booking_task = {
        'type': 'web_navigation',
        'url': 'https://www.kayak.com',
        'subtasks': [
            {
                'type': 'form_filling',
                'form_data': {
                    'from': 'SFO',
                    'to': 'JFK',
                    'depart_date': '2024-04-01',
                    'return_date': '2024-04-08',
                    'passengers': '1'
                }
            },
            {
                'type': 'data_extraction',
                'selectors': {
                    'flights': '.flight-card',
                    'airlines': '.airline-name',
                    'prices': '.price-amount',
                    'durations': '.duration',
                    'departure_times': '.depart-time',
                    'arrival_times': '.arrival-time'
                }
            }
        ]
    }
    
    try:
        # Execute booking task
        result = await agent.execute_task(booking_task)
        
        # Print results
        print("\nFlight Search Results:")
        print("-------------------------")
        if result['status'] == 'success':
            flights = result['result']['data_extraction']['extracted_data']
            for flight in flights:
                print(f"Airline: {flight['airline']}")
                print(f"Price: ${flight['price']}")
                print(f"Duration: {flight['duration']}")
                print(f"Departure: {flight['departure_time']}")
                print(f"Arrival: {flight['arrival_time']}")
                print("-------------------------")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error during flight booking: {str(e)}")
    
    # Cleanup
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(book_flight())
