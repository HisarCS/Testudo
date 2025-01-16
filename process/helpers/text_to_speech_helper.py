# helpers/text_to_speech_helper.py
import os
os.environ["ALSA_NO_WARN"] = "1"

from gtts import gTTS
from pydub import AudioSegment
import pyaudio
import wave
import threading
import time

tts_lock = threading.Lock()

def _play_audio_with_pyaudio(file_path, device_index=7):
    wf = wave.open(file_path, 'rb')
    p = pyaudio.PyAudio()

    stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True,
        output_device_index=device_index
    )

    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()

def text_to_speech(text, retries=3, device_index=7):
    with tts_lock:
        for attempt in range(retries):
            try:
                output_mp3 = "tts_output.mp3"
                output_wav = "tts_output.wav"

                tts = gTTS(text=text, lang='en')
                tts.save(output_mp3)

                sound = AudioSegment.from_mp3(output_mp3)
                sound.export(output_wav, format="wav")

                _play_audio_with_pyaudio(output_wav, device_index=device_index)

                os.remove(output_mp3)
                os.remove(output_wav)
                return

            except Exception as e:
                print(f"[TTS] Attempt {attempt + 1} failed: {e}")
                time.sleep(1)

        raise RuntimeError("[TTS] Failed after multiple retries.")
