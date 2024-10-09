# PrivateVoice
# https://github.com/Duck1776/PrivateVoice
# crypto.py

# UPDATES
# Separated the code into sections on seperate files

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def generate_key():
    return os.urandom(32).hex()

class ChaCha20Cipher:
    def __init__(self, key):
        self.key = bytes.fromhex(key)

    def encrypt(self, data):
        nonce = os.urandom(16)
        algorithm = algorithms.ChaCha20(self.key, nonce)
        cipher = Cipher(algorithm, mode=None, backend=default_backend())
        encryptor = cipher.encryptor()
        return nonce + encryptor