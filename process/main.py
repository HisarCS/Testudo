import os
import sys
from helpers.speech_helper import listen_for_keyword, recognize_speech
from helpers.text_to_speech_helper import text_to_speech
from utils.file_utils import cleanup_audio_files

# Global variable for storing the recognized text
text = ""

# Empty function for processing the recognized text
def process_text(input_text):
    """Placeholder for text processing logic."""
    return input_text  # Return the input as-is for now

def main_loop():
    global text

    print("System is active. Listening for the keyword 'turtle'...")

    while True:
        # Step 1: Listen for the keyword
        keyword_detected = listen_for_keyword(keyword="turtle")

        if keyword_detected:
            text_to_speech('Hello I am the turtle! How can I help you?')
            print("Keyword detected! Starting speech-to-text.")
            
            # Step 2: Perform speech-to-text
            text = recognize_speech()
            if text:
                print(f"Captured text: {text}")

                # Step 3: Process the text (placeholder function)
                processed_text = process_text(text)

                # Step 4: Respond to the user using text-to-speech
                text_to_speech(processed_text)

                # Step 5: Cleanup and reset
                cleanup_audio_files()
                text = ""  # Reset the global variable
                print("System reset. Listening for the keyword 'turtle'...")

if __name__ == "__main__":
    main_loop()
