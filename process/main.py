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

keyword_detected_queue = queue.Queue()

def start_rasa_servers():
    """
    Start both the Rasa main server (port 5005) and the action server (port 5055)
    as background subprocesses, same as your old code with Google STT did.
    """
    print("[Main] Starting Rasa servers in background...")

    # Main Rasa server on port 5005
    rasa_process = subprocess.Popen(
        [
            "rasa", "run",
            "--enable-api",
            "--cors", "*",
            "--port", "5005",
            "--model", "models/model_v2/models",
            "--endpoints", "models/model_v2/endpoints.yml",
            "--debug"
        ],
        text=True
    )

    # Action server on port 5055
    action_process = subprocess.Popen(
        [
            "rasa", "run",
            "actions",
            "--actions", "models.model_v2.actions.actions",
            "--debug"
        ],
        text=True
    )

    return rasa_process, action_process

def wait_for_rasa_server(url="http://localhost:5005/"):
    """
    Wait until the main Rasa server returns HTTP 200 at `url`.
    """
    print(f"[Startup] Waiting for Rasa server at {url} to be ready...")
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"[Startup] Rasa main server at {url} is up and running.")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)

def wait_for_action_server_any(url="http://localhost:5055/", max_retries=60):
    """
    Wait until we get ANY HTTP response code from the action server on `url`.
    Then sleep an extra few seconds to let it finish fully loading.
    """
    print(f"[Startup] Waiting for action server at {url} to respond with *any* code...")
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=3)
            status = response.status_code
            # If we get *any* status code, that means it's listening on the port.
            print(f"[Startup] Action server responded with status {status}.")
            print("[Startup] Sleeping extra 200 seconds to ensure it finishes loading...")
            time.sleep(3)  # Give it extra time after the first response
            return
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)

    print(f"[Startup] Action server not responding after {max_retries} attempts.")

def process_text(input_text: str) -> str:
    """
    Sends the user's text to the locally running Rasa server
    via REST and returns the bot's response as a single string.
    """
    rasa_url = "http://localhost:5005/webhooks/rest/webhook"
    payload = {
        "sender": "test_user",
        "message": input_text
    }
    try:
        response = requests.post(rasa_url, json=payload, timeout=15)
        if response.status_code == 200:
            messages = response.json()  # List of bot messages
            if messages:
                replies = [msg.get("text", "") for msg in messages if msg.get("text")]
                return " ".join(replies).strip()
            else:
                return "I didn't receive any response from Rasa."
        else:
            return f"Error from Rasa: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Request to Rasa failed: {e}"

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
    user_input = continuous_recognition(
        timeout=7,          # 5s to begin speech
        max_speak_duration=25,
        # 2.5s silence ends speech
        # If user never starts speaking => returns None
    )
    if not user_input:
        print("[Conversation] No speech within 5s => fallback to keyword detection.")
        return

    # We do have user input => Rasa + TTS
    response = process_text(user_input)
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

        response = process_text(user_input)
        print(response)
        text_to_speech(response)

        # rinse & repeat (no break here => user can keep talking)

    # We'll never reach here in normal flow.


def main():
    time.sleep(10)
    
    text_to_speech("Starting activation process")
    print("[Main] Launching Rasa servers...")
    rasa_proc, action_proc = start_rasa_servers()

    # 1) Wait for the MAIN server on port 5005 (needs a 200)
    wait_for_rasa_server("http://localhost:5005/")

    # 2) Wait for the ACTION server on port 5055 (accept any response, then sleep 200s)
    wait_for_action_server_any("http://localhost:5055/")
    
    response = process_text("When was world war two?")
    text_to_speech(response)

    # 3) Only now do we init the Vosk keyword detection
    print("[Main] Both Rasa servers are up (plus extra wait). Initializing background keyword listener...")
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
    finally:
        print("[Main] Terminating Rasa processes...")
        rasa_proc.terminate()
        action_proc.terminate()
        rasa_proc.wait()
        action_proc.wait()
        print("[Main] Exit complete.")

if __name__ == "__main__":
    main()
