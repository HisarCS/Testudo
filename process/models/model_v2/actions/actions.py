# actions.py
from typing import Any, Text, Dict, List, Optional, Text, Tuple
from collections import defaultdict
import datetime
import re
import spacy
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

# ------------------------------------------------------------------------------
# Get Weather (via DuckDuckGo + Selenium) extracting "module__current"
# ------------------------------------------------------------------------------
class ActionGetWeather(Action):
    def name(self) -> Text:
        return "action_get_weather"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        user_text = tracker.latest_message.get("text", "")
        
        # 1) Try searching user text directly
        weather_info = self.duckduckgo_search_weather_selenium(user_text)
        if weather_info:
            # We found weather info by searching the user's text
            dispatcher.utter_message(text=weather_info)
            return []

        # 2) If no weather info from user text, try retrieving 'location' slot
        try:
            location = tracker.get_slot("user_info")["location"]
        except (TypeError, KeyError):
            location = None

        if location:
            # Search "weather in {location}"
            location_query = f"weather in {location}"
            weather_info = self.duckduckgo_search_weather_selenium(location_query)
            if weather_info:
                dispatcher.utter_message(
                    text=f"The weather in {location} is: {weather_info}"
                )
            else:
                dispatcher.utter_message(text="I couldn't find the weather.")
        else:
            # If we couldn't extract the location at all
            dispatcher.utter_message(text="I couldn't find the weather.")

        return []

    def duckduckgo_search_weather_selenium(self, query: str) -> Optional[str]:
        """
        Searches DuckDuckGo for the given `query` and tries to extract
        text from the 'module__current' div using Selenium.
        Returns the text if found, or None if not.
        """
        if not query:
            return None

        options = Options()
        # Adjust these as needed for your environment
        options.binary_location = "/usr/bin/chromium-browser"
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)

        result_text = None

        try:
            driver.get(f"https://duckduckgo.com/?q={query}")
            # Wait for the 'module__current' div to appear
            weather_div = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.module__current"))
            )
            result_text = weather_div.text.strip()
        except Exception:
            # If anything goes wrong or the div is not found, return None
            pass
        finally:
            driver.quit()

        return result_text

# ------------------------------------------------------------------------------
# Get Time (no slot usage)
# ------------------------------------------------------------------------------
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
        dispatcher.utter_message(text=f"The current time is {now}.")
        return []

# ------------------------------------------------------------------------------
# Get Date (no slot usage)
# ------------------------------------------------------------------------------
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
        dispatcher.utter_message(text=f"Today's date is {today}.")
        return []
    
# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

