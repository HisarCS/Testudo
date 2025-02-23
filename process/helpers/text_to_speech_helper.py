# helpers/text_to_speech_helper.py
import os
from gtts import gTTS
from pydub import AudioSegment
import pyaudio
import wave
import threading
import time
from helpers.audio_device_helper import get_output_device_index

os.environ["ALSA_NO_WARN"] = "1"
tts_lock = threading.Lock()

def _play_audio_with_pyaudio(file_path, device_index):
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

def text_to_speech(text, retries=1, device_index=None):
    with tts_lock:
        if device_index is None:
            device_index = get_output_device_index()
        for attempt in range(retries):
            try:
                output_mp3 = "tts_output.mp3"
                output_wav = "tts_output.wav"
                tts = gTTS(text=text, lang='en')
                tts.save(output_mp3)
                sound = AudioSegment.from_mp3(output_mp3)
                sound = sound.set_frame_rate(16000)
                sound = sound + 20  # Increase volume by 20 dB
                sound.export(output_wav, format="wav")
                _play_audio_with_pyaudio(output_wav, device_index=device_index)
                os.remove(output_mp3)
                os.remove(output_wav)
                return
            except Exception as e:
                print(f"[TTS] Attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        raise RuntimeError("[TTS] Failed after multiple retries.")
