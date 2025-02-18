# actions.py
from typing import Any, Text, Dict, List
import datetime
import re
import asyncio

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

def extract_all_info(text: str):
    """
    Extract category-value pairs from text including general user info and dynamic favorite declarations.
    """
    pairs = []
    # Define a boundary that stops capturing at a comma, period, exclamation, question, or the word "and"
    boundary = r"(?=\s*(?:,|\.|!|\?|\band\b)|$)"
    
    patterns = [
        # -- General User Info Patterns --
        (r"my name is\s+([a-zA-Z\s]+?)" + boundary, "name", "{value}"),
        (r"i go by\s+([a-zA-Z\s]+?)" + boundary, "name", "{value}"),
        (r"i am\s+(\d{1,3})\s*years? old" + boundary, "age", "{value}"),
        (r"i'm\s+(\d{1,3})" + boundary, "age", "{value}"),
        (r"my age is\s+(\d{1,3})" + boundary, "age", "{value}"),
        (r"i am\s+(male|female|non[-\s]?binary|other)" + boundary, "gender", "{value}"),
        (r"my gender is\s+(male|female|non[-\s]?binary|other)" + boundary, "gender", "{value}"),
        (r"i live in\s+([a-zA-Z\s]+?)" + boundary, "location", "{value}"),
        (r"my city is\s+([a-zA-Z\s]+?)" + boundary, "location", "{value}"),
        (r"i come from\s+([a-zA-Z\s]+?)" + boundary, "origin", "{value}"),
        (r"i'm from\s+([a-zA-Z\s]+?)" + boundary, "origin", "{value}"),
        (r"i moved to\s+([a-zA-Z\s]+?)" + boundary, "moved_to", "{value}"),
        (r"i am\s+(single|married|divorced|engaged|in a relationship)" + boundary, "relationship_status", "{value}"),
        (r"my instagram is\s+(@[\w\d]+)" + boundary, "instagram", "{value}"),
        (r"my twitter is\s+(@[\w\d]+)" + boundary, "twitter", "{value}"),
        (r"my linkedin is\s+([a-zA-Z0-9_\-]+)" + boundary, "linkedin", "{value}"),
        (r"my email is\s+([\w\.-]+@[\w\.-]+\.\w+)" + boundary, "email", "{value}"),
        (r"you can reach me at\s+([\d\+\-\s]+)" + boundary, "phone", "{value}"),
        (r"i like\s+([a-zA-Z\s,]+?)" + boundary, "likes", "{value}"),
        (r"i love\s+([a-zA-Z\s,]+?)" + boundary, "loves", "{value}"),
        (r"my hobbies include\s+([a-zA-Z\s,]+?)" + boundary, "hobbies", "{value}"),
        (r"i prefer\s+([a-zA-Z\s]+?)" + boundary, "preference", "{value}"),
        (r"my favorite music genre is\s+([a-zA-Z\s]+?)" + boundary, "favorite_music", "{value}"),
        (r"i have\s+([a-zA-Z\s]+?)" + boundary, "health_condition", "{value}"),
        
        # -- Dynamic Favorites Patterns --
        (r"my favorite (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "favorite_{category}", "{value}"),
        (r"my favourite (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "favorite_{category}", "{value}"),
        
        # -- Additional Generic Patterns --
        (r"my (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"my (\w+) are ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
    ]
    
    for pattern, category_template, value_template in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if "{category}" in category_template:
                dynamic_category = match.group(1).strip().replace(" ", "_")
                value = match.group(2).strip()
                category = category_template.replace("{category}", dynamic_category)
            else:
                value = match.group(1).strip()
                category = category_template
            pairs.append((category, value))
    
    return pairs

class ActionExtractUserInfo(Action):
    def name(self) -> Text:
        return "action_extract_user_info"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "")
        # Extract dynamic pairs from the user message
        extracted_pairs = await asyncio.to_thread(extract_all_info, user_message)
        
        # Initialize or update the user_info dictionary
        user_info = tracker.get_slot("user_info") or {}
        for category, value in extracted_pairs:
            user_info[category] = value
            dispatcher.utter_message(text=f"Stored {category}: {value}")
        
        return [SlotSet("user_info", user_info)]

# Optionally, another action that uses the stored slots.
class ActionUseStoredData(Action):
    def name(self) -> Text:
        return "action_use_stored_data"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Retrieve the 'user_info' dictionary from the slot (or default to an empty dict)
        user_info = tracker.get_slot("user_info") or {}

        # Extract desired fields from the dictionary
        name = user_info.get("name")
        age = user_info.get("age")
        location = user_info.get("location")
        
        # Build a response based on the available info
        if name and age and location:
            response = f"Hi {name}, I see you're {age} years old and live in {location}."
        elif name:
            response = f"Hi {name}, nice to meet you!"
        else:
            response = "Hello, I don't have your full info yet. Could you please provide it?"
        
        dispatcher.utter_message(text=response)
        return []

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
