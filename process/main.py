# main.py
import queue
import time
from helpers.speech_helper import init_background_listener, set_keyword_listener_active
from helpers.text_to_speech_helper import text_to_speech
from utils.file_utils import cleanup_audio_files
from helpers.speech_helper import continuous_recognition

keyword_detected_queue = queue.Queue()

def process_text(input_text):
    return input_text

def conversation_flow():
    """
    Perform a single user query/response flow.
    """
    text_to_speech("Hello, I am the turtle! How can I help you?")
    
    user_input = continuous_recognition(
        mic_index=8,
        timeout=5,           # wait 5s for speech to start
        phrase_time_limit=10 # capture up to 10s
    )
    if user_input:
        print(f"[User Said]: {user_input}")
        response = process_text(user_input)
        text_to_speech(response)

    cleanup_audio_files()
    print("[Main] Conversation ended. Returning to keyword detection...\n")

def main():
    print("[Main] Initializing background keyword listener...")
    # Only start the listener once
    listener_thread = init_background_listener(
        keyword="turtle",
        event_queue=keyword_detected_queue,
        mic_index=8
    )

    print("[Main] System is active. Waiting for 'turtle'...")

    try:
        while True:
            # Block until we get a True from the queue
            keyword_detected = keyword_detected_queue.get()
            if keyword_detected:
                print("[Main] Keyword 'turtle' detected!")

                # Temporarily disable the background detection
                set_keyword_listener_active(False)

                # Handle conversation
                conversation_flow()

                # Re-enable the background detection
                set_keyword_listener_active(True)

                print("[Main] Listening again for 'turtle'...")

    except KeyboardInterrupt:
        print("[Main] Exiting on Ctrl+C.")
    finally:
        # We won't 'stop' the listener to avoid segfaults, just let the program exit
        print("[Main] Exit complete.")

if __name__ == "__main__":
    main()

