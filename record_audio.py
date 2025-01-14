import os

def record_audio(output_path, device_name, duration=5, sample_rate=16000, channels=1, format="S16_LE"):
    """
    Record audio using arecord and save it to the specified output path.

    Args:
        output_path (str): Path to save the recorded file.
        device_name (str): ALSA device name for recording.
        duration (int): Duration of the recording in seconds.
        sample_rate (int): Sampling rate in Hz.
        channels (int): Number of audio channels (1 for mono, 2 for stereo).
        format (str): Audio format (e.g., S16_LE for 16-bit little-endian).
    """
    command = (
        f"arecord -D {device_name} -r {sample_rate} -c {channels} -f {format} "
        f"-d {duration} {output_path}"
    )
    print(f"Recording audio for {duration} seconds...")
    os.system(command)
    print(f"Audio saved to: {output_path}")

# Main function
def main():
    output_path = "/home/raspberry/Desktop/recorded_audio.wav"  # Path to save the recording
    device_name = "plughw:3,0"  # ReSpeaker device (adjust as per `aplay -l`)
    duration = 5  # Recording duration in seconds

    try:
        record_audio(output_path, device_name, duration=duration)
    except Exception as e:
        print(f"Error during recording: {e}")

if __name__ == "__main__":
    main()
