import datetime
import threading
import traceback
from contextlib import contextmanager

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


class StatusLogger:
    def __init__(self):
        self.start_time = None
        self.current_status = None
        self._status_lock = threading.Lock()

    def _get_timestamp(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _create_status_panel(self, title: str, message: str, style: str, emoji: str):
        timestamp = self._get_timestamp()
        content = Text()
        content.append(f"[{timestamp}] ", style="dim")
        content.append(f"{emoji} {message}", style=style)

        return Panel(
            Align.center(content),
            title=f"[bold]{title}[/bold]",
            border_style=style,
            padding=(0, 1),
        )

    @contextmanager
    def _spinner_context(self, message: str, style: str = "cyan"):
        with self._status_lock:
            try:
                if self.current_status:
                    self.current_status.stop()
                self.current_status = console.status(
                    f"[{style}]{message}[/{style}]", spinner="dots"
                )
                self.current_status.start()
                yield
            except Exception as e:
                self.error(f"Spinner context error: {e}")
                traceback.print_exc()
                raise
            finally:
                if self.current_status:
                    self.current_status.stop()
                    self.current_status = None

    def listening(self):
        console.clear()
        panel = self._create_status_panel(
            "🎤 LISTENING", "Waiting for your voice...", "cyan", "🎤"
        )
        console.print(panel)
        console.print()

    def silence_detected(self):
        console.print("[yellow]🔇 Silence detected, processing...[/yellow]")

    def transcribing(self):
        console.print()
        self.start_time = datetime.datetime.now()
        return self._spinner_context("📝 Transcribing audio...", "blue")

    def transcription_complete(self, text: str):
        duration = (
            (datetime.datetime.now() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )

        console.print(f"[green]✓ Transcription complete ({duration:.1f}s)[/green]")
        console.print()

        user_panel = Panel(
            Text(text, style="bold white"),
            title="[bold blue]👤 You said[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
        console.print(user_panel)
        console.print()

    def generating_text(self):
        self.start_time = datetime.datetime.now()
        return self._spinner_context("🤖 Generating response...", "magenta")

    def text_complete(self, text: str):
        duration = (
            (datetime.datetime.now() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )
        console.print(f"[green]✓ Response ready ({duration:.1f}s)[/green]")
        console.print()

    def executing_command(self, command: str):
        console.print()
        cmd_panel = Panel(
            Text(f"$ {command}", style="bold yellow"),
            title="[bold cyan]⚡ Executing Command[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
        console.print(cmd_panel)

    def command_result(self, result: str):
        display_result = result[:500] + "..." if len(result) > 500 else result

        result_panel = Panel(
            Text(display_result, style="dim white"),
            title="[bold green]📋 Command Output[/bold green]",
            border_style="green",
            padding=(0, 1),
        )
        console.print(result_panel)
        console.print()

    def generating_speech(self):
        self.start_time = datetime.datetime.now()
        return self._spinner_context("🎵 Generating speech...", "blue")

    def playing_audio(self):
        duration = (
            (datetime.datetime.now() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )
        console.print(f"[green]🔊 Playing audio ({duration:.1f}s generation)[/green]")

    def audio_complete(self):
        console.print("[green]✓ Audio playback complete[/green]")
        console.print()
        console.rule("[dim]Ready for next command[/dim]", style="dim")
        console.print()

    def error(self, message: str):
        error_panel = Panel(
            Text(message, style="bold red"),
            title="[bold red]✗ ERROR[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(error_panel)
        console.print()

    def info(self, message: str):
        console.print(f"[dim]ℹ {message}[/dim]")

    def assistant_response(self, text: str):
        response_panel = Panel(
            Text(text, style="white"),
            title="[bold magenta]🤖 llmOS Assistant[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        )
        console.print(response_panel)
        console.print()

    def system_startup(self):
        console.clear()
        startup_text = Text()
        startup_text.append("llmOS", style="bold magenta")
        startup_text.append(" - Voice Operating System", style="white")

        startup_panel = Panel(
            Align.center(startup_text),
            title="[bold cyan]🚀 SYSTEM READY[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print(startup_panel)
        console.print("[dim]Speak naturally to control your system...[/dim]")
        console.print()

    def __del__(self):
        with self._status_lock:
            if self.current_status:
                self.current_status.stop()
