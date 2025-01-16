import os

def cleanup_audio_files():
    """Deletes temporary audio files to free up space."""
    for file in ["output.mp3", "output.wav"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Deleted temporary file: {file}")