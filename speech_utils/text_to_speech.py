import os
from gtts import gTTS
from pydub import AudioSegment
import pyaudio
import wave

def play_audio_with_pyaudio(file_path, device_index):
    # Open the audio file
    wf = wave.open(file_path, 'rb')

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream with the appropriate settings
    stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True,
        output_device_index=device_index
    )

    # Read and play the audio file in chunks
    chunk_size = 1024
    data = wf.readframes(chunk_size)
    while data:
        stream.write(data)
        data = wf.readframes(chunk_size)

    # Clean up
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()

def text_to_speech_with_device(text):
    # Generate the TTS audio using gTTS
    output_mp3 = "output.mp3"
    tts = gTTS(text=text, lang='en')
    tts.save(output_mp3)

    # Convert MP3 to WAV
    output_wav = "output.wav"
    sound = AudioSegment.from_mp3(output_mp3)
    sound.export(output_wav, format="wav")

    # Device index for the ReSpeaker
    device_index = 7

    # Play the audio
    play_audio_with_pyaudio(output_wav, device_index)

def main():
    text = input("Enter the text to speak: ")
    text_to_speech_with_device(text)

if __name__ == "__main__":
    main()
