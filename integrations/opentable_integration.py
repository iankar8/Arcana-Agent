import os
import json
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

class ReservationError(Exception):
    """Base exception for reservation errors"""
    pass

class RestaurantNotAvailableError(ReservationError):
    """Raised when the restaurant is not available for the requested time"""
    pass

class InvalidReservationDetailsError(ReservationError):
    """Raised when reservation details are invalid"""
    pass

class ReservationFailedError(ReservationError):
    """Raised when the reservation attempt fails"""
    pass

@dataclass
class ReservationDetails:
    confirmation_number: str
    restaurant_name: str
    date: str
    time: str
    party_size: int
    user_name: str
    user_email: str
    user_phone: str
    status: str = "pending"
    special_instructions: str = ""

class OpenTableIntegration:
    def __init__(self):
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required")
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "accept": "application/json",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "x-api-key": self.claude_api_key
        }

        # Initialize database connection (example)
        self.db = None  # In reality, you'd connect to your database here
        
        # Initialize email client (example)
        self.email_client = None  # In reality, you'd set up your email service here

    async def _extract_json_from_response(self, response_data: Dict) -> Dict:
        """Extract JSON data from Claude's response"""
        try:
            content = response_data.get('content', [])
            if not content:
                raise ValueError("No content in response")
                
            text_content = next((item['text'] for item in content if item['type'] == 'text'), None)
            if not text_content:
                raise ValueError("No text content found")
            
            # Find the JSON part within the text
            start_idx = text_content.find('{')
            end_idx = text_content.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON content found in response")
                
            json_str = text_content[start_idx:end_idx]
            return json.loads(json_str)
            
        except Exception as e:
            print(f"Error extracting JSON from response: {e}")
            print(f"Response data: {response_data}")
            raise

    async def _make_api_request(self, prompt: str) -> Dict:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "claude-3-opus-20240229",
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "system": "You are Claude, an AI assistant using a web browser to help users make restaurant reservations on OpenTable.",
                "max_tokens": 4096
            }
            
            print("\nSending request to Claude API...")
            print(f"Headers: {self.headers}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                response_text = await response.text()
                print(f"\nAPI Response Status: {response.status}")
                print(f"API Response Text: {response_text}")
                
                if response.status != 200:
                    raise Exception(f"API request failed with status {response.status}: {response_text}")
                
                try:
                    response_data = json.loads(response_text)
                    return await self._extract_json_from_response(response_data)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON response: {e}")
                    print(f"Raw response: {response_text}")
                    raise

    async def search_restaurants(self, location: str, date: str, time: str, party_size: int) -> List[Dict]:
        """
        Search for restaurants on OpenTable using Claude's web browsing capabilities.
        """
        prompt = f"""
        Task: Search OpenTable for restaurants in {location} for {party_size} people on {date} at {time}.
        
        Steps:
        1. Navigate to OpenTable.com
        2. Enter the search parameters:
           - Location: {location}
           - Date: {date}
           - Time: {time}
           - Party Size: {party_size}
        3. Submit the search
        4. Extract and return the top 3 available restaurants with their details in the following JSON format:
        {{
            "restaurants": [
                {{
                    "name": "Restaurant Name",
                    "cuisine": "Cuisine Type",
                    "price_range": "$-$$$$",
                    "available_times": ["time1", "time2"],
                    "rating": 4.5,
                    "reservation_link": "full_url"
                }}
            ]
        }}
        """
        
        try:
            response = await self._make_api_request(prompt)
            return response.get('restaurants', [])
        except Exception as e:
            print(f"Error searching restaurants: {e}")
            return []

    async def make_reservation(self, restaurant_link: str, date: str, time: str, 
                             party_size: int, user_details: Dict) -> ReservationDetails:
        """
        Make a reservation with improved error handling and validation
        """
        try:
            # Validate inputs
            if not all([restaurant_link, date, time, party_size, user_details]):
                raise InvalidReservationDetailsError("Missing required reservation details")
            
            if party_size < 1:
                raise InvalidReservationDetailsError("Party size must be at least 1")
                
            # Attempt to make the reservation
            response = await self._make_reservation_request(
                restaurant_link, date, time, party_size, user_details
            )
            
            # Create reservation details object
            reservation = ReservationDetails(
                confirmation_number=response["confirmation_number"],
                restaurant_name=response["restaurant"],
                date=response["date"],
                time=response["time"],
                party_size=response["party_size"],
                user_name=f"{user_details['name']}",
                user_email=user_details["email"],
                user_phone=user_details["phone"],
                status=response["status"],
                special_instructions=response.get("special_instructions", "")
            )
            
            # Store in database
            await self._store_reservation(reservation)
            
            # Send confirmation email
            await self._send_confirmation_email(reservation)
            
            return reservation
            
        except Exception as e:
            # Log the error
            print(f"Error making reservation: {str(e)}")
            
            # Convert to appropriate error type
            if "not available" in str(e).lower():
                raise RestaurantNotAvailableError("Restaurant is not available for the requested time")
            elif "invalid" in str(e).lower():
                raise InvalidReservationDetailsError("Invalid reservation details provided")
            else:
                raise ReservationFailedError(f"Failed to make reservation: {str(e)}")
                
    async def _make_reservation_request(self, restaurant_link: str, date: str, time: str, 
                             party_size: int, user_details: Dict) -> Dict:
        """
        Make a reservation request to OpenTable
        """
        prompt = f"""
        Task: Make a reservation on OpenTable using the following details:
        
        Restaurant Link: {restaurant_link}
        Date: {date}
        Time: {time}
        Party Size: {party_size}
        User Details:
        - Name: {user_details.get('name')}
        - Email: {user_details.get('email')}
        - Phone: {user_details.get('phone')}
        
        Steps:
        1. Navigate to the restaurant's reservation page
        2. Select the date, time, and party size
        3. Fill in the user details
        4. Submit the reservation
        5. Return the confirmation details in the following JSON format:
        {{
            "status": "confirmed",
            "confirmation_number": "OT12345678",
            "restaurant": "Restaurant Name",
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "party_size": 4,
            "special_instructions": "Any special instructions"
        }}
        """
        
        response = await self._make_api_request(prompt)
        try:
            # Parse the response and extract the confirmation details
            result = response
            return result
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error parsing API response: {e}")
            return {
                "status": "error",
                "message": f"Failed to complete reservation: {str(e)}"
            }

    async def _store_reservation(self, reservation: ReservationDetails) -> None:
        """
        Store reservation details in database
        In a real implementation, this would save to your actual database
        """
        try:
            # Example SQL query (pseudocode)
            query = """
            INSERT INTO reservations (
                confirmation_number, restaurant_name, date, time,
                party_size, user_name, user_email, user_phone,
                status, special_instructions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            # await self.db.execute(query, reservation.__dict__)
            print(f"Stored reservation {reservation.confirmation_number} in database")
            
        except Exception as e:
            print(f"Error storing reservation: {str(e)}")
            # Note: We don't re-raise here because the reservation was still made
            # Just log the error and continue
            
    async def _send_confirmation_email(self, reservation: ReservationDetails) -> None:
        """
        Send confirmation email to user
        In a real implementation, this would use your email service
        """
        try:
            email_body = f"""
            Your reservation is confirmed!
            
            Restaurant: {reservation.restaurant_name}
            Date: {reservation.date}
            Time: {reservation.time}
            Party Size: {reservation.party_size}
            Confirmation Number: {reservation.confirmation_number}
            
            Special Instructions: {reservation.special_instructions}
            
            To modify or cancel your reservation, please visit:
            https://www.opentable.com/my/reservations
            """
            
            # Example email sending (pseudocode)
            # await self.email_client.send_email(
            #     to=reservation.user_email,
            #     subject="Your OpenTable Reservation Confirmation",
            #     body=email_body
            # )
            print(f"Sent confirmation email to {reservation.user_email}")
            
        except Exception as e:
            print(f"Error sending confirmation email: {str(e)}")
            # Note: We don't re-raise here because the reservation was still made
            # Just log the error and continue
            
    async def modify_reservation(self, confirmation_number: str, 
                               updates: Dict[str, Any]) -> ReservationDetails:
        """
        Modify an existing reservation
        """
        try:
            # Fetch existing reservation
            # reservation = await self.db.get_reservation(confirmation_number)
            
            # Update the reservation through OpenTable
            response = await self._make_api_request(f"""
                Task: Modify reservation {confirmation_number} with the following changes:
                {json.dumps(updates, indent=2)}
            """)
            
            # Update database
            # await self._store_reservation(updated_reservation)
            
            # Send modification email
            # await self._send_modification_email(updated_reservation)
            
            return response
            
        except Exception as e:
            raise ReservationFailedError(f"Failed to modify reservation: {str(e)}")
            
    async def cancel_reservation(self, confirmation_number: str) -> bool:
        """
        Cancel an existing reservation
        """
        try:
            # Cancel through OpenTable
            response = await self._make_api_request(f"""
                Task: Cancel reservation {confirmation_number}
            """)
            
            # Update database status
            # await self.db.update_reservation_status(confirmation_number, "cancelled")
            
            # Send cancellation email
            # await self._send_cancellation_email(reservation)
            
            return True
            
        except Exception as e:
            raise ReservationFailedError(f"Failed to cancel reservation: {str(e)}")
