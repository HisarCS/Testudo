from typing import Any, Text, Dict, List, Optional
import requests
import datetime

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# 1) Greet user
class ActionGreetUser(Action):
    def name(self) -> Text:
        return "action_greet_user"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_name = tracker.get_slot("name")

        if user_name:
            dispatcher.utter_message(
                text=f"Hello, {user_name}! How can I assist you today?"
            )
        else:
            dispatcher.utter_message(text="Hello! What is your name?")

        return []


# 2) Get Weather
class ActionGetWeather(Action):
    def name(self) -> Text:
        return "action_get_weather"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        location = tracker.get_slot("location")

        if not location:
            location = "your area"

        # ---- Placeholder Logic: real logic would call an API (e.g., OpenWeatherMap) ----
        # For instance:
        # api_key = "YOUR_OPENWEATHER_API_KEY"
        # url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
        # response = requests.get(url).json()
        # weather_info = ...
        
        # Dummy example:
        weather_info = "cloudy, around 20°C"

        # We set a slot or simply pass it via utterance:
        return [SlotSet("location", location), SlotSet("weather_info", weather_info)]


# 3) Get Time
class ActionGetTime(Action):
    def name(self) -> Text:
        return "action_get_time"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        now = datetime.datetime.now().strftime("%H:%M")
        return [SlotSet("time_info", now)]


# 4) Get Date
class ActionGetDate(Action):
    def name(self) -> Text:
        return "action_get_date"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        today = datetime.datetime.now().strftime("%d %B %Y")  # or any format you like
        return [SlotSet("date_info", today)]


# 5) Ask Question (General Q&A)
class ActionAskQuestion(Action):
    def name(self) -> Text:
        return "action_ask_question"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # The user's query can be extracted from the last user message
        user_message = tracker.latest_message.get("text")
        
        # Placeholder Q&A logic:
        # For example, you could call Wikipedia API or WolframAlpha
        # We'll do a dummy answer:
        answer = "Google was founded in 1998 in California, USA"

        return [SlotSet("answer", answer)]


# 6) Provide Emotional Support
class ActionProvideEmotionalSupport(Action):
    def name(self) -> Text:
        return "action_provide_emotional_support"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        message = ("I am here for you. It's okay to feel sad sometimes. "
                    "Would you like to talk more about it?")
        
        dispatcher.utter_message(text=message)
        return []


# 7) Servo Control
class ActionServoControl(Action):
    def name(self) -> Text:
        return "action_servo_control"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # You might parse the exact direction or servo instruction from the text
        user_message = tracker.latest_message.get("text").lower()

        from adafruit_servokit import ServoKit

        # Create a ServoKit instance for a 16-channel servo driver
        kit = ServoKit(channels=16)

        def set_servo_angle(channel, angle):
            if angle < 0:
                angle = 0
            elif angle > 180:
                angle = 180
    
            kit.servo[channel].angle = angle
            print("Servo Moved!")
        
        set_servo_angle(kit, channel=0, angle=90)
        set_servo_angle(kit, channel=1, angle=90)
        set_servo_angle(kit, channel=2, angle=90)
        set_servo_angle(kit, channel=3, angle=90)
        set_servo_angle(kit, channel=4, angle=90)
        set_servo_angle(kit, channel=5, angle=90)
        set_servo_angle(kit, channel=6, angle=90)
        set_servo_angle(kit, channel=7, angle=90)
        
        return []


# 8) Turtle Info
class ActionTurtleInfo(Action):
    def name(self) -> Text:
        return "action_turtle_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # Provide details about the Turtle bot
        info = ("I am the Turtle companion robot. I'm equipped with a Raspberry Pi 4, "
                "servo motors, and can perform web lookups, emotional support, and more!")
        dispatcher.utter_message(text=info)
        return []
