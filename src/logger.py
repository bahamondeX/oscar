# src/logger.py (actualizado)
from colorama import Fore, Style, init
import datetime
import shutil

# Initialize colorama
init()


class StatusLogger:
    def __init__(self):
        self.start_time = None
        self.width = shutil.get_terminal_size((80, 20)).columns

    def _get_timestamp(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _line(self, char: str = "─"):
        return char * self.width

    def _title(self, title: str, icon: str = "•", color: str = Fore.WHITE):
        line = f" {icon} {title} "
        return f"{color}{line.center(self.width, '─')}{Style.RESET_ALL}"

    def _print_status(self, message: str, color: str, icon: str = "•"):
        timestamp = self._get_timestamp()
        print(
            f"{Style.DIM}[{timestamp}]{Style.RESET_ALL} {color}{icon} {message}{Style.RESET_ALL}"
        )

    def listening(self):
        print(self._title("Listening", "🎤", Fore.CYAN))

    def silence_detected(self):
        self._print_status("Silence detected, waiting...", Fore.YELLOW, "🔇")

    def transcribing(self):
        print(self._title("Transcribing Audio", "📝", Fore.BLUE))
        self.start_time = datetime.datetime.now()

    def transcription_complete(self, text: str):
        if self.start_time:
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
            print(self._title(f"Transcription Done ({duration:.1f}s)", "✓", Fore.GREEN))
        print(f"{Fore.LIGHTWHITE_EX}{Style.BRIGHT}🗣️  {text}{Style.RESET_ALL}\n")

    def generating_text(self):
        print(self._title("Generating Response", "🤖", Fore.MAGENTA))
        self.start_time = datetime.datetime.now()

    def text_complete(self, text: str):
        duration = (
            (datetime.datetime.now() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )
        print(self._title(f"Assistant Response ({duration:.1f}s)", "💬", Fore.GREEN))
        print(f"{Fore.LIGHTWHITE_EX}{Style.BRIGHT}{text}{Style.RESET_ALL}\n")

    def executing_command(self, command: str):
        print(self._title(f"Executing Command", "⚡", Fore.CYAN))
        print(f"{Fore.YELLOW}{Style.BRIGHT}$ {command}{Style.RESET_ALL}")

    def command_result(self, result: str):
        print(f"{Fore.LIGHTBLACK_EX}{result.strip()}{Style.RESET_ALL}\n")

    def generating_speech(self):
        print(self._title("Generating Speech", "🎵", Fore.BLUE))
        self.start_time = datetime.datetime.now()

    def playing_audio(self):
        if self.start_time:
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
            self._print_status(
                f"Playing audio ({duration:.1f}s generation)", Fore.GREEN, "🔊"
            )
        else:
            self._print_status("Playing audio...", Fore.GREEN, "🔊")

    def audio_complete(self):
        self._print_status("Audio playback complete", Fore.GREEN, "✓")

    def error(self, message: str):
        print(self._title("Error", "✗", Fore.RED))
        print(f"{Fore.RED}{message}{Style.RESET_ALL}\n")

    def info(self, message: str):
        print(f"{Fore.LIGHTWHITE_EX}{Style.DIM}ℹ {message}{Style.RESET_ALL}")
