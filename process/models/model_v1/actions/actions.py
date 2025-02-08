from typing import Any, Text, Dict, List, Optional
import wikipediaapi
from transformers import pipeline
import wikipedia
import re
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


import re
import wikipedia
import wikipediaapi
from rasa_sdk import Action
from rasa_sdk.events import EventType

class ActionAskQuestion(Action):
    def name(self):
        return "action_ask_question"

    def run(self, dispatcher, tracker, domain):
        user_question = (tracker.latest_message.get("text") or "").strip()
        print(f"🛠 Received question: {user_question}")

        # 1. Identify question type + the main subject (X)
        question_type, subject = self.parse_question(user_question)

        if not subject:
            # If we cannot extract an entity at all, apologize
            dispatcher.utter_message(text="I'm sorry, I couldn't figure out what you're asking.")
            return []

        # 2. Fetch a short summary from Wikipedia (first paragraph).
        summary = self.get_wikipedia_summary(subject)
        if not summary:
            dispatcher.utter_message(text="I'm sorry, I couldn't find information on that.")
            return []

        # 3. Try specialized extraction for short answers
        short_answer = None

        if question_type in ["invented", "discovered", "wrote", "ceo"]:
            short_answer = self.extract_person(question_type, summary)

        elif question_type == "capital_of":
            short_answer = self.extract_capital(summary)

        elif question_type == "where_is":
            # For "Where is X?" we might find a mention like "X is a country in..."
            # or "X is a city in [COUNTRY]."
            short_answer = self.extract_location(summary)

        # If we found a direct short answer, great!
        if short_answer:
            dispatcher.utter_message(text=short_answer)
            return []

        # Else, fallback to returning the short summary.
        dispatcher.utter_message(text=summary)
        return []

    def parse_question(self, question):
        """
        Return (question_type, subject):
          question_type: 'invented', 'discovered', 'wrote', 'ceo', 'capital_of', 'where_is', or None
          subject: the entity (e.g. 'telephone', 'spain', '1984') or None
        """
        q_lower = question.lower()

        # Regex for capturing typical patterns: e.g. "who invented the telephone"
        # We'll try some simple captures:
        # e.g. "who invented (the )?(.*)"
        # You might further refine or handle quotes.

        # WHO INVENTED X?
        match = re.match(r"who\s+(?:invented|invent) (?:the\s+)?(.*)\??", q_lower)
        if match:
            return ("invented", match.group(1).strip())

        # WHO DISCOVERED X?
        match = re.match(r"who\s+(?:discovered|discover) (?:the\s+)?(.*)\??", q_lower)
        if match:
            return ("discovered", match.group(1).strip())

        # WHO WROTE X?
        match = re.match(r"who\s+(?:wrote|write|authored) (?:the\s+)?(.*)\??", q_lower)
        if match:
            return ("wrote", match.group(1).strip())

        # WHO IS THE CEO OF X? (or who is the ceo of Tesla?)
        match = re.match(r"who\s+is\s+the\s+ceo\s+of\s+(.*)\??", q_lower)
        if match:
            return ("ceo", match.group(1).strip())

        # WHAT IS THE CAPITAL OF X?
        match = re.match(r"(?:what|which)\s+is\s+the\s+capital\s+of\s+(.*)\??", q_lower)
        if match:
            return ("capital_of", match.group(1).strip())

        # WHERE IS X?
        match = re.match(r"where\s+is\s+(.*)\??", q_lower)
        if match:
            return ("where_is", match.group(1).strip())

        # Otherwise, None
        return (None, None)

    def get_wikipedia_summary(self, subject):
        """
        Return the first ~2 sentences from the best Wikipedia page match for 'subject'.
        """
        try:
            # 1. Search up to 3 results
            search_results = wikipedia.search(subject, results=3)
            if not search_results:
                return None

            wiki_wiki = wikipediaapi.Wikipedia(language="en", user_agent="RaspiBot/1.0 (mehmet@example.com)")
            for title in search_results:
                page = wiki_wiki.page(title)
                if page.exists():
                    # Skip disambiguation pages
                    if "may refer to" in page.summary.lower():
                        continue
                    # Return the first paragraph, or first 2 sentences
                    # The summary can have multiple paragraphs. We'll just take the first.
                    paragraphs = page.summary.split("\n")
                    first_para = paragraphs[0]
                    # Maybe limit to 2 sentences max
                    sentences = first_para.split(". ")
                    short_summary = ". ".join(sentences[:2]).strip() + "."
                    if len(short_summary) < 10:
                        continue
                    return short_summary
        except Exception as e:
            print(f"⚠️ Wikipedia error: {e}")

        return None

    def extract_person(self, question_type, summary):
        """
        For "who invented X?", "who discovered X?", "who wrote X?", "who is the ceo of X?",
        try to find phrases like 'invented by XXX', 'discovered by XXX', 'written by XXX', 'CEO is XXX', etc.
        Return the short phrase or None.
        """
        summary_lower = summary.lower()

        if question_type == "invented":
            # e.g. "... was invented by Alexander Graham Bell ..."
            match = re.search(r"(?:invented\s+by\s+)([A-Z][A-Za-z .-]+)", summary)
            if match:
                return match.group(1).strip()

            # Or "inventor is " ...
            match = re.search(r"(?:inventor\s+is\s+)([A-Z][A-Za-z .-]+)", summary)
            if match:
                return match.group(1).strip()

        elif question_type == "discovered":
            # "... was discovered by Christopher Columbus ..."
            match = re.search(r"(?:discovered\s+by\s+)([A-Z][A-Za-z .-]+)", summary)
            if match:
                return match.group(1).strip()

        elif question_type == "wrote":
            # "... was written by Herman Melville ..."
            match = re.search(r"(?:written\s+by\s+)([A-Z][A-Za-z .-]+)", summary)
            if match:
                return match.group(1).strip()

            # or "author is ..."
            match = re.search(r"(?:author\s+is\s+)([A-Z][A-Za-z .-]+)", summary)
            if match:
                return match.group(1).strip()

        elif question_type == "ceo":
            # "... The CEO is Elon Musk ..."
            match = re.search(r"(?:ceo\s+(?:of|is)\s+)([A-Z][A-Za-z .-]+)", summary)
            if match:
                return match.group(1).strip()

            # or "chief executive officer is X"
            match = re.search(r"(?:chief executive officer\s+(?:of|is)\s+)([A-Z][A-Za-z .-]+)", summary)
            if match:
                return match.group(1).strip()

        return None

    def extract_capital(self, summary):
        """
        For "What is the capital of X?" we might see patterns like:
        'X is a country whose capital is <city>'
        '... capital city is <city> ...'
        'the capital is <city> ...'
        Return the first city name if matched.
        """
        match = re.search(r"(?:capital(?: city)?\s+is\s+)([A-Z][A-Za-z .-]+)", summary)
        if match:
            return match.group(1).strip()
        return None

    def extract_location(self, summary):
        """
        For "Where is X?", we might see:
        'X is a country in Europe'
        'X is a city in Turkey'
        Return a short phrase "city in Turkey" or "country in Europe"
        """
        # Something like "X is a (country|city|place) in Y"
        match = re.search(r"is\s+a\s+(\b(?:city|country|province|region|state)\b)\s+in\s+([A-Z][A-Za-z .-]+)", summary)
        if match:
            return f"a {match.group(1)} in {match.group(2)}"
        return None

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
