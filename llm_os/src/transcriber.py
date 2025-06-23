import io
import time
import typing as tp

import numpy as np
import torch
import typing_extensions as tpe
from pydub import AudioSegment  # type: ignore

from .typedefs import Component, TranscriberKwargs


class Transcriber(Component[TranscriberKwargs]):

    def __init__(self):
        self.audio: torch.Tensor | None = None
        self.duration: float = 0
        self.silence_threshold: float = 0.01
        self.silence_duration: float = 0
        self.last_audio_time: float = time.time()
        self.min_audio_duration: float = 1.5
        self.silence_timeout: float = 2.5

    def load_audio(self, *, chunk: bytes) -> tuple[torch.Tensor, int]:
        if not chunk:
            return torch.tensor([]), 44100
        audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
        audio = torch.from_numpy(audio_np).unsqueeze(0)  # type: ignore
        sr = 44100
        return audio, sr

    def is_silent(self, audio: torch.Tensor) -> bool:
        if audio.numel() == 0:
            return True
        rms = torch.sqrt(torch.mean(audio**2))
        return bool(rms < self.silence_threshold)

    def handle_stream(self, *, stream: tp.Generator[bytes, None, None]):
        for chunk in stream:
            audio, sr = self.load_audio(chunk=chunk)

            if audio.numel() == 0:
                continue

            current_time = time.time()
            chunk_duration = audio.shape[1] / sr

            if self.is_silent(audio):
                self.silence_duration += current_time - self.last_audio_time
            else:
                self.silence_duration = 0

            self.last_audio_time = current_time

            # Only accumulate non-silent audio or audio during active speech
            if not self.is_silent(audio) or (
                self.audio is not None and self.silence_duration < 1.0
            ):
                if self.audio is None:
                    self.audio = audio
                    self.duration = chunk_duration
                else:
                    self.audio = torch.cat([self.audio, audio], dim=1)
                    self.duration += chunk_duration

            # Yield accumulated audio when silence threshold is reached
            if self.silence_duration >= self.silence_timeout:
                if self.audio is not None and self.duration >= self.min_audio_duration:
                    yield self.audio.numpy().squeeze(), sr
                self._reset_buffer()

    def _reset_buffer(self):
        self.audio = None
        self.duration = 0
        self.silence_duration = 0

    def run(self, **kwargs: tpe.Unpack[TranscriberKwargs]):
        for audio_array, sr in self.handle_stream(stream=kwargs["stream"]):
            # Skip if audio is too short or empty
            if len(audio_array) == 0:
                continue

            # Convert float32 [-1.0, 1.0] to int16 for pydub
            audio_int16 = (np.clip(audio_array, -1.0, 1.0) * 32767).astype(np.int16)

            # Create a WAV audio segment
            segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=sr,
                sample_width=2,
                channels=1,
            )

            # Export to in-memory WAV
            buffer = io.BytesIO()
            segment.export(buffer, format="wav")  # type: ignore
            buffer.seek(0)

            try:
                client = kwargs["client"]
                response = client.audio.transcriptions.create(
                    file=("audio.wav", buffer.read(), "audio/wav"),
                    model="whisper-large-v3",
                )
                if response.text.strip():  # Only yield non-empty transcriptions
                    yield response.text
            except Exception as e:
                print(f"Transcription error: {e}")
                continue
