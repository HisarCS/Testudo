# helpers/speech_helper.py
import os
os.environ["ALSA_NO_WARN"] = "1"

import speech_recognition as sr
import threading
import time

# For the single background thread approach:
_keyword_listener_active = True
_stop_listening = None  # The function returned by listen_in_background

def _keyword_callback(recognizer, audio, keyword, event_queue):
    """
    This callback runs whenever speech_recognition picks up audio in the background.
    We only process if _keyword_listener_active is True.
    """
    global _keyword_listener_active
    if not _keyword_listener_active:
        return  # Do nothing if temporarily "inactive"

    try:
        transcript = recognizer.recognize_google(audio)
        transcript_lower = transcript.lower()
        print(f"[Keyword Listener] Heard: {transcript_lower}")

        if keyword.lower() in transcript_lower:
            event_queue.put(True)  # signal main loop

    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"[Keyword Listener] API error: {e}")

def init_background_listener(keyword, event_queue, mic_index=8):
    """
    Initialize a single background listener that runs forever.
    We do NOT stop/restart it to avoid segfaults.
    """
    global _stop_listening

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300

    # If mic_index is None, use default microphone
    mic = sr.Microphone(device_index=mic_index)
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    # Start listening in the background
    _stop_listening = recognizer.listen_in_background(
        mic,
        lambda r, a: _keyword_callback(r, a, keyword, event_queue)
    )

    # Return a dummy thread handle (the library internally manages the real thread)
    # We won't typically call join() on it, to avoid segfault on repeated teardown.
    listener_thread = threading.Thread(target=lambda: None)
    listener_thread.start()

    return listener_thread

def set_keyword_listener_active(active: bool):
    """
    Toggle whether the background listener actually processes recognized text.
    If set to False, we ignore transcripts in the callback.
    """
    global _keyword_listener_active
    _keyword_listener_active = active

def continuous_recognition(mic_index=8, timeout=5, phrase_time_limit=10):
    """
    A single-pass blocking recognition for the user's query.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    mic = sr.Microphone(device_index=mic_index)

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[Speech] Listening for your response...")
        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )
            print("[Speech] Processing your speech...")
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            print("[Speech] No speech detected within timeout.")
        except sr.UnknownValueError:
            print("[Speech] Could not understand you.")
        except sr.RequestError as e:
            print(f"[Speech] Recognition service error: {e}")

    return None
