# src/recorder.py
import pyaudio
from copy import copy

# Constants
CHUNK = 2048  # Increased buffer size to prevent overflow
FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
CHANNELS = 1  # Mono audio
RATE = 44100  # Sample rate in Hz

class Recorder:
    def run(self):
        """
		Generator function that reads audio from the Mac OS microphone.

		Yields:
			bytes: The next chunk of audio data from the microphone.
		"""
        p = pyaudio.PyAudio()

        # Open a stream to capture audio with larger buffer to prevent overflow
        stream = p.open(
			format=FORMAT, 
			channels=CHANNELS, 
			rate=RATE, 
			input=True, 
			frames_per_buffer=CHUNK,
			input_device_index=None,  # Use default input device
		)
        self.state = copy(stream)

        print("Listening...")

        try:
            while True:
                try:
                    data = self.state.read(CHUNK, exception_on_overflow=False)
                    yield data  # Yield the audio data chunk
                except OSError as e:
                    if "Input overflowed" in str(e):
                        # Skip overflowed data and continue
                        print("Audio buffer overflow - skipping chunk")
                        continue
                    else:
                        raise e
        except KeyboardInterrupt:
            pass  # Allow user to stop by pressing Ctrl+C

        # Stop and close the stream, and terminate the PyAudio session
        self.state.stop_stream()
        self.state.close()
        p.terminate()
