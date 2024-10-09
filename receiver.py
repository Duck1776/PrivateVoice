# PrivateVoice
# https://github.com/Duck1776/PrivateVoice
# reciever.py

# UPDATES
# Separated the code into sections on seperate files

import pyaudio
import numpy as np
from crypto import ChaCha20Cipher
import logging

class AudioReceiver:
    def __init__(self, key, input_device, output_device):
        self.cipher = ChaCha20Cipher(key)
        self.input_device = input_device
        self.output_device = output_device
        self.running = False
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100

    def audio_callback(self, in_data, frame_count, time_info, status):
        decrypted_data = self.cipher.decrypt(in_data)
        return (decrypted_data, pyaudio.paContinue)

    def start(self):
        self.running = True
        p = pyaudio.PyAudio()

        try:
            input_stream = p.open(format=self.format,
                                channels=self.channels,
                                rate=self.rate,
                                input=True,
                                input_device_index=self.input_device,
                                frames_per_buffer=self.chunk)

            output_stream = p.open(format=self.format,
                                channels=self.channels,
                                rate=self.rate,
                                output=True,
                                output_device_index=self.output_device,
                                frames_per_buffer=self.chunk)

            logging.info("Audio streams opened successfully")

            input_stream.start_stream()
            
            while self.running:
                data = input_stream.read(self.chunk)
                output_stream.write(data)

        except Exception as e:
            logging.error(f"Error in AudioReceiver: {str(e)}")
            raise

        finally:
            if 'input_stream' in locals():
                input_stream.stop_stream()
                input_stream.close()
            if 'output_stream' in locals():
                output_stream.stop_stream()
                output_stream.close()
            p.terminate()

    def stop(self):
        self.running = False