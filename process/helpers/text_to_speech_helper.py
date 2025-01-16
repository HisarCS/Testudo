from gtts import gTTS
from pydub import AudioSegment
import pyaudio
import wave
import os

def play_audio_with_pyaudio(file_path, device_index=7):
    """Plays a WAV audio file using PyAudio."""
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

def text_to_speech(text):
    """Converts text to speech and plays the audio."""
    output_mp3 = "output.mp3"
    output_wav = "output.wav"

    tts = gTTS(text=text, lang='en')
    tts.save(output_mp3)

    sound = AudioSegment.from_mp3(output_mp3)
    sound.export(output_wav, format="wav")

    play_audio_with_pyaudio(output_wav)