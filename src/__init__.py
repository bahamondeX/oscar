# src/__init__.py
from .chatbot import ChatBot
from .recorder import Recorder
from .speaker import Speaker
from .transcriber import Transcriber
from .terminal import Terminal
from openai import OpenAI

def main():
    client = OpenAI(base_url="https://api.oscarbahamonde.cloud/v1")
    recorder = Recorder()
    transcriber = Transcriber()
    chatbot = ChatBot()
    speaker = Speaker()
    while True:
        stream = recorder.run()
        for chunk in transcriber.run(stream=stream):
            for content in chatbot.run(content=chunk, client=client):
                print(f"\nAssistant:\n {content}")
                # Generate and play TTS audio
                for audio_chunk in speaker.run(content=content, client=client):
                    print("Playing TTS audio...")
                    speaker.play_audio(audio_chunk)
