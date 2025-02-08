# utils/file_utils.py
import os

def cleanup_audio_files():
    """
    An optional function to remove any stray audio files you
    might have created but didn't remove.
    """
    for filename in os.listdir():
        if filename.endswith(".mp3") or filename.endswith(".wav"):
            try:
                os.remove(filename)
            except OSError:
                pass
