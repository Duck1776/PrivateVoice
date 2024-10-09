# PrivateVoice
3rd party client working as a middle man between your voice and your choice of voice chat client - using a random 256 key that you must share chat.

# The idea: 
A software application running locally offline, encrypting in real time your michrophone audio, and dycrypting incoming audio from this application running on a different computer, through any voice communication software.

Written in Python right now, using PyAudio.

Current packages needed to install if you don't already

```bash
pip install pyaudio pycryptodome
```

# ROADMAP
Not in any particular order...
- [ ] Currently designed to use a Virtual Cable like VB-Cable but idelay would be better if it was its own input and output virtual cable.
- [ ] Save settings on close / set settings on open
- [ ] Include a "Show Key" button or eye ball to hide the key
- [ ] Have a "Copy" button to copy the key even if it is hidden
- [ ] Built in tool that can make sharing the key more secure. Right now, I assume you get a key, copy/paste it to the other user, paste into local application. But if there was a way to make a way to encrypt/decrypt the key using the program... (maybe not worth/necessary doing)
- [ ] Show stats on the bottom of the app that show TX/RX rate, packes per second - something that shows how well it is performing
- [ ] Somehow be able to adapt to the client, or perhaps a tab that has these settings. Presets for common voice chat applications, or a custom checkbox to fill in the settings if known
- [ ] Maybe create an RSA style of keys - so users dont have to share their key every time, they could save a hash with a rolling code
- [ ] Multi-user support - have a one-to-one mode and a one-to-many mode
- [ ] Add an option to limit live time. After X minutes stop the service
