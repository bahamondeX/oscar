# src/logger.py
from colorama import Fore, Back, Style, init
import datetime

# Initialize colorama for cross-platform colored output
init()

class StatusLogger:
    def __init__(self):
        self.start_time = None
    
    def _get_timestamp(self):
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def _print_status(self, message: str, color: str, icon: str = "•"):
        timestamp = self._get_timestamp()
        print(f"{Style.DIM}[{timestamp}]{Style.RESET_ALL} {color}{icon} {message}{Style.RESET_ALL}")
    
    def listening(self):
        self._print_status("Listening for audio...", Fore.CYAN, "🎤")
    
    def silence_detected(self):
        self._print_status("Silence detected, waiting...", Fore.YELLOW, "🔇")
    
    def transcribing(self):
        self._print_status("Transcribing audio...", Fore.BLUE, "📝")
        self.start_time = datetime.datetime.now()
    
    def transcription_complete(self, text: str):
        if self.start_time:
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
            self._print_status(f"Transcription complete ({duration:.1f}s): \"{text[:50]}...\"", Fore.GREEN, "✓")
        else:
            self._print_status(f"Transcription complete: \"{text[:50]}...\"", Fore.GREEN, "✓")
    
    def generating_text(self):
        self._print_status("Generating response...", Fore.MAGENTA, "🤖")
        self.start_time = datetime.datetime.now()
    
    def text_complete(self, text: str):
        if self.start_time:
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
            self._print_status(f"Response generated ({duration:.1f}s)", Fore.GREEN, "✓")
        else:
            self._print_status("Response generated", Fore.GREEN, "✓")
        print(f"{Fore.WHITE}{Style.BRIGHT}Assistant: {text}{Style.RESET_ALL}")
    
    def executing_command(self, command: str):
        self._print_status(f"Executing: {command}", Fore.CYAN, "⚡")
    
    def command_result(self, result: str):
        lines = result.strip().split('\n')
        for line in lines:
            if line.strip():
                print(f"{Style.DIM}  {line}{Style.RESET_ALL}")
    
    def generating_speech(self):
        self._print_status("Generating speech...", Fore.BLUE, "🎵")
        self.start_time = datetime.datetime.now()
    
    def playing_audio(self):
        if self.start_time:
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
            self._print_status(f"Playing audio ({duration:.1f}s generation time)...", Fore.GREEN, "🔊")
        else:
            self._print_status("Playing audio...", Fore.GREEN, "🔊")
    
    def audio_complete(self):
        self._print_status("Audio playback complete", Fore.GREEN, "✓")
    
    def error(self, message: str):
        self._print_status(f"Error: {message}", Fore.RED, "✗")
    
    def info(self, message: str):
        self._print_status(message, Fore.WHITE, "ℹ")

# Global logger instance
logger = StatusLogger()
