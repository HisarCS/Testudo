import os
os.environ["ALSA_NO_WARN"] = "1"

import time
import threading
import json
import pyaudio

from vosk import KaldiRecognizer
from helpers.audio_device_helper import get_input_device_index

_stop_listening = None  # We'll store a function to stop background listening
_IGNORE_UNTIL = 0.0


def set_ignore_until(t: float):
    """
    Sets a timestamp until which we will ignore recognized text
    from the background listener.
    """
    global _IGNORE_UNTIL
    _IGNORE_UNTIL = t


def init_background_listener(
    keyword,
    event_queue,
    vosk_model,
    mic_index=None,
    frames_per_buffer=2048
):
    """
    Initialize a background thread for keyword detection using Vosk.
    We reuse an already-loaded `vosk_model` (Model object), reducing overhead.
    Whenever the keyword is detected, we put True into event_queue.
    Returns a stop_listening() function that terminates the background thread.
    """
    global _stop_listening

    recognizer = KaldiRecognizer(vosk_model, 16000)

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
        frames_per_buffer=frames_per_buffer
    )
    stream.start_stream()

    running = True

    def run_background():
        global _IGNORE_UNTIL
        while running:
            # Read a smaller chunk for lower latency
            data = stream.read(frames_per_buffer, exception_on_overflow=False)
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

                if text:
                    print(f"[Keyword Listener] Final recognized: {text}")
                    # Check if "turtle" or synonyms appear
                    if (
                        keyword.lower() in text
                        or "hurtful" in text
                        or "hurt so " in text
                        or "tirtle" in text
                        or "tortle" in text
                        or "tartle" in text
                        or "hurdle" in text
                        or "hurtle" in text
                        or "murtle" in text
                        or "durtle" in text
                        or "hurtel" in text
                        or "nurtle" in text
                        or "tarte" in text
                        or "thirty" in text
                        or "tarthole" in text
                    ):
                        event_queue.put(True)
                # Partial results are ignored for keyword detection
            else:
                # Partial result => ignore for now
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
    vosk_model,
    mic_index=None,
    timeout=2.0,
    max_speak_duration=16,
    silence_timeout=2.0,
    frames_per_buffer=2048
):
    """
    Blocks and listens for a single user utterance using a reused Vosk model.
    - `timeout`: how many seconds to wait for the user to start speaking
    - `max_speak_duration`: max time (in seconds) to capture speech
    - `silence_timeout`: after the user starts speaking, if they go silent for
      this many seconds, we finalize recognition
    - `frames_per_buffer`: smaller buffer => lower latency
    Returns the recognized text (str) or None if nothing recognized.
    """
    recognizer = KaldiRecognizer(vosk_model, 16000)

    if mic_index is None:
        mic_index = get_input_device_index()

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=mic_index,
        frames_per_buffer=frames_per_buffer
    )
    stream.start_stream()

    print("[Speech] Listening for your response...")

    start_time = time.time()
    speech_start_time = None
    recognized_text = []

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

        data = stream.read(frames_per_buffer, exception_on_overflow=False)
        if len(data) == 0:
            continue

        if recognizer.AcceptWaveform(data):
            # Final result
            result_json = recognizer.Result()
            result_dict = json.loads(result_json)
            text = result_dict.get("text", "").strip()

            # Remove the old "huh" check for optimization (5)
            if text:
                recognized_text.append(text)
                last_speech_time = time.time()
                if speech_start_time is None:
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
