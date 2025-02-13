from typing import Any, Text, Dict, List, Optional
import wikipedia
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

        today = datetime.datetime.now().strftime("%d %B %Y")
        return [SlotSet("date_info", today)]

class ActionAskQuestion(Action):
    def name(self):
        return "action_ask_question"

    def run(self, dispatcher, tracker, domain):
        user_question = (tracker.latest_message.get("text") or "").strip()
        print(f"🛠 Received question: {user_question}")

        # Call the search function and get the result
        answer = self.duckduckgo_search_selenium(user_question)

        # Send the result to the user
        dispatcher.utter_message(text=answer)
        return []

    def duckduckgo_search_selenium(query):
    """ Searches DuckDuckGo and extracts the answer from a <p> element using Selenium on Raspberry Pi. """

    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    # Load DuckDuckGo with the query.
    driver.get(f"https://duckduckgo.com/?q={query}")

    answer = "Sorry, I couldn't find an answer."

    try:
        # Wait for a <p> element that might contain the answer
        p_element = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.VrBPSncUavA1d7C9kAc5.FQ2XxQQbwcMwCtbtebpY p"))
        )
        answer = p_element.text.strip()
    except Exception as e:
        try:
            p_element = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.aSBdOftk9efiVV8GwLLE"))
            )
            answer = p_element.text.strip()
        except Exception as e:
            pass

    driver.quit()
    return answer


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
        info = ("I am Testudo, an AI-integrated, quadruped companion.. I'm equipped with a Raspberry Pi 4, "
                "servo motors, and can perform web lookups, store user data, and more!")
        dispatcher.utter_message(text=info)
        return []
