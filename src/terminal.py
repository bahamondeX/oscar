# src/terminal.py
import subprocess
import typing as tp

class Terminal:
    def execute_command(self, command: str) -> str:
        """Execute a terminal command and return the output"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            if result.returncode == 0:
                return f"Command executed successfully:\n{result.stdout}"
            else:
                return f"Command failed with error:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def run(self, content: str) -> tp.Generator[str, None, None]:
        """Parse content for commands and execute them"""
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            yield line
            result = self.execute_command(line)
            yield "\n"
            yield result
