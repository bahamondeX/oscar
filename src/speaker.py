# src/speaker.py
from openai import OpenAI
import pyaudio
import io
import tempfile
import os
from pydub import AudioSegment  # type: ignore
from pydub.playback import play  # type: ignore

class Speaker:

    def __init__(self):
        self.p = pyaudio.PyAudio()

    def play_audio_with_pydub(self, audio_data: bytes):
        """Play audio using pydub for better format handling"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(audio_data)
                temp_filename = temp_file.name

            # Load and play with pydub
            audio = AudioSegment.from_file(temp_filename)  # type: ignore
            play(audio)  # type: ignore

        except Exception as e:
            print(f"Pydub playback failed: {e}, trying raw PCM...")
            self.play_audio_raw_pcm(audio_data)
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_filename)  # type: ignore
            except:
                pass

    def play_audio_raw_pcm(self, audio_data: bytes):
        """Fallback: Play as raw PCM data"""
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 24000  # Try common TTS rate
        CHUNK = 1024

        stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            frames_per_buffer=CHUNK,
        )

        try:
            audio_io = io.BytesIO(audio_data)
            while True:
                chunk = audio_io.read(CHUNK * 2)
                if not chunk:
                    break
                stream.write(chunk)
        finally:
            stream.stop_stream()
            stream.close()

    def play_audio(self, audio_data: bytes):
        """Play audio data through speakers with format detection"""
        # Try pydub first (handles MP3, WAV, etc.)
        self.play_audio_with_pydub(audio_data)

    def run(self, *, content: str, client: OpenAI):
        response = client.audio.speech.create(
            input=content,
            model="tts-1-hd",
            voice="nova",
            response_format="mp3",  # Explicitly request MP3 format
        )

        # Collect all audio data
        audio_data = b""
        for chunk in response.iter_bytes():
            audio_data += chunk

        # Debug: Check audio format
        print(f"Audio data size: {len(audio_data)} bytes")
        print(
            f"First few bytes: {audio_data[:10].hex() if len(audio_data) >= 10 else 'N/A'}"
        )

        # Play the complete audio
        self.play_audio(audio_data)
        yield audio_data  # Still yield for compatibility

    def __del__(self):
        """Cleanup PyAudio instance"""
        if hasattr(self, "p"):
            self.p.terminate()
