import speech_recognition as sr
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

    # Device index for the output audio (adjust as needed)
    device_index = 7

    # Play the audio
    play_audio_with_pyaudio(output_wav, device_index)

def recognize_speech():
    # Initialize recognizer
    rec = sr.Recognizer()
    rec.energy_threshold = 400

    # Use the microphone as source for input (specify the microphone index)
    with sr.Microphone(8) as source:
        # Adjusting for ambient noise
        rec.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")
        
        try:
            # Capture audio
            audio = rec.listen(source, timeout=15)
            # Recognize speech
            text = rec.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Google Web Speech API could not understand the audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Web Speech API; {e}")
        return None

def respond_to_turtle():
    print("The word 'turtle' was detected!")

def listen_for_turtle():
    while True:
        spoken_text = recognize_speech()
        if spoken_text and 'turtle' in spoken_text.lower():
            respond_to_turtle()
            break

def main():
    # Step 1: Listen for 'turtle'
    print("Waiting to hear the word 'turtle'...")
    listen_for_turtle()

if __name__ == "__main__":
    main()
