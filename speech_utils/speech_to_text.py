import speech_recognition as sr
import sounddevice

# Initialize recognizer
rec = sr.Recognizer()
rec.energy_threshold = 400 
 
# Function to capture audio and recognize speech
def recognize_speech():
    # Use the microphone as source for input (specify the microphone index)
    with sr.Microphone(8) as source:  
        # Adjusting for ambient noise
        rec.adjust_for_ambient_noise(source, duration=1)      
        print("Listening...")
        audio = rec.listen(source, timeout=15)
 
        try:
            text = rec.recognize_google(audio) 
            print(f"You said: {text}")
        except sr.UnknownValueError:
            print("Google Web Speech API could not understand the audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Web Speech API; {e}")

# Main function
if __name__ == "__main__":
    recognize_speech() 
