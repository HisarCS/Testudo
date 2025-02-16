import pyaudio
import threading

def audio_echo(input_device_index, output_device_index, sample_rate=16000, chunk_size=1024, channels=1):
    """
    Real-time audio echo: capture input from a microphone and play it back on the output device.

    :param input_device_index: Index of the input device (microphone).
    :param output_device_index: Index of the output device (speaker/headphones).
    :param sample_rate: Sample rate for audio streaming.
    :param chunk_size: Size of audio chunks.
    :param channels: Number of audio channels (e.g., 1 for mono, 2 for stereo).
    """
    p = pyaudio.PyAudio()

    # Open input and output streams
    input_stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk_size,
        input_device_index=input_device_index
    )

    output_stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        output=True,
        frames_per_buffer=chunk_size,
        output_device_index=output_device_index
    )

    def stream_audio():
        print("Starting audio echo. Press Ctrl+C to stop.")
        try:
            while True:
                data = input_stream.read(chunk_size, exception_on_overflow=False)
                output_stream.write(data)
        except KeyboardInterrupt:
            print("Stopping audio echo.")
        finally:
            input_stream.stop_stream()
            input_stream.close()
            output_stream.stop_stream()
            output_stream.close()
            p.terminate()

    thread = threading.Thread(target=stream_audio)
    thread.start()

    thread.join()

def list_devices():
    """List all audio devices."""
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    print("=== PyAudio Devices ===")
    for i in range(device_count):
        dev_info = p.get_device_info_by_index(i)
        print(f"Index {i}: {dev_info['name']}")
    p.terminate()

def main():
    audio_echo(
        input_device_index=8,
        output_device_index=7,
        sample_rate=16000,
        chunk_size=1024,
        channels=1
    )

if __name__ == "__main__":
    main()

