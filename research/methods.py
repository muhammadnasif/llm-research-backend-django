from langchain.tools import tool
import requests
from pydantic import BaseModel, Field, constr
import datetime
from datetime import date


ROOM_NUMBER = 305
TODAY = date.today()


# Define the input schema
class OpenMeteoInput(BaseModel):
    latitude: float = Field(...,
                            description="Latitude of the location to fetch weather data for")
    longitude: float = Field(...,
                             description="Longitude of the location to fetch weather data for")


@tool(args_schema=OpenMeteoInput, return_direct=True)
def get_current_temperature(latitude: float, longitude: float) -> dict:
    """Fetch current Weather for given cities or coordinates. For example: what is the weather of Colombo ?"""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # Parameters for the request
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m',
        'forecast_days': 1,
    }

    # Make the request
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        results = response.json()
    else:
        raise Exception(
            f"API Request failed with status code: {response.status_code}")

    current_utc_time = datetime.datetime.utcnow()
    time_list = [datetime.datetime.fromisoformat(time_str.replace(
        'Z', '+00:00')) for time_str in results['hourly']['time']]
    temperature_list = results['hourly']['temperature_2m']

    closest_time_index = min(range(len(time_list)), key=lambda i: abs(
        time_list[i] - current_utc_time))
    current_temperature = temperature_list[closest_time_index]

    return f'The current temperature is {current_temperature}Â°C'


class book_room_input(BaseModel):
    room_type: str = Field(...,
                           description="Which type of room AC or Non-AC. Input from user")
    class_type: str = Field(
        ..., description="Which class of room it is. Business class or Economic class.Input from user")
    check_in_date: date = Field(...,
                                description="The date user will check-in. Input from user")
    check_out_date: date = Field(...,
                                 description="The date user will check-out. Input from user")
    mobile_no: str = Field(...,
                           description="Mobile number of the user. Input from user")
    # mobile_no : constr(regex=r'(^(?:\+?88)?01[3-9]\d{8})$') = Field(...,description="Mobile number of the user")


@tool(args_schema=book_room_input, return_direct=True)
def book_room(room_type: str, class_type: str, check_in_date: date, check_out_date: date, mobile_no: constr) -> str:
    """
      Book a room with the specified details.

      Args:
          room_type (str): Which type of room to book (AC or Non-AC). Input from user.
          class_type (str): Which class of room it is (Business class or Economic class). Input from user.
          check_in_date (date): The date the user will check-in. Input from user.
          check_out_date (date): The date the user will check-out. Input from user.
          mobile_no (str): Mobile number of the user. Input from user.

      Returns:
          str: A message confirming the room booking. 
      """
    # Placeholder logic for booking the room
    # return f"Room has been booked for {room_type} {class_type} class from {check_in_date} to {check_out_date}. Mobile number: {mobile_no}."
    return f'''{{
                  "function-name": "book_room",
                  "parameters": {{
                      "room_type": "{room_type}",
                      "class_type": "{class_type}",
                      "check_in_date": "{check_in_date}",
                      "check_out_date": "{check_out_date}",
                      "mobile_no": "{mobile_no}"
                  }}
              }}'''


class requestFoodFromRestaurant(BaseModel):
    item_name: str = Field(...,
                           description="The food item they want to order from the restaurant")
    dine_in_type: str = Field(..., description="If the customer wants to eat in the door-step, take parcel or dine in the restaurant. It can have at most 3 values 'dine-in-room', 'dine-in-restaurant', 'parcel'")


@tool(args_schema=requestFoodFromRestaurant, return_direct=True)
def order_resturant_item(item_name: str,  dine_in_type: str, room_number=ROOM_NUMBER) -> str:
    """
    Order food and bevarages at the hotel restaurant with specified details.

    Args:
      item_name (str) : The food item they want to order from the restaurant
      dine_in_type (str) : inside hotel room, dine in restaurant or parcel

    Returns
      str: A message for confirmation of food order.
    """

    # if dine_in_type == "dine-in-room":
    #     return f"Your order have been placed. The food will get delivered at your room."
    # elif dine_in_type == "dine-in-restaurant":
    #     return f"Your order have been placed. You will be notified once the food is almost ready."
    # else:
    #     return f"Your order have been placed. The parcel will be ready in 45 minutes."

    return f'''{{
                  "function-name": "order_resturant_item",
                  "parameters": {{
                      "item_name": "{item_name}",
                      "room_number": "{room_number}",
                      "dine_in_type": "{dine_in_type}"
                  }}
              }}'''


