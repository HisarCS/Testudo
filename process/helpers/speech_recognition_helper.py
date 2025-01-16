import speech_recognition as sr

def recognize_speech():
    """Captures and recognizes speech from the microphone."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 400

    with sr.Microphone(8) as source:  # Replace with the appropriate microphone index
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening for speech...")

        try:
            audio = recognizer.listen(source, timeout=15)
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("Could not understand the audio.")
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
        return None

def listen_for_keyword(keyword):
    """Listens for a specific keyword in the user's speech."""
    while True:
        spoken_text = recognize_speech()
        if spoken_text and keyword.lower() in spoken_text.lower():
            return True