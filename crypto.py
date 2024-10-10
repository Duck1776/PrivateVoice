# PrivateVoice
# https://github.com/Duck1776/PrivateVoice
# crypto.py

# UPDATES
# Auto Audio Channels

import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def generate_key():
    return os.urandom(32).hex()

class ChaCha20Cipher:
    def __init__(self, key):
        self.key = bytes.fromhex(key)
        self.nonce_size = 16  # in bytes

    def encrypt(self, data):
        nonce = os.urandom(self.nonce_size)
        cipher = Cipher(algorithms.ChaCha20(self.key, nonce), mode=None, backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = nonce + encryptor.update(data)
        return encrypted_data

    def decrypt(self, data):
        nonce = data[:self.nonce_size]
        ciphertext = data[self.nonce_size:]
        cipher = Cipher(algorithms.ChaCha20(self.key, nonce), mode=None, backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext)
        return decrypted_data