class requestBillingChangeRequest(BaseModel):
    complaint: str = Field(..., description="Complain about the bill. It could be that the bill is more than it should be. Or some services are charged more than it was supposed to be")


@tool(args_schema=requestBillingChangeRequest, return_direct=True)
def bill_complain_request(complaint: str, room_number=ROOM_NUMBER) -> str:
    """
    Complaints about billing with specified details.
    Args:
      complaint (str) : Complain about the bill. It could be that the bill is more than it should be. Or some services are charged more than it was supposed to be.
      room_number (int) : The room number from where the complain is made. Not Default value, should be asked from user.
    Returns
      str: A message for confirmation of the bill complaint.
    """

    # return f"We  have received your complain {complaint}  and notified accounts department to handle the issue. Please keep your patience while we resolve. You will be notified from the front-desk once it is resolved"
    return f'''{{
                  "function-name": "bill_complain_request",
                  "parameters": {{
                      "complaint": "{complaint}",
                      "room_number": "{room_number}"
                  }}
              }}'''

class InformationEntity(BaseModel):
    subject: str = Field(...,
                         description="The subject user wants to know about")


@tool(args_schema=InformationEntity, return_direct=True)
def restaurant_information(subject: str):
    """
    Information related ot the restaurant of the hotel
    """

    return f"Data is returned from resturant-faq-api/{subject}"


@tool(args_schema=InformationEntity, return_direct=True)
def hotel_information_request(subject: str):
    """
    Information related to residential hotel.
    """

    # return f"Data is returned from hotel-faq-api/{subject}"
    return f'''{{
                  "function-name": "hotel_information_request",
                  "parameters": {{
                      "subject": "{subject}"
                  }}
              }}'''


class ConciergeEntity(BaseModel):
    location: str = Field(..., description="Location for emergecy. Example - Garage, Lobby, Plinth at 6th floor, balcony of room, dining room etc")


@tool(args_schema=ConciergeEntity, return_direct=True)
def emergencyConciergeRequest(location: str, room_number = ROOM_NUMBER):
    """
    Emergency Safety calls for help with  speciefied details
    Args:
      location (str) : Location for emergecy. Example - Garage, Lobby, Plinth at 6th floor, balcony of room, dining room etc
      room_number (int) : The room number from where the complain is made. Not Default value, should be asked from user.
    Returns
      str: A message for confirmation of the assistance.
    """

    # return f"Our staff is on the way to {location} to assist you."
    return f'''{{
                  "function-name": "food_recommedation",
                  "parameters": {{
                      "location": "{location}"
                      "room_number": "{room_number}"
                  }}
              }}'''



class RecommendationExcursion(BaseModel):
    place_type: str = Field(
        ..., description="The type of place the customer wants to visit. Example - park, zoo, pool. Take input from user")


class TransportationRecommendationEntity(BaseModel):
    location: str = Field(..., description="The place customer wants to go visit")


class RoomRecommendation(BaseModel):
    budget_highest: int = Field(..., description="Maximum rent customer can pay per day for a room. Take input from user")


class FoodRecommendation(BaseModel):
    cuisine: str = Field(..., description="The type of cuisine the customer wants to eat. Like - Chinese, Indian, Italian etc. Take input from user.")


@tool(args_schema=FoodRecommendation, return_direct=True)
def food_recommedation(cuisine: str):
    """
    Recommend foods that is suited for the customer according to the weather from the restaurant.
    """

    return f'''{{
                  "function-name": "food_recommedation",
                  "parameters": {{
                      "cuisine": "{cuisine}"
                  }}
              }}'''

@tool(args_schema=TransportationRecommendationEntity, return_direct=True)
def transportation_recommendation(location: str) -> str:
    """
    Recommends transportation with specified details
    Args:
      location (str) : The place customer wants to go visit
    Returns
      str: A message with transportation recommendation.
    """

    # transport = "Private Car"

    # return f"I recommend to go there by {transport}"
    return f'''{{
                  "function-name": "transportation_recommendation",
                  "parameters": {{
                      "location": "{location}"
                  }}
              }}'''


