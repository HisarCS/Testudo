import subprocess
import time
import requests
import queue

import os
from gtts import gTTS
from pydub import AudioSegment
import pyaudio
import wave
import threading

# Local imports
from helpers.speech_helper import (
    init_background_listener,
    continuous_recognition,
    set_ignore_until
)
from helpers.text_to_speech_helper import text_to_speech
from helpers.audio_device_helper import get_input_device_index, get_output_device_index
from utils.file_utils import cleanup_audio_files
from helpers.user_data_extraction import extract_all_info
from helpers.user_data_manager import load_user_data, save_user_data, merge_new_data

from vosk import Model  # We'll load the model once here

keyword_detected_queue = queue.Queue()


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
        
        response_data = response.json()
        choices = response_data.get("choices", [])
        if not choices:
            return "[No completion returned]"

        text = choices[0].get("text", "")
        return text.strip()

    except requests.exceptions.RequestException as e:
        print(f"[LM Studio] Error: {e}")
        return "[Error retrieving LM Studio response]"


def process_text(input_text: str) -> str:
    """
    Simple wrapper to call LM Studio with user input and return the model's response.
    """
    return call_lm_studio(input_text)


def conversation_flow(vosk_model):
    """
    New conversation flow logic:
      1) Bot says "How can I help you?"
      2) Listen for user up to 7s (timeout=7).
         If no speech => fallback to keyword detection.
      3) Once user speaks (silence_timeout=2.0), pass text to LM Studio, TTS response.
      4) Repeat until user doesn't speak for 7s => fallback.
    """
    text_to_speech("How can I help you?")

    user_input = continuous_recognition(
        vosk_model=vosk_model,
        timeout=7,
        max_speak_duration=25,
        silence_timeout=2.5
    )
    if not user_input:
        print("[Conversation] No speech within 7s => fallback to keyword detection.")
        return []

    extracted = extract_all_info(user_input)
    print("EXTRACTED: ", extracted)
    if extracted:
        print(f"[Conversation] Extracted new user data: {extracted}")
        existing_data = load_user_data()
        updated_data = merge_new_data(existing_data, extracted)
        save_user_data(updated_data)

    # Load user data for context
    user_data_str = ""
    user_data = load_user_data()
    if user_data:
        user_data_str = (
            "Here is the known user data:\n"
            + "\n".join([f"{k}: {v}" for k, v in user_data.items()])
            + "\n"
        )
    # Combine user data + user input
    engineered_input = f"{user_data_str}User says: {user_input}"
    response = process_text(engineered_input)
    print("RESPOND FOUND: ", response)
    text_to_speech(response)

    # Repeated conversation
    while True:
        user_input = continuous_recognition(
            vosk_model=vosk_model,
            timeout=7,
            max_speak_duration=25,
            silence_timeout=2.5
        )
        if not user_input:
            print("[Conversation] No speech within 7s => fallback to keyword detection.")
            return

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


def main():
    print("[Main] Loading Vosk model once...")
    vosk_model = Model("/home/pi/Testudo/vosk-model-small-en-us-0.15")
    print("[Main] Model loaded.")

    stop_listening_fn = init_background_listener(
        keyword="turtle",
        event_queue=keyword_detected_queue,
        vosk_model=vosk_model,        # pass the loaded model
        frames_per_buffer=2048
    )

    text_to_speech("System is active. Waiting for the keyword")
    print("[Main] System is active. Waiting for the keyword 'turtle'...")

    try:
        while True:
            keyword_detected = keyword_detected_queue.get()
            if keyword_detected:
                print("[Main] Keyword 'turtle' detected!")
                # Stop background listener to free the mic
                stop_listening_fn()
                # Run conversation
                conversation_flow(vosk_model)

                # Re-init background listener
                stop_listening_fn = init_background_listener(
                    keyword="turtle",
                    event_queue=keyword_detected_queue,
                    vosk_model=vosk_model,
                    frames_per_buffer=2048
                )
                # Ignore triggers for 1s after re-init
                set_ignore_until(time.time() + 1)

    except KeyboardInterrupt:
        print("[Main] Exiting on Ctrl+C.")


if __name__ == "__main__":
    main()
