# helpers/speech_helper.py
import os
os.environ["ALSA_NO_WARN"] = "1"

import speech_recognition as sr
import time

_stop_listening = None  # function pointer returned by listen_in_background
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
    We only process if current time >= _IGNORE_UNTIL.
    """
    global _IGNORE_UNTIL

    current_time = time.time()
    if current_time < _IGNORE_UNTIL:
        # We are in a "cooldown" period, so ignore
        return

    try:
        transcript = recognizer.recognize_google(audio)
        transcript_lower = transcript.lower()
        print(f"[Keyword Listener] Heard: {transcript_lower}")

        if keyword.lower() in transcript_lower:
            # Put True on the event_queue to signal the main loop
            event_queue.put(True)

    except sr.UnknownValueError:
        pass  # ignore
    except sr.RequestError as e:
        print(f"[Keyword Listener] API error: {e}")

def init_background_listener(keyword, event_queue, mic_index=2):
    """
    Initialize and start the background listener thread.
    Returns the stop_listening function so you can stop the background thread later.
    """
    global _stop_listening

    # Print microphone list for debugging
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        print(i, name)

    recognizer = sr.Recognizer()

    # A static threshold helps avoid over-adjusting for silent environments
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = 400  # Adjust as needed

    # Must open the microphone in a 'with' block once to calibrate
    mic = sr.Microphone(device_index=mic_index, sample_rate=16000, chunk_size=1024)
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    # Start background listening
    _stop_listening = recognizer.listen_in_background(
        mic,
        lambda r, a: _keyword_callback(r, a, keyword, event_queue)
    )

    # Return the stop_listening function to the caller
    return _stop_listening

def continuous_recognition(mic_index=2, timeout=5, max_speak_duration=25):
    """
    A single-pass blocking recognition for the user's query.
    Uses a separate mic stream from the background listener (which must be stopped).
    """
    recognizer = sr.Recognizer()

    # Let the recognizer dynamically adjust energy threshold
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.pause_threshold = 1.5
    recognizer.phrase_threshold = 0.2
    recognizer.non_speaking_duration = 0.6

    with sr.Microphone(device_index=mic_index) as source:
        # Adjust for ambient noise inside a 'with' block
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[Speech] Listening for your response (silence detection + fallback)...")

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,            # wait up to 'timeout' sec to start hearing
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
