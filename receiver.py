# PrivateVoice
# https://github.com/Duck1776/PrivateVoice
# receiver.py

# UPDATES
# Auto Audio Channels

import soundcard as sc
import numpy as np
from crypto import ChaCha20Cipher
import time
import logging
import collections

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AudioReceiver:
    def __init__(self, key):
        self.cipher = ChaCha20Cipher(key)
        self.vb_cable_input = sc.get_microphone('CABLE Output')  # VB-Cable Input
        self.real_speaker = sc.default_speaker()
        self.running = False
        self.chunk = 1024
        self.channels = 1
        self.rate = 44100
        self.buffer = collections.deque(maxlen=5)

    def start(self):
        self.running = True
        with self.vb_cable_input.recorder(samplerate=self.rate, channels=self.channels) as mic, \
            self.real_speaker.player(samplerate=self.rate, channels=self.channels) as output:
            while self.running:
                try:
                    data = mic.record(numframes=self.chunk)
                    if data is None or len(data) == 0:
                        logger.warning("Empty audio frame received, skipping")
                        continue
                    self.buffer.append(data)
                    if len(self.buffer) == 5:
                        averaged_data = np.mean(self.buffer, axis=0)
                        decrypted_data = self.cipher.decrypt(averaged_data.tobytes())
                        output.play(np.frombuffer(decrypted_data, dtype=np.float32).reshape(-1, self.channels))
                except Exception as e:
                    logger.error(f"Error during audio processing: {e}")
                    time.sleep(0.1)

    def stop(self):
        self.running = False