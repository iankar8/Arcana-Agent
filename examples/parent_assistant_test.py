import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from agents.last_mile_agent import LastMileAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_parent_assistant():
    """Test various tasks that a parent's personal assistant would handle"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize agent
    agent = LastMileAgent()
    await agent.initialize()
    
    try:
        # Test 1: Find and Book Activities
        print("\nTest 1: Find and Book Children's Activities")
        print("------------------------------------------")
        
        activities = [
            {
                'platform': 'ActivityHero',
                'url': 'https://www.activityhero.com',
                'search_params': {
                    'activity_type': 'After School',
                    'age_range': '5-7',
                    'location': 'San Francisco',
                    'date_range': 'Next Week'
                }
            }
        ]
        
        for platform in activities:
            print(f"\nSearching {platform['platform']}...")
            
            # Navigation task with search
            nav_task = {
                'type': 'web_navigation',
                'url': platform['url'],
                'search_query': f"{platform['search_params']['activity_type']} activities for kids {platform['search_params']['age_range']} in {platform['search_params']['location']}"
            }
            
            result = await agent.execute_task(nav_task)
            print(f"Navigation Result: {result}")
            
            if result['status'] == 'success':
                # Fill search form
                form_task = {
                    'type': 'form_filling',
                    'form_data': platform['search_params'],
                    'selectors': {
                        'activity_type': 'select[name="activity_type"], #activity-type',
                        'age_range': 'input[name="age"], #age-range',
                        'location': 'input[name="location"], #location',
                        'date_range': 'input[name="date"], #date-range'
                    }
                }
                
                form_result = await agent.execute_task(form_task)
                print(f"Search Form Result: {form_result}")
                
                if form_result['status'] == 'success':
                    # Extract activity data
                    extract_task = {
                        'type': 'data_extraction',
                        'selectors': {
                            'activity_names': '.activity-name, .class-title',
                            'schedules': '.schedule, .time-slot',
                            'age_ranges': '.age-range, .ages',
                            'prices': '.price, .cost',
                            'locations': '.location, .venue'
                        }
                    }
                    
                    extract_result = await agent.execute_task(extract_task)
                    print(f"Activity Data: {extract_result}")
                    
        # Test 2: School Lunch Menu Planning
        print("\nTest 2: School Lunch Menu Planning")
        print("--------------------------------")
        
        menu_sites = [
            {
                'name': 'School Menu',
                'url': 'https://www.schoolcafe.com/login',
                'auth': {
                    'type': 'form_login',
                    'credentials': {
                        'username': 'test_user',
                        'password': 'test_pass'
                    }
                }
            }
        ]
        
        for site in menu_sites:
            print(f"\nChecking {site['name']}...")
            
            # Authentication task
            auth_task = {
                'type': 'authentication',
                'url': site['url'],
                'auth_type': site['auth']['type'],
                'credentials': site['auth']['credentials']
            }
            
            auth_result = await agent.execute_task(auth_task)
            print(f"Authentication Result: {auth_result}")
            
            if auth_result['status'] == 'success':
                # Get menu data
                menu_task = {
                    'type': 'data_extraction',
                    'selectors': {
                        'dates': '.menu-date',
                        'meals': '.menu-item',
                        'nutritional_info': '.nutrition-info'
                    }
                }
                
                menu_result = await agent.execute_task(menu_task)
                print(f"Menu Data: {menu_result}")
        
        # Test 3: Healthcare Appointment Booking
        print("\nTest 3: Healthcare Appointment Booking")
        print("------------------------------------")
        
        healthcare_sites = [
            {
                'name': 'One Medical',
                'url': 'https://www.onemedical.com/appointments',
                'search_params': {
                    'specialty': 'Pediatrics',
                    'location': 'San Francisco'
                }
            }
        ]
        
        for site in healthcare_sites:
            print(f"\nChecking {site['name']}...")
            
            # Navigation and search
            search_task = {
                'type': 'web_navigation',
                'url': site['url'],
                'search_query': f"{site['search_params']['specialty']} appointment in {site['search_params']['location']}"
            }
            
            search_result = await agent.execute_task(search_task)
            print(f"Search Result: {search_result}")
            
            if search_result['status'] == 'success':
                # Fill appointment search form
                form_task = {
                    'type': 'form_filling',
                    'form_data': site['search_params'],
                    'selectors': {
                        'specialty': 'select[name="specialty"], #specialty',
                        'location': 'input[name="location"], #location'
                    }
                }
                
                form_result = await agent.execute_task(form_task)
                print(f"Form Result: {form_result}")
                
                if form_result['status'] == 'success':
                    # Extract available appointments
                    appointment_task = {
                        'type': 'data_extraction',
                        'selectors': {
                            'dates': '.available-date',
                            'times': '.time-slot',
                            'providers': '.provider-name',
                            'locations': '.clinic-location'
                        }
                    }
                    
                    appointment_result = await agent.execute_task(appointment_task)
                    print(f"Available Appointments: {appointment_result}")
        
        # Test 4: Educational Resource Finding
        print("\nTest 4: Educational Resource Finding")
        print("---------------------------------")
        
        education_sites = [
            {
                'name': 'Khan Academy Kids',
                'url': 'https://learn.khanacademy.org/khan-academy-kids/',
                'subject': 'Math',
                'grade': 'Grade 1'
            },
            {
                'name': 'PBS Kids',
                'url': 'https://pbskids.org',
                'subject': 'Reading',
                'age': '5-7'
            }
        ]
        
        for site in education_sites:
            print(f"\nSearching {site['name']}...")
            
            # Navigation task
            nav_task = {
                'type': 'web_navigation',
                'url': site['url']
            }
            
            nav_result = await agent.execute_task(nav_task)
            print(f"Navigation Result: {nav_result}")
            
            if nav_result['status'] == 'success':
                # Extract educational content
                content_task = {
                    'type': 'data_extraction',
                    'selectors': {
                        'lesson_titles': '.lesson-title, .game-title',
                        'subjects': '.subject-area, .category',
                        'age_ranges': '.age-range, .grade-level',
                        'descriptions': '.description, .summary'
                    }
                }
                
                content_result = await agent.execute_task(content_task)
                print(f"Educational Content: {content_result}")
        
        # Print Strategy Performance
        print("\nStrategy Performance Analysis")
        print("---------------------------")
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
    asyncio.run(test_parent_assistant())
