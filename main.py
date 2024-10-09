# PrivateVoice
# https://github.com/Duck1776/PrivateVoice
# main.py

# UPDATES
# Separated the code into sections on seperate files

import json
import os
import sys
import pyaudio
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from sender import sender
from receiver import receiver

def generate_key():
    return os.urandom(32)

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


def save_settings(settings):
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
    except IOError as e:
        print(f"Error saving settings: {e}")

def load_settings():
    default_settings = {
        'raw_mic_input_id': 0,
        'encrypted_output_id': 0,
        'encrypted_input_id': 0,
        'decrypted_output_id': 0,
        'key': generate_key().hex()
    }
    
    try:
        if not os.path.exists('settings.json'):
            save_settings(default_settings)
            return default_settings

        with open('settings.json', 'r') as f:
            settings = json.load(f)
            
        for key in default_settings:
            if key not in settings:
                settings[key] = default_settings[key]
        
        return settings
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading settings: {e}")
        return default_settings



class AudioEncryptorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrivateVoice v00.02")
        self.setGeometry(100, 100, 600, 350)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.add_key_input(layout)
        self.add_device_selectors(layout)
        self.add_control_buttons(layout)

        self.encryption_thread = None
        self.populate_device_lists()
        self.load_settings()

    def add_key_input(self, layout):
        key_layout = QHBoxLayout()
        key_label = QLabel("Key:")
        self.key_input = QLineEdit()
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
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.regenerate_key_button = QPushButton("Regenerate Key")
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.regenerate_key_button)

        self.start_button.clicked.connect(self.start_encryption)
        self.stop_button.clicked.connect(self.stop_encryption)
        self.regenerate_key_button.clicked.connect(self.regenerate_key)

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
            QMessageBox.warning(self, "Warning", "Already running.")
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
            QMessageBox.warning(self, "Warning", "Not running")

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def regenerate_key(self):
        new_key = generate_key()
        self.key_input.setText(new_key.hex())
        QMessageBox.information(self, "Key Regenerated", "A new encryption key has been generated.")

    def save_settings(self):
        settings = {
            'raw_mic_input_id': self.raw_mic_input.currentIndex(),
            'encrypted_output_id': self.encrypted_output.currentIndex(),
            'encrypted_input_id': self.encrypted_input.currentIndex(),
            'decrypted_output_id': self.decrypted_output.currentIndex(),
            'key': self.key_input.text()
        }
        save_settings(settings)

    def load_settings(self):
        settings = load_settings()
        if settings:
            self.raw_mic_input.setCurrentIndex(settings.get('raw_mic_input_id', 0))
            self.encrypted_output.setCurrentIndex(settings.get('encrypted_output_id', 0))
            self.encrypted_input.setCurrentIndex(settings.get('encrypted_input_id', 0))
            self.decrypted_output.setCurrentIndex(settings.get('decrypted_output_id', 0))
            self.key_input.setText(settings.get('key', generate_key().hex()))

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = AudioEncryptorUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()