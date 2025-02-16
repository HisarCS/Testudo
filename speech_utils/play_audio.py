import os
import pyaudio
import wave

def play_audio_with_pyaudio(file_path, device_name_substring):
    # Open the audio file
    wf = wave.open(file_path, 'rb')

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream with the appropriate settings
    stream = p.open(
        format = p.get_format_from_width(wf.getsampwidth()),
        channels = wf.getnchannels(),
        rate = wf.getframerate(),
        output = True,
        output_device_index = 7
    )
    print(wf.getnchannels())
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

def main():
    file_path = "/home/raspberry/Desktop/recorded_audio.wav"
    
    play_audio_with_pyaudio(file_path, "seeed-2mic-voicecard")

if __name__ == "__main__":
    main()
