# PrivateVoice
# https://github.com/Duck1776/PrivateVoice
# sender.py

# UPDATES
# Separated the code into sections on seperate files

import pyaudio
from crypto_utils import encrypt_audio

CHUNK = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

def get_device_info(p, device_id):
    device_info = p.get_device_info_by_index(device_id)
    max_input_channels = device_info['maxInputChannels']
    max_output_channels = device_info['maxOutputChannels']
    return device_info, max_input_channels, max_output_channels

def sender(key, stop_event, raw_mic_input_id, encrypted_output_id):
    p = pyaudio.PyAudio()
    _, input_channels, _ = get_device_info(p, raw_mic_input_id)
    _, _, output_channels = get_device_info(p, encrypted_output_id)
    
    input_stream = p.open(format=FORMAT, 
                          channels=input_channels,
                          rate=RATE, 
                          input=True, 
                          frames_per_buffer=CHUNK, 
                          input_device_index=raw_mic_input_id)
    
    output_stream = p.open(format=FORMAT, 
                           channels=output_channels,
                           rate=RATE, 
                           output=True, 
                           frames_per_buffer=CHUNK, 
                           output_device_index=encrypted_output_id)

    print(f"Sender started. Input channels: {input_channels}, Output channels: {output_channels}")
    try:
        while not stop_event.is_set():
            audio_chunk = input_stream.read(CHUNK)
            encrypted_chunk = encrypt_audio(audio_chunk, key)
            output_stream.write(encrypted_chunk)
    finally:
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()
    print("Sender stopped.")