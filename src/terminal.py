# src/terminal.py
import os
import subprocess
import typing as tp

import typing_extensions as tpe

from .typedefs import JSON, Component, TerminalKwargs


class Terminal(Component[TerminalKwargs]):
    def __init__(self):
        self.current_dir = os.getcwd()
        self.env = os.environ.copy()
        self.command_history: list[str] = []

    def _is_safe_command(self, command: str) -> tuple[bool, str]:
        """Check if command is safe to execute"""
        dangerous_patterns = [
            "rm -rf /",
            "sudo rm -rf",
            "mkfs",
            "dd if=",
            "format",
            "> /dev/sda",
            "chmod -R 777 /",
            "chown -R root /",
        ]

        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return (
                    False,
                    f"Potentially dangerous command pattern detected: {pattern}",
                )

        return True, ""

    def _parse_cd_command(self, command: str) -> str:
        """Handle cd commands to maintain working directory state"""
        if command.strip().startswith("cd "):
            path = command.strip()[3:].strip()
            if not path or path == "~":
                path = os.path.expanduser("~")
            elif path.startswith("~/"):
                path = os.path.expanduser(path)
            elif not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)

            try:
                path = os.path.abspath(path)
                if os.path.exists(path) and os.path.isdir(path):
                    self.current_dir = path
                    return f"Changed directory to: {path}"
                else:
                    return f"Directory does not exist: {path}"
            except Exception as e:
                return f"Error changing directory: {str(e)}"
        return ""

    def execute_command(self, command: str) -> JSON:
        """Execute a terminal command and return structured output"""
        command = command.strip()
        if not command:
            return {"success": False, "output": "", "error": "Empty command"}

        # Check for safety
        is_safe, safety_msg = self._is_safe_command(command)
        if not is_safe:
            return {
                "success": False,
                "output": "",
                "error": f"Command blocked for safety: {safety_msg}",
                "command": command,
            }

        # Handle cd commands specially
        cd_result = self._parse_cd_command(command)
        if cd_result:
            return {
                "success": True,
                "output": cd_result,
                "error": "",
                "command": command,
                "cwd": self.current_dir,
            }

        # Store command in history
        self.command_history.append(command)

        try:
            # Execute command in current directory
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,  # Increased timeout
                cwd=self.current_dir,
                env=self.env,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip() if result.stdout else "",
                "error": result.stderr.strip() if result.stderr else "",
                "return_code": result.returncode,
                "command": command,
                "cwd": self.current_dir,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Command timed out after 60 seconds",
                "command": command,
                "cwd": self.current_dir,
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "command": command,
                "cwd": self.current_dir,
            }

    def run(
        self, **kwargs: tpe.Unpack[TerminalKwargs]
    ) -> tp.Generator[str, None, None]:
        """Execute command and yield formatted results"""
        result = self.execute_command(kwargs["content"])

        # Format output for display
        if result["success"]:
            if result["output"]:
                yield f"✅ Command executed successfully:\n{result['output']}"
            else:
                yield "✅ Command executed successfully (no output)"
        else:
            error_msg = result["error"] or "Unknown error"
            yield f"❌ Command failed:\n{error_msg}"

        # Show current directory if it changed
        if "cwd" in result and result["cwd"] != os.getcwd():
            yield f"\n📁 Current directory: {result['cwd']}"

    def get_current_directory(self) -> str:
        """Get current working directory"""
        return self.current_dir

    def get_command_history(self) -> list[str]:
        """Get command execution history"""
        return self.command_history.copy()

    def clear_history(self):
        """Clear command history"""
        self.command_history.clear()
