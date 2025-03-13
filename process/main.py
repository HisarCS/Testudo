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
    user_input: str,
    user_data_str: str = "",
    host: str = "10.0.90.140",
    port: int = 1234,
    model: str = "wizard-vicuna-13b-uncensored"
) -> str:
    """
    Send a ChatML-style prompt to LM Studio's /v1/completions endpoint.
    """
    # Your system prompt from the inference preset:
    system_prompt = (
        "You are TESTUDO, an affordable, open-source, AI-integrated quadruped robotic companion. "
        "You are inspired by a tortoise in design and you are powered by an AI-integrated low-cost microcontroller.\n\n"
        "Students can then modify and personalize their version of you to fit their needs while continuously "
        "improving through the iteration process.\n\n"
        "Your modification system relies on open-source programs, designs, and electronic frameworks. "
        "You adjust their development path to align with individual strengths. You do this by analyzing user data "
        "collected from verbal interactions.\n\n"
        "The inputs are given to you from your user. The user is a human. When the user asks something about you, "
        "answer from the text above but when the user asks something about itself accept that the user is a human "
        "speaking with Testudo.\n\n"
        "Your Identity: You are Testudo.\n"
        "User Identity: The user is a human.\n\n"
        "Role Clarity:\n"
        " - If the user asks “Who am I?” or “What am I”, you must remind them they are a human.\n"
        " - If asked “Who are you?”, you must identify yourself as Testudo, the AI companion.\n"
        " - Do not claim that the user is Testudo.\n\n"
        "Style: Provide accurate information, maintain a helpful and empathetic tone.\n"
        "Make sure that you don't tell what you are to the user all the time, only tell the user that you are testudo "
        "when the user asks about you or it.\n\n"
        "When the user asks a question about itself, use the user_data which is collected by previous conversations "
        "that is provided in the user's prompt. If the user asks a question that can be found in the user data, "
        "answer that question using only the values inside of user data. Please answer the user's question only "
        "with the answer. Don't say anything else.\n\n"
        "When responding to the user, respond as if you only give what you want to say. Don't give output that starts "
        "with 'Answer: '. Also don't respond with 'User says' ever. What you give as output is read out loud by "
        "Testudo to the user so make sure to speak as if you are in a conversation with the user."
    )

    # Construct a ChatML-style prompt
    # We’ll include user_data_str before the user’s raw text (if you want the model to see user data).
    chatml_prompt = (
        f"<|system|>\n{system_prompt}\n\n"  # system instructions
        f"<|user|>\n"                       # user role
        f"{user_data_str}"                 # known user data (optional chunk)
        f"{user_input}\n"                  # actual user text
        "<|assistant|>\n"                  # assistant role
    )

    # Prepare the request payload with the desired parameters
    url = f"http://{host}:{port}/v1/completions"
    payload = {
        "model": model,
        "prompt": chatml_prompt,
        # match your desired inference settings:
        "temperature": 0.8,
        "top_p": 0.95,
        "max_tokens": 150,
        # some versions of LM Studio may use "typical_p" for the min_p style:
        "min_p": 0.05,
        # "stream": False if you don't want streaming
        "stream": False
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


def process_text(input_text: str, user_data_str: str = "") -> str:
    """
    Simple wrapper to call LM Studio with user input + user data string.
    """
    return call_lm_studio(
        user_input=input_text,
        user_data_str=user_data_str
    )


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
    response_text = process_text(user_input, user_data_str)
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
        print("[Conversation] Input:", user_input, user_data_str)
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