@tool(args_schema=RecommendationExcursion, return_direct=True)
def excursion_recommendation(place_type: str) -> str:
    """
    Suggest nice places to visit nearby with specified details
    Args:
      place_type (str) : The type of place the customer wants to visit. Example - park, zoo, pool. Alsways ask for this value.
    Returns
      str: A message with excursion recommendation.
    """

    return f'''{{
                  "function-name": "excursion_recommendation",
                  "parameters": {{
                      "place_type": "{place_type}"
                  }}
              }}'''


@tool(args_schema=RoomRecommendation, return_direct=True)
def room_recommendation(budget_highest: int) -> str:
    """
    Room recommendation for customer with specified details
    Args:
      budget_highest (int) : Maximum rent customer can pay per day for a room. Take input from user
    Returns
      str: A message with room suggestions according to budget.
    """

    return f'''{{
                  "function-name": "room_recommendation",
                  "parameters": {{
                      "budget_highest": "{budget_highest}"
                  }}
              }}'''


# @tool(args_schema = None)
# def negative_requisition() -> str:
#   """
#   When a requisition is made and not sure what to do.
#   """

#   return f"Sorry, can you please say that again."


@tool(return_direct=True)
def housekeeping_service_request(room_number=ROOM_NUMBER) -> str:
    """
    Provides housekeeping service to the hotel room.
    """

    return f'''{{
                  "function-name": "housekeeping_service_request",
                  "parameters": {{
                      "room_number": "{room_number}"
                  }}
              }}'''


class RoomMaintenanceRequestInput(BaseModel):
    room_number: int = Field(
        ..., description="The room number that needs room maintenance service.")
    issue: str = Field(...,
                       description="The issue for which it needs maintenance service")


class RoomAmenitiesRequest(BaseModel):
    requested_amenity: str = Field(...,description="The amenity that the customer wants to request. Example - extra towel, extra pillow, extra blanket etc. Take input from user.")
    

@tool(args_schema=RoomAmenitiesRequest, return_direct=True)
def request_room_amenity(requested_amenity: str, room_number=ROOM_NUMBER):
    """
    Request for room amenities like extra towel, extra pillow, extra blanket etc.

    Args:
      room_number (int) : The room number that needs the room amenities service
      requested_amenity (str) : The amenity that the customer wants to request. Example - extra towel, extra pillow, extra blanket etc. Take input from user.
    Returns
      str: An acknowdelgement that ensures that someone is sent to the room for fixing.
    """

    return f'''{{
                  "function-name": "request_room_amenity",
                  "parameters": {{"requested_amenity": "{requested_amenity}","room_number": "{room_number}"}}
              }}'''

@tool(args_schema=RoomMaintenanceRequestInput, return_direct=True)
def request_room_maintenance(issue: str, room_number=ROOM_NUMBER):
    """
    Resolves room issues regarding hardware like toilteries, furnitures, windows or electric gadgets like FAN, TC, AC etc of hotel room.

    Args:
      room_number (int) : The room number that needs the room maintenance service
    Returns
      str: An acknowdelgement that ensures that someone is sent to the room for fixing.
    """

    return f'''{{
                  "function-name": "request_room_maintenance",
                  "parameters": {{
                      "issue": "{issue}",
                      "room_number": "{room_number}"
                  }}
              }}'''

class MiscellaneousRequestEntity(BaseModel):
    request: str = Field(..., description="The service they want")


@tool(args_schema=MiscellaneousRequestEntity, return_direct=True)
def request_miscellaneous(request: str, room_number=ROOM_NUMBER):
    """
    Other requests that can be served by ordirnary staff.
    """

    return f'''{{
                  "function-name": "request_miscellaneous",
                  "parameters": {{
                      "request": "{request}",
                      "room_number": "{room_number}"
                  }}
              }}'''



class ReminderEntity(BaseModel):
    reminder_message: str = Field(..., description="The reminder message of the customer")
    reminder_time: str = Field(..., description="The time to remind at")


