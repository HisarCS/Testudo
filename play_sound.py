import os
import pyaudio
import wave

def find_device_index(target_name):
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if target_name in dev_info['name']:
            return i
    return None

def play_audio_with_pyaudio(file_path, device_name):
    # Open the audio file
    wf = wave.open(file_path, 'rb')

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Find the device index
    device_index = find_device_index(device_name)
    if device_index is None:
        raise ValueError(f"Audio device '{device_name}' not found.")

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

def play_audio_with_aplay(file_path, device_name):
    command = f"aplay -D {device_name} {file_path}"
    os.system(command)

# Main function to play audio
def main():
    file_path = "/home/raspberry/Desktop/a.wav"
    device_name = "seeed-2mic-voicecard"

    try:
        # Attempt to play using PyAudio
        play_audio_with_pyaudio(file_path, device_name)
    except Exception as e:
        print(f"PyAudio failed: {e}")
        print("Falling back to aplay...")
        # Use aplay as a fallback
        play_audio_with_aplay(file_path, "plughw:3,0")

if __name__ == "__main__":
    main()

