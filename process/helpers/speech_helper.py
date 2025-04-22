# helpers/speech_helper.py
import os
os.environ["ALSA_NO_WARN"] = "1"

import time
import threading
import pyaudio
import speech_recognition as sr
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


def init_background_listener(keyword, event_queue, mic_index=None):
    """
    Initialize a background thread for *keyword detection* using Google STT
    via manual PyAudio streaming. We'll read ~3 seconds at a time (instead of 2),
    feed them to `recognize_google`, and if the recognized text contains <keyword>,
    we put True into event_queue.
    """
    global _stop_listening

    if mic_index is None:
        mic_index = get_input_device_index()
        
    print(mic_index)

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,  # same as old Vosk approach
        input=True,
        input_device_index=mic_index,
        frames_per_buffer=8000
    )
    stream.start_stream()

    r = sr.Recognizer()

    running = True

    def run_background():
        global _IGNORE_UNTIL

        chunk_duration = 2.0  # we read 2 seconds of audio data
        bytes_per_second = 16000 * 2  # 32k
        chunk_bytes = int(bytes_per_second * chunk_duration)  # ~96k bytes

        while running:
            current_time = time.time()
            if current_time < _IGNORE_UNTIL:
                # ignoring triggers => just read some audio to flush buffer
                stream.read(min(4000, chunk_bytes), exception_on_overflow=False)
                continue

            # Read a full 3-second chunk
            frames = []
            total_needed = chunk_bytes
            while total_needed > 0:
                block_size = min(4000, total_needed)
                data = stream.read(block_size, exception_on_overflow=False)
                frames.append(data)
                total_needed -= len(data)

            # Convert to sr.AudioData
            audio_data = sr.AudioData(b''.join(frames), 16000, 2)
            try:
                text = r.recognize_google(audio_data).lower()
                if text:
                    print(f"[Keyword Listener] Final recognized: {text}")
                    if keyword.lower() in text or "cancel" in text or "turn" in text or "turd" in text or "hurdle" in text or "purple" in text:
                        event_queue.put(True)
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[Keyword Listener] Google request error: {e}")
                pass

        # Cleanup
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
        thread.join()

    _stop_listening = stop_listening
    return _stop_listening


def continuous_recognition(
    mic_index=None,
    timeout=7.0,
    max_speak_duration=25.0,
    silence_duration=4.0
):
    """
    Blocks and listens for a single user utterance using Google STT
    via manual PyAudio chunking.

    Changes:
    - chunk_time increased to 2 seconds
    - silence_duration = 4 (so you won't get cut off after a short pause)
    - no phrase_time_limit

    Returns recognized text (str) or None if no speech detected.
    """
    print("[Speech] Starting continuous recognition with Google STT...")

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

    r = sr.Recognizer()
    recognized_segments = []

    start_time = time.time()
    speech_start_time = None
    last_speech_time = None

    # We'll decode every 3s worth of audio
    chunk_time = 3.0
    bytes_per_second = 16000 * 2  # 32k
    chunk_bytes = int(bytes_per_second * chunk_time)  # ~64k bytes

    buffer_frames = b''

    while True:
        # If user hasn't started speaking after `timeout` seconds, give up
        if speech_start_time is None and (time.time() - start_time) > timeout:
            print("[Speech] No speech detected within timeout.")
            break

        # If user started speaking and we've exceeded max_speak_duration, stop
        if speech_start_time is not None and (time.time() - speech_start_time) > max_speak_duration:
            print("[Speech] Max speaking duration exceeded.")
            break

        data = stream.read(min(4000, chunk_bytes), exception_on_overflow=False)
        if not data:
            continue

        buffer_frames += data
        # Once we have 2s worth of audio, send to Google
        if len(buffer_frames) >= chunk_bytes:
            audio_data = sr.AudioData(buffer_frames, 16000, 2)
            buffer_frames = b''

            try:
                text_chunk = r.recognize_google(audio_data)
                text_chunk = text_chunk.strip()
                if text_chunk:
                    recognized_segments.append(text_chunk)
                    if speech_start_time is None:
                        # The moment we get some recognized text, user has started speaking
                        speech_start_time = time.time()
                    last_speech_time = time.time()
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[Speech] Google request error: {e}")
                pass

        # If user started speaking and there's been `silence_duration` of no new text, finalize
        if speech_start_time is not None and last_speech_time is not None:
            if (time.time() - last_speech_time) >= silence_duration:
                print("[Speech] Detected silence, ending recognition.")
                break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    final_text = " ".join(recognized_segments).strip()
    if final_text:
        print("[Speech] Final recognized text:", final_text)
        return final_text
    else:
        return None