# main.py
import queue
import time
from helpers.speech_helper import (
    init_background_listener, 
    set_keyword_listener_active,
    continuous_recognition, 
    set_ignore_until
)
from helpers.text_to_speech_helper import text_to_speech
from utils.file_utils import cleanup_audio_files

keyword_detected_queue = queue.Queue()

def process_text(input_text):
    return input_text

def conversation_flow():
    """
    Perform a single user query/response flow.
    """
    text_to_speech("How can I help you?")
    
    user_input = continuous_recognition(
        mic_index=8,
        timeout=5,
        max_speak_duration=25
    )
    if user_input:
        print(f"[User Said]: {user_input}")
        response = process_text(user_input)
        text_to_speech(response)

    cleanup_audio_files()
    print("[Main] Conversation ended. Returning to keyword detection...\n")

def main():
    print("[Main] Initializing background keyword listener...")
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

                # Temporarily disable background detection logic
                set_keyword_listener_active(False)

                # Handle conversation
                conversation_flow()

                # Mark a grace period to ignore leftover audio
                # e.g. 2 seconds of ignoring any recognized text.
                set_ignore_until(time.time() + 2.5)

                # Re-enable the background detection
                set_keyword_listener_active(True)

                print("[Main] Listening again for 'turtle'...")

    except KeyboardInterrupt:
        print("[Main] Exiting on Ctrl+C.")
    finally:
        print("[Main] Exit complete.")

if __name__ == "__main__":
    main()

