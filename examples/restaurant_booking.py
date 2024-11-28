import asyncio
import os
import logging
from dotenv import load_dotenv
from agents.last_mile_agent import LastMileAgent
from tools.selenium_tool import SeleniumTool
from tools.claude_tool import ClaudeTool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_web_automation():
    """Test the web automation framework with various tasks"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize agent
    agent = LastMileAgent()
    await agent.initialize()
    
    try:
        # Test 1: Restaurant Search (Multiple Platforms)
        print("\nTest 1: Restaurant Search (Multiple Platforms)")
        print("--------------------------------------------")
        
        platforms = [
            {
                'url': 'https://www.opentable.com',
                'search_query': 'fine dining restaurants in San Francisco'
            },
            {
                'url': 'https://www.yelp.com',
                'search_query': 'best restaurants san francisco'
            },
            {
                'url': 'https://www.michelin.com',
                'search_query': 'michelin star restaurants san francisco'
            }
        ]
        
        for platform in platforms:
            print(f"\nTrying {platform['url']}...")
            task = {
                'type': 'web_navigation',
                'url': platform['url'],
                'search_query': platform['search_query'],
                'params': {
                    'location': 'San Francisco',
                    'cuisine': 'Fine Dining',
                    'price_range': '$$$$'
                }
            }
            
            result = await agent.execute_task(task)
            print(f"Navigation Result: {result}")
            
            if result['status'] == 'success':
                # Try data extraction
                extraction_task = {
                    'type': 'data_extraction',
                    'url': platform['url'],
                    'selectors': {
                        'restaurant_names': '.restaurant-name, .biz-name, .heading--title',
                        'ratings': '.star-rating, .rating, .stars',
                        'prices': '.price-range, .price, .business-price',
                        'cuisines': '.cuisine-type, .category-str-list, .restaurant-type'
                    }
                }
                
                extract_result = await agent.execute_task(extraction_task)
                print(f"Extraction Result: {extract_result}")
                
        # Test 2: Strategy Performance Analysis
        print("\nTest 2: Strategy Performance Analysis")
        print("-----------------------------------")
        stats = agent.get_strategy_stats()
        
        for task_type, strategies in stats.items():
            print(f"\n{task_type} Strategies:")
            for strategy_name, metrics in strategies.items():
                print(f"\n  {strategy_name}:")
                print(f"    Success Rate: {metrics['success_rate']:.2%}")
                print(f"    Successes: {metrics['success_count']}")
                print(f"    Failures: {metrics['failure_count']}")
                print(f"    Avg Execution Time: {metrics['avg_execution_time']:.2f}s")
                if metrics['last_execution']:
                    print(f"    Last Execution: {metrics['last_execution'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
    except Exception as e:
        logging.error(f"Error during testing: {str(e)}")
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_web_automation())
