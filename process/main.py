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
    Start both the Rasa server (for conversation) and Rasa action server
    as background subprocesses.
    """
    rasa_process = subprocess.Popen(
        [
            "rasa",
            "run",
            "--enable-api",
            "--cors", "*",
            "--port", "5005",
            "--model", "models/model_v1/models",
            "--endpoints", "models/model_v1/endpoints.yml",
            "--debug"
        ],
        text=True
    )

    action_process = subprocess.Popen(
        [
            "rasa",
            "run",
            "actions",
            "--actions",
            "models.model_v1.actions.actions",
            "--debug"
        ],
        text=True
    )

    return rasa_process, action_process

def wait_for_rasa_server(url="http://localhost:5005/"):
    """
    Poll the Rasa server until it responds with status 200.
    """
    print("[Startup] Waiting for Rasa server to be ready...")
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("[Startup] Rasa server is up and running.")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)

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
    Perform a single user query/response flow.
    """
    
    user_input = continuous_recognition(
        mic_index=2,
        timeout=5,
        max_speak_duration=25
    )
    if user_input:
        print(f"[User Said]: {user_input}")
        response = process_text(user_input)
        print(f"[Bot Reply]: {response}")
        text_to_speech(response)

    cleanup_audio_files()
    print("[Main] Conversation ended. Returning to keyword detection...\n")

def main():
    print("[Main] Starting Rasa servers in background...")
    rasa_proc, action_proc = start_rasa_servers()
    wait_for_rasa_server("http://localhost:5005")

    print("[Main] Initializing background keyword listener...")
    
    # init_background_listener now returns a "stop_listening_fn" you can call
    stop_listening_fn = init_background_listener(
        keyword="testudo",
        event_queue=keyword_detected_queue,
        mic_index=2
    )

    print("[Main] System is active. Waiting for 'testudo'...")

    try:
        while True:
            keyword_detected = keyword_detected_queue.get()
            if keyword_detected:
                print("[Main] Keyword 'testudo' detected!")
                
                # 1) Stop the background listener to free the mic
                stop_listening_fn()
                
                text_to_speech("How can I help you?")
                
                while True:
                    conversation_flow()

                    set_ignore_until(time.time() + 1.5)

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
