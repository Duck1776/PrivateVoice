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
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QPushButton, QLineEdit, QComboBox, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from crypto import generate_key
from sender import AudioSender
from receiver import AudioReceiver

logging.basicConfig(level=logging.DEBUG)

class AudioThread(QThread):
    error_signal = pyqtSignal(str)

    def __init__(self, audio_class, *args):
        super().__init__()
        self.audio_class = audio_class
        self.args = args
        self.audio_instance = None

    def run(self):
        try:
            self.audio_instance = self.audio_class(*self.args)
            self.audio_instance.start()
        except Exception as e:
            self.error_signal.emit(str(e))

    def stop(self):
        if self.audio_instance:
            self.audio_instance.stop()
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Encryption")
        self.setGeometry(100, 100, 400, 500)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.init_main_tab()
        self.init_settings_tab()

        self.load_settings()

        self.sender_thread = None
        self.receiver_thread = None

    def init_main_tab(self):
        main_tab = QWidget()
        layout = QVBoxLayout()
        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.clicked.connect(self.toggle_encryption)
        layout.addWidget(self.start_stop_button)
        main_tab.setLayout(layout)
        self.tab_widget.addTab(main_tab, "Main")

    def init_settings_tab(self):
        settings_tab = QWidget()
        layout = QVBoxLayout()

        self.key_field = QLineEdit()
        self.key_field.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Encryption Key:"))
        layout.addWidget(self.key_field)

        self.show_key_button = QPushButton("Show Key")
        self.show_key_button.setCheckable(True)
        self.show_key_button.toggled.connect(self.toggle_key_visibility)
        layout.addWidget(self.show_key_button)

        self.new_key_button = QPushButton("New Key")
        self.new_key_button.clicked.connect(self.generate_new_key)
        layout.addWidget(self.new_key_button)

        self.copy_key_button = QPushButton("Copy Key")
        self.copy_key_button.clicked.connect(self.copy_key)
        layout.addWidget(self.copy_key_button)

        input_devices, output_devices = self.get_audio_devices()

        self.mic_input = QComboBox()
        self.mic_input.addItems(input_devices)
        layout.addWidget(QLabel("Microphone Input:"))
        layout.addWidget(self.mic_input)

        self.encrypted_output = QComboBox()
        self.encrypted_output.addItems(output_devices)
        layout.addWidget(QLabel("Encrypted Output:"))
        layout.addWidget(self.encrypted_output)

        self.encrypted_input = QComboBox()
        self.encrypted_input.addItems(input_devices)
        layout.addWidget(QLabel("Encrypted Input:"))
        layout.addWidget(self.encrypted_input)

        self.decrypted_output = QComboBox()
        self.decrypted_output.addItems(output_devices)
        layout.addWidget(QLabel("Decrypted Output:"))
        layout.addWidget(self.decrypted_output)

        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_settings_button)

        settings_tab.setLayout(layout)
        self.tab_widget.addTab(settings_tab, "Settings")

    def get_audio_devices(self):
        p = pyaudio.PyAudio()
        input_devices = []
        output_devices = []
        
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            device_name = device_info['name']
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_name)
            if device_info['maxOutputChannels'] > 0:
                output_devices.append(device_name)
        
        p.terminate()
        return input_devices, output_devices

    def get_device_index(self, device_name, is_input):
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['name'] == device_name:
                if (is_input and dev['maxInputChannels'] > 0) or (not is_input and dev['maxOutputChannels'] > 0):
                    return i
        return -1

    def load_settings(self):
        if not os.path.exists("settings.json"):
            self.generate_new_key()
        else:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.key_field.setText(settings["key"])
                
                if "mic_input" in settings and settings["mic_input"] in [self.mic_input.itemText(i) for i in range(self.mic_input.count())]:
                    self.mic_input.setCurrentText(settings["mic_input"])
                if "encrypted_output" in settings and settings["encrypted_output"] in [self.encrypted_output.itemText(i) for i in range(self.encrypted_output.count())]:
                    self.encrypted_output.setCurrentText(settings["encrypted_output"])
                if "encrypted_input" in settings and settings["encrypted_input"] in [self.encrypted_input.itemText(i) for i in range(self.encrypted_input.count())]:
                    self.encrypted_input.setCurrentText(settings["encrypted_input"])
                if "decrypted_output" in settings and settings["decrypted_output"] in [self.decrypted_output.itemText(i) for i in range(self.decrypted_output.count())]:
                    self.decrypted_output.setCurrentText(settings["decrypted_output"])

    def save_settings(self):
        settings = {
            "key": self.key_field.text(),
            "mic_input": self.mic_input.currentText(),
            "encrypted_output": self.encrypted_output.currentText(),
            "encrypted_input": self.encrypted_input.currentText(),
            "decrypted_output": self.decrypted_output.currentText()
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)
        logging.info("Settings saved successfully")

    def toggle_key_visibility(self, checked):
        self.key_field.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def generate_new_key(self):
        new_key = generate_key()
        self.key_field.setText(new_key)
        self.save_settings()

    def copy_key(self):
        QApplication.clipboard().setText(self.key_field.text())

    def toggle_encryption(self):
        if self.sender_thread is None and self.receiver_thread is None:
            self.start_encryption()
        else:
            self.stop_encryption()

    def start_encryption(self):
        key = self.key_field.text()
        
        input_index = self.get_device_index(self.mic_input.currentText(), True)
        output_index = self.get_device_index(self.encrypted_output.currentText(), False)
        encrypted_input_index = self.get_device_index(self.encrypted_input.currentText(), True)
        decrypted_output_index = self.get_device_index(self.decrypted_output.currentText(), False)
        
        if -1 in [input_index, output_index, encrypted_input_index, decrypted_output_index]:
            logging.error("Error: Invalid device selection")
            return

        self.sender_thread = AudioThread(AudioSender, key, input_index, output_index)
        self.receiver_thread = AudioThread(AudioReceiver, key, encrypted_input_index, decrypted_output_index)
        
        self.sender_thread.error_signal.connect(self.handle_audio_error)
        self.receiver_thread.error_signal.connect(self.handle_audio_error)
        
        self.sender_thread.start()
        self.receiver_thread.start()
        
        self.start_stop_button.setText("Stop")
        self.disable_settings()

    def stop_encryption(self):
        if self.sender_thread:
            self.sender_thread.stop()
            self.sender_thread = None
        if self.receiver_thread:
            self.receiver_thread.stop()
            self.receiver_thread = None
        self.start_stop_button.setText("Start")
        self.enable_settings()

    def handle_audio_error(self, error_message):
        logging.error(f"Audio Error: {error_message}")
        self.stop_encryption()

    def disable_settings(self):
        for widget in self.tab_widget.widget(1).findChildren((QLineEdit, QComboBox, QPushButton)):
            if widget != self.copy_key_button:
                widget.setEnabled(False)

    def enable_settings(self):
        for widget in self.tab_widget.widget(1).findChildren((QLineEdit, QComboBox, QPushButton)):
            widget.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())