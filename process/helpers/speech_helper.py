# helpers/speech_helper.py
import os
os.environ["ALSA_NO_WARN"] = "1"

import time
import threading
import json
import pyaudio
from helpers.audio_device_helper import get_input_device_index
from vosk import Model, KaldiRecognizer

_stop_listening = None  # We'll store a function to stop background listening
_IGNORE_UNTIL = 0.0

def set_ignore_until(t: float):
    """
    Sets a timestamp until which we will ignore recognized text
    from the background listener.
    """
    global _IGNORE_UNTIL
    _IGNORE_UNTIL = t


def init_background_listener(keyword, event_queue, mic_index=None, model_path="/path/to/vosk-model"):
    """
    Initialize a background thread for keyword detection using Vosk.
    Whenever the keyword is detected, we put True into event_queue.
    Returns a stop_listening() function that terminates the background thread.
    """
    global _stop_listening

    # Load Vosk model once here
    print("[Keyword Listener] Loading Vosk model for keyword detection...")
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    print("[Keyword Listener] Model loaded.")
    
    if mic_index is None:
        mic_index = get_input_device_index()

    # Initialize PyAudio for capturing microphone input
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=mic_index,
        frames_per_buffer=8000
    )
    stream.start_stream()

    running = True

    def run_background():
        global _IGNORE_UNTIL
        while running:
            data = stream.read(4000, exception_on_overflow=False)
            if len(data) == 0:
                continue

            current_time = time.time()
            if current_time < _IGNORE_UNTIL:
                continue

            if recognizer.AcceptWaveform(data):
                # Final result
                res_json = recognizer.Result()
                res_dict = json.loads(res_json)
                text = res_dict.get("text", "").strip().lower()
                if text == "huh":
                    text = ""

                if text:
                    print(f"[Keyword Listener] Final recognized: {text}")
                    # Only check final recognized text for "turtle"
                    if keyword.lower() in text or "tirtle" in text or "tortle" in text or "tartle" in text or "hurdle" in text or "hurtle" in text or "murtle" in text or "durtle" in text or "hurtel" in text or "nurtle" in text or "tarte" in text or "thirty" in text or "tarthole" in text:
                        event_queue.put(True)
            else:
                # partial result => ignore for keyword detection
                pass

        # Clean up resources
        print("[Keyword Listener] Background thread stopping...")
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("[Keyword Listener] Closed PyAudio stream.")

    thread = threading.Thread(target=run_background, daemon=True)
    thread.start()

    def stop_listening():
        nonlocal running
        running = False
        # Wait for the thread to finish
        thread.join()

    _stop_listening = stop_listening
    return _stop_listening


def continuous_recognition(
        mic_index=None,
        timeout=2.0,
        max_speak_duration=16,
        model_path="/home/pi/Testudo/vosk-model-small-en-us-0.15"):
    """
    Blocks and listens for a single user utterance using Vosk-based STT.
    - `timeout`: How many seconds to wait for the user to start speaking
    - `max_speak_duration`: Max time (in seconds) to capture speech
    - `model_path`: Path to your Vosk STT model
    Returns the recognized text (str) or None if nothing recognized.
    """
    print("[Speech] Loading Vosk model for continuous recognition...")
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    print("[Speech] Model loaded.")
    
    if mic_index is None:
        mic_index = get_input_device_index()

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=mic_index,
        frames_per_buffer=8000
    )
    stream.start_stream()

    print("[Speech] Listening for your response...")

    start_time = time.time()
    speech_start_time = None
    recognized_text = []

    silence_timeout = 2.0
    last_speech_time = None

    while True:
        # If user hasn't started speaking after `timeout` sec, give up
        if speech_start_time is None and (time.time() - start_time) > timeout:
            print("[Speech] No speech detected within timeout.")
            break

        # If user started speaking and we've exceeded max_speak_duration, stop
        if speech_start_time is not None and (time.time() - speech_start_time) > max_speak_duration:
            print("[Speech] Max speaking duration exceeded.")
            break

        data = stream.read(4000, exception_on_overflow=False)
        if len(data) == 0:
            continue

        if recognizer.AcceptWaveform(data):
            # Final result
            result_json = recognizer.Result()
            result_dict = json.loads(result_json)
            text = result_dict.get("text", "").strip()
            if text == "huh":
                    text = ""
            if text:
                recognized_text.append(text)
                last_speech_time = time.time()
                if speech_start_time is None:
                    # The moment we get some final text, user has started speaking
                    speech_start_time = time.time()
        else:
            # Partial result
            partial_json = recognizer.PartialResult()
            partial_dict = json.loads(partial_json)
            partial_text = partial_dict.get("partial", "").strip()
            if partial_text:
                last_speech_time = time.time()
                if speech_start_time is None:
                    speech_start_time = time.time()

        # If we've started speech and haven't heard anything for `silence_timeout`, end
        if speech_start_time is not None and last_speech_time is not None:
            if (time.time() - last_speech_time) > silence_timeout:
                print("[Speech] Silence detected, ending recognition.")
                break

    # Cleanup
    stream.stop_stream()
    stream.close()
    audio.terminate()

    final_text = " ".join(recognized_text).strip()
    if final_text:
        print("[Speech] Final recognized text:", final_text)
        return final_text
    else:
        return None
