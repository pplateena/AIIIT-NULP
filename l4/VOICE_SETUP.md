# Voice Interface Setup Guide

Your GT New Horizons RAG system now supports voice interaction! Follow this guide to set up voice capabilities.

## 🎤 Features

- **Wake Word Detection**: Say "Hey GT", "Computer", "Assistant", or "Greg Tech" to activate
- **Speech-to-Text**: Ask questions naturally by voice
- **Text-to-Speech**: Hear responses spoken back to you
- **Hands-Free Operation**: Perfect for while playing Minecraft!

## 📦 Installation

### 1. Install Voice Dependencies

```bash
pip install SpeechRecognition pyttsx3 pyaudio
```

### 2. Platform-Specific Setup

#### Windows (Your System):
```bash
# Usually works out of the box, but if you have issues:
pip install pipwin
pipwin install pyaudio
```

#### macOS:
```bash
brew install portaudio
pip install pyaudio
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install python3-pyaudio portaudio19-dev
pip install pyaudio
```

## 🚀 Usage

### Test Voice System
```bash
python main_simple.py test-voice
```

### Start Voice Mode
```bash
python main_simple.py voice
```

### Example Voice Session:
1. Run: `python main_simple.py voice`
2. Say: **"Hey GT"** or **"Computer"**
3. Wait for: *"Yes, how can I help you?"*
4. Ask: **"What is a Large Steam Turbine?"**
5. Listen to the response!

## 🎯 Voice Commands

### Wake Words (case-insensitive):
- **"Hey GT"** - Primary wake word for GT New Horizons
- **"Computer"** - Classic AI assistant wake word
- **"Assistant"** - General assistant wake word  
- **"Greg Tech"** - Full mod name wake word

### Example Questions:
- "How do I build an Electric Blast Furnace?"
- "What materials do I need for LV tier?"
- "Tell me about the Assembly Line"
- "How does ore processing work?"

## 🔧 Configuration

### Voice Settings (in voice_interface.py):
```python
# Customize wake words
wake_words = ["hey gt", "computer", "assistant", "greg tech"]

# Adjust TTS settings
tts_engine.setProperty('rate', 180)     # Speech speed
tts_engine.setProperty('volume', 0.8)   # Volume level

# Speech recognition language
language = "en-US"  # or "en-GB", "en-AU", etc.
```

## 🛠️ Troubleshooting

### Common Issues:

#### 1. Microphone Not Working
```
Error: Could not calibrate microphone
```
**Solution**: Check microphone permissions and ensure it's not being used by other apps.

#### 2. PyAudio Installation Error
```
ERROR: Failed building wheel for pyaudio
```
**Solutions**:
- Windows: `pipwin install pyaudio`
- macOS: `brew install portaudio` first
- Linux: Install system audio libraries

#### 3. Speech Recognition Errors
```
Speech recognition error: [Errno 2] No such file or directory
```
**Solution**: Ensure internet connection (Google Speech API requires internet).

#### 4. TTS Not Working
```
TTS Error: No module named 'pyttsx3'
```
**Solution**: `pip install pyttsx3`

### Advanced Troubleshooting:

#### Test Individual Components:
```python
# Test microphone
python -c "import speech_recognition as sr; print('Mic OK')"

# Test TTS
python -c "import pyttsx3; e=pyttsx3.init(); e.say('test'); e.runAndWait()"

# Test full system
python main_simple.py test-voice
```

## 🎮 Gaming Integration Tips

### While Playing Minecraft:
1. Start voice mode in separate terminal
2. Keep terminal visible but minimized
3. Use push-to-talk if game conflicts with continuous listening
4. Adjust TTS volume to not conflict with game audio

### Optimal Setup:
- Use headset with microphone for clear audio
- Position terminal window for easy monitoring
- Consider dual monitor setup for best experience

## 🔒 Privacy Notes

- Speech recognition uses Google's API (requires internet)
- Audio is processed for wake words and commands only
- No audio is stored or logged by the system
- Voice data is not sent anywhere except Google for transcription

## 📋 Command Reference

| Command | Description |
|---------|-------------|
| `python main_simple.py voice` | Start voice-enabled interactive mode |
| `python main_simple.py test-voice` | Test voice system components |
| `python main_simple.py ask -q "question"` | Regular text-based questions |
| Ctrl+C | Exit voice mode |

## 🎵 Audio Settings

The system automatically:
- Calibrates for ambient noise
- Adjusts for your microphone sensitivity  
- Selects best available TTS voice
- Cleans responses for natural speech

Enjoy your voice-enabled GT New Horizons assistant! 🎤🤖