# actions.py
from typing import Any, Text, Dict, List
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

        return [SlotSet("location", location), SlotSet("weather_info", weather_info)]

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

# ------------------------------------------------------------------------------
# AskQuestion action that uses DuckDuckGo + Selenium
# ------------------------------------------------------------------------------
class ActionAskQuestion(Action):
    def name(self) -> Text:
        return "action_ask_question"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_question = (tracker.latest_message.get("text") or "").strip()
        print(f"🛠 Received question: {user_question}")

        answer = self.duckduckgo_search_selenium(user_question)
        dispatcher.utter_message(text=answer)
        return []

    def duckduckgo_search_selenium(self, query: str) -> str:
        """
        Searches DuckDuckGo and extracts an answer from a <p> element using Selenium.
        Designed for use on a Raspberry Pi with Chromium + chromedriver.
        """
        options = Options()
        # Point to your Pi's Chromium browser location:
        options.binary_location = "/usr/bin/chromium-browser"
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)

        # Load DuckDuckGo with the query
        driver.get(f"https://duckduckgo.com/?q={query}")

        answer = "Sorry, I couldn't find an answer."

        try:
            # Try a known CSS selector for a search-answer snippet
            p_element = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.VrBPSncUavA1d7C9kAc5.FQ2XxQQbwcMwCtbtebpY p")
                )
            )
            answer = p_element.text.strip()
        except Exception:
            # Try a fallback CSS selector
            try:
                p_element = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.aSBdOftk9efiVV8GwLLE"))
                )
                answer = p_element.text.strip()
            except Exception:
                pass

        driver.quit()
        return answer

# ------------------------------------------------------------------------------
# Provide Emotional Support
# ------------------------------------------------------------------------------
class ActionProvideEmotionalSupport(Action):
    def name(self) -> Text:
        return "action_provide_emotional_support"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        message = (
            "I am here for you. It's okay to feel sad sometimes. "
            "Would you like to talk more about it?"
        )
        
        dispatcher.utter_message(text=message)
        return []

# ------------------------------------------------------------------------------
# Servo Control
# ------------------------------------------------------------------------------
class ActionServoControl(Action):
    def name(self) -> Text:
        return "action_servo_control"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # You can parse direction from user_message if needed
        user_message = tracker.latest_message.get("text").lower()
        
        from adafruit_servokit import ServoKit
        kit = ServoKit(channels=16)

        # Helper function to safely set a servo angle
        def set_servo_angle(kit_instance, channel, angle):
            """Set the servo channel to a safe angle [0..180]."""
            if angle < 0:
                angle = 0
            elif angle > 180:
                angle = 180
            kit_instance.servo[channel].angle = angle
            print("[Servo] Moved channel", channel, "to", angle)

        # Example: set 8 channels to 90 degrees
        for channel_idx in range(8):
            set_servo_angle(kit, channel_idx, 90)

        dispatcher.utter_message(text="Servos have been set to 90 degrees.")
        return []

# ------------------------------------------------------------------------------
# Turtle Info
# ------------------------------------------------------------------------------
class ActionTurtleInfo(Action):
    def name(self) -> Text:
        return "action_turtle_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        info = (
            "I am Testudo, an AI-integrated, quadruped companion. "
            "I'm equipped with a Raspberry Pi 4, servo motors, and can "
            "perform web lookups, store user data, and more!"
        )
        dispatcher.utter_message(text=info)
        return []
