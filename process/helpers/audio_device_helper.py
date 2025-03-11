# helpers/audio_device_helper.py

import pyaudio

def get_input_device_index(device_name="seeed-2mic-voicecard"):
    p = pyaudio.PyAudio()
    index = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if device_name.lower() in info["name"].lower() and info.get("maxInputChannels", 0) > 0:
            index = i
            break
    p.terminate()
    if index is None:
        raise RuntimeError(f"Input device '{device_name}' not found.")
    return index

def get_output_device_index(device_name="seeed-2mic-voicecard"):
    p = pyaudio.PyAudio()
    index = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if device_name.lower() in info["name"].lower() and info.get("maxOutputChannels", 0) > 0:
            index = i
            break
    p.terminate()
    if index is None:
        raise RuntimeError(f"Output device '{device_name}' not found.")
    return index
