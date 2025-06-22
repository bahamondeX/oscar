# src/transcriber.py
import torch
import typing as tp
from requests import post
import numpy as np
import time


class Transcriber:

    def __init__(self):
        self.audio: torch.Tensor | None = None
        self.duration: float = 0
        self.silence_threshold: float = 0.01  # RMS threshold for silence detection
        self.silence_duration: float = 0
        self.last_audio_time: float = time.time()

    def load_audio(self, *, chunk: bytes) -> tuple[torch.Tensor, int]:
        # Convert raw PCM bytes to numpy array
        audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
        # Convert to torch tensor and add channel dimension
        audio = torch.from_numpy(audio_np).unsqueeze(0)  # type: ignore
        sr = 44100  # Sample rate from recorder
        return audio, sr

    def is_silent(self, audio: torch.Tensor) -> bool:
        """Check if audio chunk is silent based on RMS threshold"""
        rms = torch.sqrt(torch.mean(audio**2))
        return bool(rms < self.silence_threshold)

    def handle_stream(self, *, stream: tp.Generator[bytes, None, None]):
        for chunk in stream:
            if not chunk:
                continue
            audio, sr = self.load_audio(chunk=chunk)

            # Check for silence
            current_time = time.time()
            is_silent = self.is_silent(audio)

            if is_silent:
                self.silence_duration += current_time - self.last_audio_time
            else:
                self.silence_duration = 0

            self.last_audio_time = current_time

            # Accumulate audio
            if self.audio is None:
                self.audio = audio
                self.duration += audio.shape[1] / sr
            else:
                self.audio = torch.cat([self.audio, audio])
                self.duration += audio.shape[1] / sr

            # Trigger transcription after 5 seconds of silence
            if self.silence_duration >= 2.5 and self.audio is not None:  # type: ignore
                yield self.audio.numpy().tobytes()  # type: ignore
                self.audio = None
                self.duration = 0
                self.silence_duration = 0

    def run(self, *, stream: tp.Generator[bytes, None, None]):
        for chunk in self.handle_stream(stream=stream):
            response = post(
                "http://localhost:9000/asr?task=translate", files={"audio_file": chunk}
            )
            yield response.text
