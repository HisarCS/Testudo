# helpers/speech_helper.py
import os
os.environ["ALSA_NO_WARN"] = "1"

import speech_recognition as sr
import threading
import time

_keyword_listener_active = True
_stop_listening = None  # The function returned by listen_in_background

# We'll store a global "ignore until" timestamp
_IGNORE_UNTIL = 0.0

def set_ignore_until(t: float):
    """
    Sets a timestamp until which we will ignore recognized text
    from the background listener.
    """
    global _IGNORE_UNTIL
    _IGNORE_UNTIL = t

def _keyword_callback(recognizer, audio, keyword, event_queue):
    """
    This callback runs whenever speech_recognition picks up audio in the background.
    We only process if _keyword_listener_active is True
    and if the current time is >= _IGNORE_UNTIL.
    """
    global _keyword_listener_active, _IGNORE_UNTIL

    if not _keyword_listener_active:
        return  # Do nothing if temporarily "inactive"

    # If we're within the ignore window, skip any recognized text
    current_time = time.time()
    if current_time < _IGNORE_UNTIL:
        # We are in a "cooldown" period, so ignore
        return

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
    recognizer.dynamic_energy_threshold = False
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.energy_threshold = 400  # Baseline

    mic = sr.Microphone(device_index=mic_index)
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    _stop_listening = recognizer.listen_in_background(
        mic,
        lambda r, a: _keyword_callback(r, a, keyword, event_queue)
    )

    listener_thread = threading.Thread(target=lambda: None)
    listener_thread.start()

    return listener_thread

def set_keyword_listener_active(active: bool):
    """
    Toggle whether the background listener actually processes recognized text.
    If set to False, we ignore transcripts in the callback.
    If set to True, no special flush is strictly needed because we
    also rely on the 'ignore until' approach.
    """
    global _keyword_listener_active
    _keyword_listener_active = active

    if active:
        # Optionally, do a short sleep to let the mic buffer pass,
        # but the main fix is ignoring recognized text for a short time.
        time.sleep(0.5)


def continuous_recognition(mic_index=8, timeout=5, max_speak_duration=25):
    """
    A single-pass blocking recognition for the user's query.
    We'll rely on silence detection but also use a fallback max_speak_duration.
    """
    recognizer = sr.Recognizer()

    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    # Lower pause_threshold to reduce post-speech delay
    recognizer.pause_threshold = 1.5
    recognizer.phrase_threshold = 0.2
    recognizer.non_speaking_duration = 0.6

    mic = sr.Microphone(device_index=mic_index)

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[Speech] Listening for your response (silence detection + fallback)...")

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,            # wait up to 'timeout' sec to start
                phrase_time_limit=max_speak_duration
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
