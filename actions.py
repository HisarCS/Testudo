from typing import Any, Text, Dict, List
from transformers import pipeline
import requests
import datetime

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
            return [SlotSet("location", "Unkown"), SlotSet("weather_info", "Unkown")]

        API_KEY = "401462fb8ae4613950ea28c83c14572c"
        CITY = location

        url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
        response = requests.get(url).json()

        weather_description = response['weather'][0]['description']
        temperature = response['main']['temp']

        weather_info = f"The weather in {CITY} is {weather_description} with a temperature of {temperature}°C."

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

class ActionAskQuestion(Action):
    def name(self):
        return "action_ask_question"

    def run(self, dispatcher, tracker, domain):
        user_question = (tracker.latest_message.get("text") or "").strip()
        print(f"🛠 Received question: {user_question}")

        # ✅ Call the search function and get the result
        summary = self.google_search_selenium(user_question)

        # ✅ Send the result to the user
        dispatcher.utter_message(text=summary)
        return []

    def google_search_selenium(self, query):
        """ Searches Google and extracts the featured snippet. """

        # ✅ Set Chrome options
        options = Options()
        options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection

        # ✅ Set the correct ChromeDriver path
        service = Service("/opt/homebrew/bin/chromedriver")  # Use correct path
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(f"https://www.google.com/search?q={query}")

        summary = "Sorry, I couldn't find an answer."

        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.FLP8od"))
            )
            summary = element.text.strip()
        except Exception:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.IZ6rdc"))
                )
                summary = element.text.strip()
            except Exception:
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.PZPZlf.ssJ7i.B5dxMb"))
                    )

                    # Locate all <b> tags inside this div
                    bold_elements = element.find_elements(By.TAG_NAME, "b")

                    # Extract text only from bold elements with font-size > 16px
                    for bold in bold_elements:
                        font_size = float(bold.value_of_css_property("font-size").replace("px", ""))
                        if font_size > 16:
                            summary = bold.text.strip()
                            break  # Stop after finding the first valid one

                except Exception as e:
                    print("❌ Element not found:", e)

        driver.quit()
        return summary

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
