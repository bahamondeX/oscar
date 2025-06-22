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
	terminal = Terminal()
	while True:
		stream = recorder.run()
		for chunk in transcriber.run(stream=stream):
			content = chatbot.run(content=chunk,client=client)
			print(f"Assistant: {content}")
			
			# Execute any commands in the response
			for command_result in terminal.run(content):
				print(command_result)
			
			# Generate and play TTS audio
			for audio_chunk in speaker.run(content=content,client=client):
				print("Playing TTS audio...")
				speaker.play_audio(audio_chunk)
