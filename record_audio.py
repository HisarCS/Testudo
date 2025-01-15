import pyaudio
import wave
import time

def record_audio_with_pyaudio(output_path,
                              device_index,
                              duration=5,
                              sample_rate=16000,
                              channels=1):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Configure the input stream
    # paInt16 => 16-bit samples
    # frames_per_buffer (chunk size) can be adjusted if desired
    chunk = 1024
    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk,
        input_device_index=device_index
    )

    print(f"Recording audio from device index={device_index} for {duration} seconds...")
    print("Press Ctrl+C to stop early (if running interactively).")

    frames = []
    start_time = time.time()

    # Capture data until the specified duration is reached
    while (time.time() - start_time) < duration:
        data = stream.read(chunk, exception_on_overflow=False)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Write the recorded frames to a WAV file
    wf = wave.open(output_path, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(2)  # 16-bit => 2 bytes per sample
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"Audio saved to: {output_path}")

def main():
    """
    Example usage: record 5 seconds of audio at 16 kHz, mono,
    from PyAudio device index 3 (adjust index to match your system).
    """
    output_path = "/home/raspberry/Desktop/recorded_audio.wav"
    duration = 5  # 5 seconds
    sample_rate = 16000
    channels = 1

    # Adjust this device_index to match your actual input device in PyAudio
    # e.g., if you want to replicate "plughw:3,0" from arecord, find which
    # PyAudio index corresponds to that device.
    device_index = 8


    try:
        record_audio_with_pyaudio(
            output_path=output_path,
            device_index=device_index,
            duration=duration,
            sample_rate=sample_rate,
            channels=channels
        )
    except Exception as e:
        print(f"Error during recording: {e}")


if __name__ == "__main__":
    main()
