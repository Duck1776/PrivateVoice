# PrivateVoice v00.01
# https://github.com/Duck1776/PrivateVoice/tree/main

# UPDATES
# - v00.01 - Initial

import pyaudio
import threading
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox, QLineEdit, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal

CHUNK = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

# Generate a default 256-bit key
DEFAULT_KEY = os.urandom(32)

def derive_key(code):
    return SHA256.new(code.encode()).digest()

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

def receiver(key, stop_event, encrypted_input_id, decrypted_output_id):
    p = pyaudio.PyAudio()
    _, input_channels, _ = get_device_info(p, encrypted_input_id)
    _, _, output_channels = get_device_info(p, decrypted_output_id)
    
    input_stream = p.open(format=FORMAT, 
                          channels=input_channels,
                          rate=RATE, 
                          input=True, 
                          frames_per_buffer=CHUNK+48, 
                          input_device_index=encrypted_input_id)
    
    output_stream = p.open(format=FORMAT, 
                           channels=output_channels,
                           rate=RATE, 
                           output=True, 
                           frames_per_buffer=CHUNK, 
                           output_device_index=decrypted_output_id)

    print(f"Receiver started. Input channels: {input_channels}, Output channels: {output_channels}")
    try:
        while not stop_event.is_set():
            encrypted_chunk = input_stream.read(CHUNK + 48)
            if len(encrypted_chunk) == (CHUNK + 48) * input_channels:
                try:
                    decrypted_chunk = decrypt_audio(encrypted_chunk, key)
                    output_stream.write(decrypted_chunk)
                except Exception as e:
                    print(f"Decryption error: {e}")
    finally:
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()
    print("Receiver stopped.")

class EncryptionThread(QThread):
    error_occurred = pyqtSignal(str)

    def __init__(self, key, raw_mic_input_id, encrypted_output_id, encrypted_input_id, decrypted_output_id):
        super().__init__()
        self.key = key
        self.raw_mic_input_id = raw_mic_input_id
        self.encrypted_output_id = encrypted_output_id
        self.encrypted_input_id = encrypted_input_id
        self.decrypted_output_id = decrypted_output_id
        self.stop_event = threading.Event()

    def run(self):
        try:
            sender_thread = threading.Thread(target=sender, args=(self.key, self.stop_event, self.raw_mic_input_id, self.encrypted_output_id))
            receiver_thread = threading.Thread(target=receiver, args=(self.key, self.stop_event, self.encrypted_input_id, self.decrypted_output_id))

            sender_thread.start()
            receiver_thread.start()

            sender_thread.join()
            receiver_thread.join()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self.stop_event.set()

class AudioEncryptorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrivateVoice v00.01")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.add_key_input(layout)
        self.add_device_selectors(layout)
        self.add_control_buttons(layout)

        self.encryption_thread = None
        self.populate_device_lists()

    def add_key_input(self, layout):
        key_layout = QHBoxLayout()
        key_label = QLabel("Key:")
        self.key_input = QLineEdit()
        self.key_input.setText(DEFAULT_KEY.hex())  # Set default key
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        layout.addLayout(key_layout)

    def add_device_selectors(self, layout):
        self.raw_mic_input = QComboBox()
        self.encrypted_output = QComboBox()
        self.encrypted_input = QComboBox()
        self.decrypted_output = QComboBox()

        layout.addWidget(QLabel("Raw Microphone Input:"))
        layout.addWidget(self.raw_mic_input)
        layout.addWidget(QLabel("Encrypted Audio Output:"))
        layout.addWidget(self.encrypted_output)
        layout.addWidget(QLabel("Encrypted Audio Input:"))
        layout.addWidget(self.encrypted_input)
        layout.addWidget(QLabel("Decrypted Audio Output:"))
        layout.addWidget(self.decrypted_output)

    def add_control_buttons(self, layout):
        self.start_button = QPushButton("Start Encryption/Decryption")
        self.stop_button = QPushButton("Stop Encryption/Decryption")
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.start_button.clicked.connect(self.start_encryption)
        self.stop_button.clicked.connect(self.stop_encryption)

    def populate_device_lists(self):
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            device_name = device_info['name']
            if device_info['maxInputChannels'] > 0:
                self.raw_mic_input.addItem(f"{i}: {device_name}")
                self.encrypted_input.addItem(f"{i}: {device_name}")
            if device_info['maxOutputChannels'] > 0:
                self.encrypted_output.addItem(f"{i}: {device_name}")
                self.decrypted_output.addItem(f"{i}: {device_name}")
        p.terminate()

    def start_encryption(self):
        if self.encryption_thread and self.encryption_thread.isRunning():
            QMessageBox.warning(self, "Warning", "Encryption/Decryption is already running.")
            return

        key = bytes.fromhex(self.key_input.text())
        raw_mic_input_id = int(self.raw_mic_input.currentText().split(':')[0])
        encrypted_output_id = int(self.encrypted_output.currentText().split(':')[0])
        encrypted_input_id = int(self.encrypted_input.currentText().split(':')[0])
        decrypted_output_id = int(self.decrypted_output.currentText().split(':')[0])

        self.encryption_thread = EncryptionThread(key, raw_mic_input_id, encrypted_output_id, encrypted_input_id, decrypted_output_id)
        self.encryption_thread.error_occurred.connect(self.show_error)
        self.encryption_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_encryption(self):
        if self.encryption_thread and self.encryption_thread.isRunning():
            self.encryption_thread.stop()
            self.encryption_thread.wait()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        else:
            QMessageBox.warning(self, "Warning", "Encryption/Decryption is not running.")

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

def main():
    app = QApplication(sys.argv)
    window = AudioEncryptorUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()