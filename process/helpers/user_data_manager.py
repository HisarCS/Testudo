# helpers/user_data_manager.py
import json
import os

USER_DATA_PATH = "/home/pi/Testudo/user_data.json"

def load_user_data() -> dict:
    """Load user data from a JSON file. Returns {} if file doesn’t exist."""
    if not os.path.exists(USER_DATA_PATH):
        return {}
    with open(USER_DATA_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Log an error if you like, but here we just return {}
            return {}

def save_user_data(data: dict):
    """Save user data back to the JSON file."""
    with open(USER_DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

def merge_new_data(existing_data: dict, extracted_info: list[tuple]) -> dict:
    for item in extracted_info:
        cat, val = item  # unpack the tuple
        existing_data[cat] = val
    return existing_data

