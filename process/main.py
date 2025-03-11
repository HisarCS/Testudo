# main.py

import os
import time
import requests
import queue

# Now we import from the updated speech_helper, which uses speech_recognition
from helpers.speech_helper import (
    init_background_listener,
    continuous_recognition,
    set_ignore_until
)

# TTS, user data, file utils, etc. remain the same
from helpers.text_to_speech_helper import text_to_speech
from helpers.user_data_extraction import extract_all_info
from helpers.user_data_manager import load_user_data, save_user_data, merge_new_data
from utils.file_utils import cleanup_audio_files

# Our audio device helper for picking the ReSpeaker mic
from helpers.audio_device_helper import get_input_device_index, get_output_device_index

keyword_detected_queue = queue.Queue()

def call_lm_studio(
    prompt: str,
    host: str = "10.0.90.140",
    port: int = 1234,
    model: str = "wizard-vicuna-13b-uncensored",
    max_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
    n: int = 1,
    stream: bool = False
) -> str:
    """
    Send 'prompt' to LM Studio's /v1/completions endpoint, parse JSON,
    and extract the text from the first choice.
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


def conversation_flow():
    """
    Same conversation flow, except now continuous_recognition uses Google STT.
    """
    text_to_speech("How can I help you?")

    user_input = continuous_recognition(
        mic_index=get_input_device_index(),
        timeout=7,
        max_speak_duration=25,
        silence_duration=3.0
    )
    if not user_input:
        print("[Conversation] No speech within 7s => fallback to keyword detection.")
        return []
    
    extracted = extract_all_info(user_input)
    print("EXTRACTED:", extracted)
    if extracted:
        existing_data = load_user_data()
        updated_data = merge_new_data(existing_data, extracted)
        save_user_data(updated_data)

    user_data = load_user_data()
    user_data_str = ""
    if user_data:
        user_data_str = (
            "Here is the known user data:\n"
            + "\n".join([f"{k}: {v}" for k, v in user_data.items()])
            + "\n"
        )

    # Combine user data + user's text
    engineered_input = f"{user_data_str}User says: {user_input}"
    response_text = process_text(engineered_input)
    print("[Conversation] Model response:", response_text)
    text_to_speech(response_text)

    # Continue until user doesn't speak for 7s
    while True:
        user_input = continuous_recognition(
            mic_index=get_input_device_index(),
            timeout=7,
            max_speak_duration=25,
            silence_duration=3.0
        )
        if not user_input:
            print("[Conversation] No speech within 7s => fallback to keyword detection.")
            return

        extracted = extract_all_info(user_input)
        if extracted:
            existing_data = load_user_data()
            updated_data = merge_new_data(existing_data, extracted)
            save_user_data(updated_data)

        user_data = load_user_data()
        user_data_str = ""
        if user_data:
            user_data_str = (
                "Here is some known user data:\n"
                + "\n".join([f"{k}: {v}" for k, v in user_data.items()])
                + "\n"
            )

        engineered_input = f"{user_data_str}User says: {user_input}"
        print("[Conversation] Input:", engineered_input)
        response_text = process_text(engineered_input)
        print("[Conversation] Output:", response_text)
        text_to_speech(response_text)


def main():
    print("[Main] Using Google STT (speech_recognition) with manual PyAudio. No Vosk model needed.")

    # Start background listener with the same device approach
    mic_idx = get_input_device_index()
    stop_listening_fn = init_background_listener(
        keyword="turtle",
        event_queue=keyword_detected_queue,
        mic_index=mic_idx
    )
    text_to_speech("System is active. Waiting for the keyword 'turtle'.")
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

                # After conversation, re-init the background listener
                stop_listening_fn = init_background_listener(
                    keyword="turtle",
                    event_queue=keyword_detected_queue,
                    mic_index=mic_idx
                )

                # Ignore triggers for ~1 second to avoid immediate re-trigger
                set_ignore_until(time.time() + 1)

    except KeyboardInterrupt:
        print("[Main] Exiting on Ctrl+C.")


if __name__ == "__main__":
    main()