def extract_all_info(text: str) -> List[Dict[str, Any]]:
    """
    Extract category-value pairs from text, including general user info (name, age, etc.)
    and dynamic favorite declarations. If no regex patterns match, fallback to a simple 
    spaCy-based verb/adjective detector for sentences that start with "I".
    """
    pairs = []
    boundary = r"(?=\s*(?:,|\.|!|\?|\band\b)|$)"
    
    patterns = [
        # -- General User Info Patterns --
        # Name
        (r"my name is\s+([a-zA-Z\s]+?)" + boundary, "name", "{value}"),
        (r"i go by\s+([a-zA-Z\s]+?)" + boundary, "name", "{value}"),

        # Age
        (r"i am\s+(\d{1,3})\s*years? old" + boundary, "age", "{value}"),
        (r"i'm\s+(\d{1,3})" + boundary, "age", "{value}"),
        (r"my age is\s+(\d{1,3})" + boundary, "age", "{value}"),

        # Gender
        (r"i am\s+(male|female|non[-\s]?binary|other)" + boundary, "gender", "{value}"),
        (r"my gender is\s+(male|female|non[-\s]?binary|other)" + boundary, "gender", "{value}"),

        # Location / Origin
        (r"i live in\s+([a-zA-Z\s]+?)" + boundary, "location", "{value}"),
        (r"my city is\s+([a-zA-Z\s]+?)" + boundary, "location", "{value}"),
        (r"i come from\s+([a-zA-Z\s]+?)" + boundary, "origin", "{value}"),
        (r"i'm from\s+([a-zA-Z\s]+?)" + boundary, "origin", "{value}"),
        (r"i moved to\s+([a-zA-Z\s]+?)" + boundary, "moved_to", "{value}"),

        # Relationship Status
        (r"i am\s+(single|married|divorced|engaged|in a relationship)" + boundary, "relationship_status", "{value}"),
        
        # Social Media
        (r"my instagram is\s+(@[\w\d]+)" + boundary, "instagram", "{value}"),
        (r"my twitter is\s+(@[\w\d]+)" + boundary, "twitter", "{value}"),
        (r"my linkedin is\s+([a-zA-Z0-9_\-]+)" + boundary, "linkedin", "{value}"),
        
        # Contact Information
        (r"my email is\s+([\w\.-]+@[\w\.-]+\.\w+)" + boundary, "email", "{value}"),
        (r"you can reach me at\s+([\d\+\-\s]+)" + boundary, "phone", "{value}"),

        # Hobbies and Interests
        (r"i like\s+([a-zA-Z\s,]+?)" + boundary, "likes", "{value}"),
        (r"i love\s+([a-zA-Z\s,]+?)" + boundary, "loves", "{value}"),
        (r"my hobbies include\s+([a-zA-Z\s,]+?)" + boundary, "hobbies", "{value}"),

        # More Personal Preferences
        (r"i prefer\s+([a-zA-Z\s]+?)" + boundary, "preference", "{value}"),
        (r"my favorite music genre is\s+([a-zA-Z\s]+?)" + boundary, "favorite_music", "{value}"),
        
        # Health Conditions
        (r"i have\s+([a-zA-Z\s]+?)" + boundary, "health_condition", "{value}"),
        
        # -- Dynamic Favorites Patterns --
        (r"my favorite (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "favorite_{category}", "{value}"),
        (r"my favourite (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "favorite_{category}", "{value}"),
        
        (r"my (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"my (\w+) are ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        
        (r"I (\w+) in ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"I (\w+) at ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"I (\w+) from ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"I (\w+) as ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"I (\w+) to ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        
        (r"i'm\s+([a-zA-Z\s]+?)" + boundary, "current_user_adj", "{value}"),
        (r"i am\s+([a-zA-Z\s]+?)" + boundary, "current_user_adj", "{value}"),
        (r"i was\s+([a-zA-Z\s]+?)" + boundary, "past_user_adj", "{value}"),
        (r"we were\s+([a-zA-Z\s]+?)" + boundary, "users_adj", "{value}"),
        
        (r"he is\s+([a-zA-Z\s]+?)" + boundary, "other_current_user_adj", "{value}"),
        (r"he was\s+([a-zA-Z\s]+?)" + boundary, "other_past_user_adj", "{value}"),
        (r"she is\s+([a-zA-Z\s]+?)" + boundary, "other_current_user_adj", "{value}"),
        (r"she was\s+([a-zA-Z\s]+?)" + boundary, "other_past_user_adj", "{value}"),
        (r"they were\s+([a-zA-Z\s]+?)" + boundary, "they_user_adj", "{value}"),
    ]
    
    extracted_pairs = []

    # Regex-based extraction
    for pattern, category_template, value_template in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if "{category}" in category_template:
                dynamic_category = match.group(1).strip().replace(" ", "_")
                value = match.group(2).strip()
                category = category_template.replace("{category}", dynamic_category)
            else:
                value = match.group(1).strip()
                category = category_template
            extracted_pairs.append((category, value))

    # If nothing was extracted, try spaCy fallback
    if not extracted_pairs:
        doc = nlp(text.lower().strip())

        if text.lower().startswith("i") or text.lower().startswith("i'm"):
            for token in doc:
                if token.pos_ == "VERB" and token.dep_ == "ROOT":
                    dobj = [child.text for child in token.children if child.dep_ in ["dobj", "attr", "acomp", "pobj"]]
                    if dobj:
                        extracted_pairs.append((token.lemma_ + "s", " ".join(dobj)))

            if not extracted_pairs:
                for token in doc:
                    if token.dep_ == "ROOT" and token.lemma_.lower() in ["be"] and token.pos_ in ["AUX", "VERB"]:
                        adj_kids = [child.text for child in token.children if child.pos_ == "ADJ"]
                        for adj in adj_kids:
                            extracted_pairs.append(("current_user_adj", adj))

    return extracted_pairs


### **Fixed Category-Value Storage**
class ActionExtractUserInfo(Action):
    def name(self) -> Text:
        return "action_extract_user_info"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "")
        raw_pairs = await asyncio.to_thread(extract_all_info, user_message)

        if not raw_pairs:
            return []

        grouped_new_data = defaultdict(list)
        for category, value in raw_pairs:
            grouped_new_data[category].append(value)

        current_user_info = tracker.get_slot("user_info") or []
        existing_data_dict = {obj["category"]: obj["values"] for obj in current_user_info}

        for cat, vals in grouped_new_data.items():
            if cat in existing_data_dict:
                existing_data_dict[cat].extend(vals)
            else:
                existing_data_dict[cat] = vals

        updated_user_info = [{"category": c, "values": list(set(v))} for c, v in existing_data_dict.items()]
        return [SlotSet("user_info", updated_user_info)]

class ActionUseStoredData(Action):
    def name(self) -> Text:
        return "action_use_stored_data"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_info = tracker.get_slot("user_info") or []
        name = next((item["values"][0] for item in user_info if item["category"] == "name"), None)
        age = next((item["values"][0] for item in user_info if item["category"] == "age"), None)
        location = next((item["values"][0] for item in user_info if item["category"] == "location"), None)

        if name and age and location:
            response = f"Hi {name}, I see you're {age} years old and live in {location}."
        elif name:
            response = f"Hi {name}, nice to meet you!"
        else:
            response = "Hello, I don't have your full info yet. Could you please provide it?"
        
        dispatcher.utter_message(text=response)
        return []

# ------------------------------------------------------------------------------
# AskQuestion (DuckDuckGo + Selenium)
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
        options.binary_location = "/usr/bin/chromium-browser"
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)

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
# Servo Control (example code, uses hardware)
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
