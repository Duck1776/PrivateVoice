# PrivateVoice
# https://github.com/Duck1776/PrivateVoice
# main.py

# UPDATES
# Auto Audio Channels

import sys
import os
import json
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
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
        self.setWindowTitle("PrivateVoice")
        self.setGeometry(100, 100, 400, 100)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

         # Create a horizontal layout for the key label and input
        key_layout = QHBoxLayout()
        key_label = QLabel("Key:")
        key_layout.addWidget(key_label)
        
        self.key_field = QLineEdit()
        self.key_field.setEchoMode(QLineEdit.Password)
        key_layout.addWidget(self.key_field)
        
        # Add the horizontal key layout to the main vertical layout
        layout.addLayout(key_layout)

        button_layout = QHBoxLayout()
        
        self.show_key_button = QPushButton("Show Key")
        self.show_key_button.setCheckable(True)
        self.show_key_button.toggled.connect(self.toggle_key_visibility)
        button_layout.addWidget(self.show_key_button)

        self.new_key_button = QPushButton("New Key")
        self.new_key_button.clicked.connect(self.generate_new_key)
        button_layout.addWidget(self.new_key_button)

        self.copy_key_button = QPushButton("Copy Key")
        self.copy_key_button.clicked.connect(self.copy_key)
        button_layout.addWidget(self.copy_key_button)

        layout.addLayout(button_layout)

        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.clicked.connect(self.toggle_encryption)
        self.start_stop_button.setFixedHeight(40)
        font = self.start_stop_button.font()
        font.setPointSize(font.pointSize() + 2)
        self.start_stop_button.setFont(font)
        layout.addWidget(self.start_stop_button)

        self.load_settings()

        self.sender_thread = None
        self.receiver_thread = None

    def load_settings(self):
        if not os.path.exists("settings.json"):
            self.generate_new_key()
        else:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.key_field.setText(settings["key"])

    def save_settings(self):
        settings = {
            "key": self.key_field.text()
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
        self.sender_thread = AudioThread(AudioSender, key)
        self.receiver_thread = AudioThread(AudioReceiver, key)
        
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
        for widget in self.findChildren((QLineEdit, QPushButton)):
            if widget != self.start_stop_button and widget != self.copy_key_button and widget != self.show_key_button:
                widget.setEnabled(False)

    def enable_settings(self):
        for widget in self.findChildren((QLineEdit, QPushButton)):
            widget.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())