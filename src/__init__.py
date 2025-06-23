# src/__init__.py
import os

from openai import OpenAI

from .chatbot import ChatBot
from .logger import StatusLogger
from .recorder import Recorder
from .speaker import Speaker
from .transcriber import Transcriber


def main():
    stt = OpenAI(
        base_url="https://api.groq.com/openai/v1", api_key=os.environ["GROQ_API_KEY"]
    )
    llm = OpenAI()
    tts = OpenAI(base_url="https://api.oscarbahamonde.cloud/v1")

    logger = StatusLogger()
    logger.system_startup()

    recorder = Recorder()
    transcriber = Transcriber()
    chatbot = ChatBot()
    speaker = Speaker()

    while True:
        try:
            logger.listening()
            stream = recorder.run()

            for chunk in transcriber.run(stream=stream, client=stt):
                if not chunk.strip():
                    continue

                # Transcription step
                with logger.transcribing():
                    pass  # spinner just for effect before printing transcription

                logger.transcription_complete(chunk)

                # LLM generation
                full_response = ""
                with logger.generating_text():
                    for content in chatbot.run(content=chunk, client=llm):
                        full_response += content + " "

                logger.text_complete(full_response)

                if full_response.strip():
                    # TTS generation and playback
                    with logger.generating_speech():
                        for audio_data in speaker.run(
                            content=full_response.strip(), client=tts
                        ):
                            speaker.play_audio(audio_data=audio_data)
                            logger.playing_audio()
                    logger.audio_complete()

        except KeyboardInterrupt:
            logger.info("Shutting down llmOS...")
            break
        except Exception as e:
            logger.error(f"System error: {str(e)}")
            continue