@tool(args_schema=ReminderEntity, return_direct=True)
def request_reminder(reminder_message: str, reminder_time: str, room_number=ROOM_NUMBER):
    """
    Set an alarm for the customer to remind about the message at the mentioned time.

    Args:
      room_number (int) : The room number that needs reminder service
      reminder_message (str) : The reminder message of the customer
      reminder_time (str) : The time to remind the customer at.
    Returns
      str: An acknowdelgement message for the customer.
    """

    return f'''{{
                  "function-name": "request_reminder",
                  "parameters": {{
                      "reminder_time": "{reminder_time}",
                      "reminder_message": "{reminder_message}",
                      "room_number": "{room_number}"
                  }}
              }}'''


class WakeUpEntity(BaseModel):
    wakeup_time: str = Field(..., description="The time to remind at")


@tool(args_schema=WakeUpEntity, return_direct=True)
def request_wakeup(wakeup_time: str, room_number=ROOM_NUMBER):
    """
    Set an alarm for the customer to wake him up.

    Args:
      room_number (int) : The room number that needs wakeup call
      wakeup_time (str) : The time to remind the customer at
    Returns
      str: An acknowdelgement message for the customer.
    """

    return f'''{{
                  "function-name": "request_wakeup",
                  "parameters": {{
                      "room_number": "{room_number}",
                      "wakeup_time": "{wakeup_time}"
                  }}
              }}'''

# @tool(args_schema = None)
# def redirect_to_reception() -> str:
#   """
#   Redirects the call to the hotel reception when a customer wants to directly
#   interact with a real human
#   """

#   return f"We are transferring the call to the hotel reception. Hold on a bit...."


class StockAvailabilityEntity(BaseModel):
    stock_of: int = Field(..., description="The object that user wants to know the availibility about. Take input from user.")
    query_date: date = Field(..., description="The date user wants to know about the stock. Take input from user.")

    

@tool(args_schema=StockAvailabilityEntity, return_direct=True)
def check_stock_availability(stock_of: str, query_date = TODAY):
    """
    Check for amount of stock in the warehouse

     Args :
      stock_of (int) : The room number the request is made from. Take input from user.
      date (str) : The date time user wants to know about the stock. By default take todays date. Take input from user.

    return :
      str : A message of the amount of stock

    """

    return f'''{{
                    "function-name": "check_stock_availability",
                    "parameters": {{
                        "stock_of": "{stock_of}",
                        "query_date": "{query_date}"
                    }}
                }}'''

class StatusOfRequest(BaseModel):
    request_type: str = Field(..., description="The type of request of the customer")


@tool(args_schema=StatusOfRequest, return_direct=True)
def check_status_request(request_type: str,room_number = ROOM_NUMBER):
    """
    Checks the status of the request.
    Args :
      request_type (int) : The type of request of the customer

    return :
      str : A message of the status of the room
    """

    return f'''{{
                    "function-name": "check_status_request",
                    "parameters": {{
                        "request_type": "{request_type}",
                        "room_number": "{room_number}"
                    }}
                }}'''


class ShuttleServiceEntity(BaseModel):
    location: str = Field(...,
                          description="The location from where the customer will be picked up ")
    time: str = Field(...,
                      description="The time at which the customer will be picked up")


@tool(args_schema=ShuttleServiceEntity, return_direct=True)
def shuttle_service_request(location: str, time: str) -> str:
    """
    Books a shuttle service that picks up or drops off customer.

    Args :
      location (str) : The location from where the customer will be picked up
      time (str) : The exact time of pickup or drop off
    return :
      str : A message that customer is picked or dropped successfully

    """

    return f'''{{
                    "function-name": "shuttle_service_request",
                    "parameters": {{
                        "location": "{location}",
                        "time": "{time}"
                    }}
                }}'''

tools = [
    get_current_temperature,
    book_room,
    order_resturant_item,
    bill_complain_request,
    restaurant_information,
    hotel_information_request,
    emergencyConciergeRequest,
    excursion_recommendation,
    transportation_recommendation,
    food_recommedation,
    room_recommendation,
    # negative_requisition,
    housekeeping_service_request,
    request_room_maintenance,
    request_miscellaneous,
    request_reminder,
    request_wakeup,
    # redirect_to_reception,
    check_stock_availability,
    check_status_request,
    shuttle_service_request,
    request_room_amenity
]  # Add extra function names here...
