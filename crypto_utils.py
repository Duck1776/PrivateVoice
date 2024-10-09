# PrivateVoice
# https://github.com/Duck1776/PrivateVoice
# crypto_utils.py

# UPDATES
# Separated the code into sections on seperate files

from Crypto.Cipher import AES

def encrypt_audio(audio_chunk, key):
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(audio_chunk)
    return nonce + tag + ciphertext

def decrypt_audio(encrypted_chunk, key):
    nonce = encrypted_chunk[:16]
    tag = encrypted_chunk[16:32]
    ciphertext = encrypted_chunk[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)