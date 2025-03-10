import subprocess
import time
import requests
import queue
from helpers.speech_helper import (
    init_background_listener,
    continuous_recognition,
    set_ignore_until
)
from helpers.text_to_speech_helper import text_to_speech
from utils.file_utils import cleanup_audio_files
from helpers.user_data_extraction import extract_all_info
from helpers.user_data_manager import load_user_data, save_user_data, merge_new_data

keyword_detected_queue = queue.Queue()

import requests

def call_lm_studio(
    prompt: str,
    host: str = "10.0.90.140",    # or the IP of your Windows machine
    port: int = 1234,             # LM Studio port
    model: str = "wizard-vicuna-13b-uncensored",
    max_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
    n: int = 1,
    stream: bool = False
) -> str:
    """
    Send 'prompt' to LM Studio's /v1/completions endpoint, parse the JSON
    it returns, and extract the text from the first choice.
    """
    url = f"http://{host}:{port}/v1/completions"
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "n": n,
        "stream": stream,
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        # We parse the JSON and get the text from choices[0]["text"].
        response_data = response.json()
        choices = response_data.get("choices", [])
        if not choices:
            return "[No completion returned]"

        # Extract text from the first choice
        text = choices[0].get("text", "")

        # Strip leading/trailing whitespace/newlines:
        text = text.strip()

        return text

    except requests.exceptions.RequestException as e:
        print(f"[LM Studio] Error: {e}")
        return "[Error retrieving LM Studio response]"

def process_text(input_text: str) -> str:
    """
    Simple wrapper to call LM Studio with user input and return the model's response.
    """
    return call_lm_studio(input_text)

def conversation_flow():
    """
    New conversation flow logic:
      1) Bot says "How can I help you?"
      2) Listen for user up to 5s (timeout=5). 
         If no speech => fallback to keyword detection.
      3) Once user speaks (silence_timeout=2.5 to finalize),
         pass text to Rasa, TTS the response.
      4) Then repeatedly listen for user again with 6s timeout. 
         If no speech => fallback. 
         Otherwise => respond again, etc.
      5) Continue until user doesn't speak for 6s => fallback.
    """
    # 1) Prompt
    text_to_speech("How can I help you?")

    # 2) First user input => must start within 5s
    user_input =  continuous_recognition(
        timeout=7,          # 5s to begin speech
        max_speak_duration=25,
         #2.5s silence ends speech
         #If user never starts speaking => returns None
    )
    if not user_input:
        print("[Conversation] No speech within 5s => fallback to keyword detection.")
        return []
    
    extracted = extract_all_info(user_input)
    print("EXTRACTED: ", extracted)
    if extracted:
        print(f"[Conversation] Extracted new user data: {extracted}")
        # Load existing data, merge, save
        existing_data = load_user_data()
        updated_data = merge_new_data(existing_data, extracted)
        save_user_data(updated_data)
    
    # --- Prompt engineering step: 
    #  e.g., prepend "User info: <some summary>" to user input 
    user_data_str = ""
    # read the newly updated data from file
    user_data = load_user_data()
    if user_data:
        # You can format it however you want:
        user_data_str = (
            "Here is the known user data:\n"
            + "\n".join([f"{k}: {v}" for k, v in user_data.items()])
            + "\n"
        )
    
    # Combine user data + the user’s text into a single prompt
    engineered_input = f"{user_data_str}User says: {user_input}"

    # Now pass the combined text to Rasa
    response = process_text(engineered_input)
    print("RESPOND FOUND: ", response)
    text_to_speech(response)

    # 3) Now repeat until user doesn't speak within 6s
    while True:
        user_input = continuous_recognition(
            timeout=7,        # 6s to begin speech
            max_speak_duration=25
        )
        if not user_input:
            print("[Conversation] No speech within 6s => fallback to keyword detection.")
            return

        # Extract data again
        extracted = extract_all_info(user_input)
        if extracted:
            print(f"[Conversation] Extracted new user data: {extracted}")
            existing_data = load_user_data()
            updated_data = merge_new_data(existing_data, extracted)
            save_user_data(updated_data)

        # Re-load user_data for each new turn
        user_data = load_user_data()
        user_data_str = ""
        if user_data:
            user_data_str = (
                "Here is some known user data:\n"
                + "\n".join([f"{k}: {v}" for k, v in user_data.items()])
                + "\n"
            )

        engineered_input = f"{user_data_str}User says: {user_input}"
        print("Input: " + engineered_input)
        response = process_text(engineered_input)
        print("Output: " + response)
        text_to_speech(response)

        # rinse & repeat (no break here => user can keep talking)

    # We'll never reach here in normal flow.


def main():
    stop_listening_fn = init_background_listener(
        keyword="turtle",
        event_queue=keyword_detected_queue,
        model_path="/home/pi/Testudo/vosk-model-small-en-us-0.15"
    )
    text_to_speech("System is active. Waiting for the keyword")
    print("[Main] System is active. Waiting for the keyword 'turtle'...")

    try:
        while True:
            keyword_detected = keyword_detected_queue.get()
            if keyword_detected:
                print("[Main] Keyword 'turtle' detected!")

                # Stop background listener to free the mic for conversation
                stop_listening_fn()

                # Run conversation flow
                conversation_flow()

                # After the conversation ends, we re-init the background listener
                stop_listening_fn = init_background_listener(
                    keyword="turtle",
                    event_queue=keyword_detected_queue,
                    model_path="/home/pi/Testudo/vosk-model-small-en-us-0.15"
                )
                
                # After we re-init, ignore triggers for a few seconds
                set_ignore_until(time.time() + 1)

    except KeyboardInterrupt:
        print("[Main] Exiting on Ctrl+C.")

if __name__ == "__main__":
    main()
