#!/usr/bin/env python3
"""
Voice interface for GT New Horizons RAG system
Features:
- Wake word detection ("Hey GT", "Computer", "Assistant")
- Speech-to-text for questions
- Text-to-speech for responses
- Voice-enabled interactive mode
"""

import speech_recognition as sr
import pyttsx3
import threading
import time
import queue
from typing import Optional, Callable
import re

class VoiceInterface:
    def __init__(self, wake_words=None, language="en-US"):
        """Initialize voice interface"""
        self.wake_words = wake_words or ["hey gt", "computer", "assistant", "greg tech"]
        self.language = language
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
        # Voice control state
        self.listening = False
        self.active = False
        self.audio_queue = queue.Queue()
        
        # Calibrate microphone
        self.calibrate_microphone()
    
    def setup_tts(self):
        """Configure text-to-speech settings"""
        voices = self.tts_engine.getProperty('voices')
        if voices:
            # Try to find a female voice, fallback to first available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            else:
                self.tts_engine.setProperty('voice', voices[0].id)
        
        self.tts_engine.setProperty('rate', 180)  # Speed
        self.tts_engine.setProperty('volume', 0.8)  # Volume
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        print("Calibrating microphone for ambient noise...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone calibrated successfully!")
        except Exception as e:
            print(f"Warning: Could not calibrate microphone: {e}")
    
    def speak(self, text: str):
        """Convert text to speech"""
        try:
            # Clean text for TTS (remove markdown)
            clean_text = self.clean_text_for_tts(text)
            print(f"Speaking: {clean_text[:100]}...")
            self.tts_engine.say(clean_text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
    
    def clean_text_for_tts(self, text: str) -> str:
        """Clean markdown and formatting for TTS"""
        # Remove markdown links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove markdown bold **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        
        # Remove code blocks `code`
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove headers ###
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        
        # Remove bullet points
        text = re.sub(r'^\s*[•\-\*]\s*', '', text, flags=re.MULTILINE)
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Limit length for TTS
        if len(text) > 500:
            sentences = text.split('. ')
            text = '. '.join(sentences[:3]) + '.'
        
        return text.strip()
    
    def listen_for_wake_word(self, timeout=None) -> bool:
        """Listen for wake word in audio stream"""
        try:
            with self.microphone as source:
                print("Listening for wake word... (say 'Hey GT', 'Computer', or 'Assistant')")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
            
            text = self.recognizer.recognize_google(audio, language=self.language).lower()
            print(f"Heard: '{text}'")
            
            # Check if any wake word is in the recognized text
            for wake_word in self.wake_words:
                if wake_word in text:
                    print(f"Wake word '{wake_word}' detected!")
                    return True
            
            return False
            
        except sr.WaitTimeoutError:
            return False
        except sr.UnknownValueError:
            return False
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return False
        except Exception as e:
            print(f"Wake word detection error: {e}")
            return False
    
    def listen_for_command(self, timeout=10) -> Optional[str]:
        """Listen for voice command after wake word"""
        try:
            print("Listening for your question...")
            self.speak("What would you like to know about GT New Horizons?")
            
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            command = self.recognizer.recognize_google(audio, language=self.language)
            print(f"Command received: '{command}'")
            return command
            
        except sr.WaitTimeoutError:
            print("No command received within timeout")
            self.speak("I didn't hear anything. Please try again.")
            return None
        except sr.UnknownValueError:
            print("Could not understand the command")
            self.speak("Sorry, I didn't understand. Please speak clearly.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            self.speak("Sorry, there was an error with speech recognition.")
            return None
        except Exception as e:
            print(f"Command recognition error: {e}")
            return None
    
    def start_listening(self, command_callback: Callable[[str], str]):
        """Start continuous voice interface loop"""
        self.active = True
        print("\n" + "="*60)
        print("🎤 VOICE-ENABLED GT NEW HORIZONS ASSISTANT")
        print("="*60)
        print("Say one of these wake words to activate:")
        for wake_word in self.wake_words:
            print(f"  • '{wake_word.title()}'")
        print("\nPress Ctrl+C to exit voice mode")
        print("="*60)
        
        try:
            while self.active:
                # Listen for wake word
                if self.listen_for_wake_word(timeout=1):
                    self.speak("Yes, how can I help you?")
                    
                    # Listen for command
                    command = self.listen_for_command()
                    if command:
                        # Process command
                        print(f"\nProcessing: {command}")
                        response = command_callback(command)
                        
                        # Speak response (shortened for TTS)
                        if response:
                            self.speak(response)
                            print(f"\nFull response available above ↑")
                        
                        print("\n" + "-"*40)
                        print("Listening for wake word again...")
                
        except KeyboardInterrupt:
            print("\n\nVoice interface stopped by user")
        except Exception as e:
            print(f"Voice interface error: {e}")
        finally:
            self.stop_listening()
    
    def stop_listening(self):
        """Stop voice interface"""
        self.active = False
        print("Voice interface stopped")
    
    def test_voice_system(self):
        """Test voice system components"""
        print("Testing voice system...")
        
        # Test TTS
        print("1. Testing text-to-speech...")
        self.speak("Hello! Voice system is working correctly.")
        
        # Test microphone
        print("2. Testing microphone (say something)...")
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            text = self.recognizer.recognize_google(audio)
            print(f"   Heard: '{text}'")
            self.speak(f"I heard you say: {text}")
            
        except Exception as e:
            print(f"   Microphone test failed: {e}")
        
        print("Voice system test complete!")

class VoiceEnabledRAG:
    """Voice-enabled wrapper for RAG pipeline"""
    
    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline
        self.voice = VoiceInterface()
    
    def process_voice_command(self, command: str) -> str:
        """Process voice command and return response"""
        try:
            # Use RAG to get response
            response, sources = self.rag.generate_response(command, use_history=True)
            
            # Display full response
            print(f"\n📝 Full Response:")
            print("-" * 40)
            from markdown_renderer import render_markdown
            print(render_markdown(response))
            
            if sources:
                print(f"\n📚 Sources ({len(sources)} found):")
                for i, source in enumerate(sources, 1):
                    print(f"  {i}. {source['title']}")
                    print(f"     {source['url']}")
            
            return response
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(error_msg)
            return error_msg
    
    def start_voice_mode(self):
        """Start voice-enabled interactive mode"""
        # Check if knowledge base exists
        stats = self.rag.vector_db.get_collection_stats()
        if stats.get('total_chunks', 0) == 0:
            print("❌ Knowledge base is empty! Run 'python main_simple.py build' first.")
            return
        
        self.voice.start_listening(self.process_voice_command)
    
    def test_system(self):
        """Test the voice system"""
        self.voice.test_voice_system()

if __name__ == "__main__":
    # Test voice interface
    voice = VoiceInterface()
    voice.test_voice_system()