# helpers/user_data_manager.py
import json
import os

USER_DATA_PATH = "/home/pi/Testudo/user_data.json"

def load_user_data() -> dict:
    """Load user data from a JSON file. Returns {} if file doesn’t exist."""
    if not os.path.exists(USER_DATA_PATH):
        return {}
    with open(USER_DATA_PATH, "r") as f:
        return json.load(f)

def save_user_data(data: dict):
    """Save user data back to the JSON file."""
    with open(USER_DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

def merge_new_data(existing_data: dict, extracted_info: list[dict]) -> dict:
    """
    Merges a list of extracted info into existing_data. 
    For example, if we extracted {'category': 'name', 'value': 'Alice'},
    store it in existing_data['name'] = 'Alice'.
    Return the updated dictionary.
    """
    for item in extracted_info:
        cat = item["category"]
        val = item["value"]
        # You can decide if you want arrays or single values, 
        # or keep a history, etc. For simplicity:
        existing_data[cat] = val
    return existing_data
