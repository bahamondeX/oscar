# src/context.py
import json
import threading
import typing as tp
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .typedefs import JSON


class SystemContext:
    """Manages system context and state across sessions"""

    def __init__(self):
        self.context_file = Path.home() / ".llmos_context.json"
        self.lock = threading.Lock()
        self._context: dict[str, tp.Any] = {
            "current_project": None,
            "active_tasks": [],
            "user_preferences": {},
            "recent_commands": [],
            "working_directories": {},
            "installed_packages": {},
            "system_info": {},
            "session_start": datetime.now().isoformat(),
        }
        self.load_context()

    def load_context(self):
        """Load context from persistent storage"""
        try:
            if self.context_file.exists():
                with open(self.context_file, "r") as f:
                    saved_context = json.load(f)
                    self._context.update(saved_context)
        except Exception as e:
            print(f"Warning: Could not load context: {e}")

    def save_context(self):
        """Save context to persistent storage"""
        try:
            with self.lock:
                with open(self.context_file, "w") as f:
                    json.dump(self._context, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save context: {e}")

    def set_current_project(self, project_path: str, project_type: str = "unknown"):
        """Set the current working project"""
        with self.lock:
            self._context["current_project"] = {
                "path": project_path,
                "type": project_type,
                "last_accessed": datetime.now().isoformat(),
            }
            self.save_context()

    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """Get current project information"""
        return self._context.get("current_project")

    def add_task(self, task: str, priority: str = "normal"):
        """Add a task to the active tasks list"""
        with self.lock:
            task_obj: JSON = {
                "id": len(self._context["active_tasks"]) + 1,
                "description": task,
                "priority": priority,
                "created": datetime.now().isoformat(),
                "status": "pending",
            }
            self._context["active_tasks"].append(task_obj)
            self.save_context()

    def complete_task(self, task_id: int):
        """Mark a task as completed"""
        with self.lock:
            for task in self._context["active_tasks"]:
                if task["id"] == task_id:
                    task["status"] = "completed"
                    task["completed"] = datetime.now().isoformat()
            self.save_context()

    def get_active_tasks(self) -> list[JSON]:
        """Get list of active tasks"""
        return [
            task
            for task in self._context["active_tasks"]
            if task["status"] == "pending"
        ]

    def add_command_to_history(self, command: str, result: str, success: bool):
        """Add command to recent history"""
        with self.lock:
            history_entry: JSON = {
                "command": command,
                "result": result[:500],  # Truncate long results
                "success": success,
                "timestamp": datetime.now().isoformat(),
            }

            self._context["recent_commands"].append(history_entry)

            # Keep only last 50 commands
            if len(self._context["recent_commands"]) > 50:
                self._context["recent_commands"] = self._context["recent_commands"][
                    -50:
                ]

            self.save_context()

    def set_user_preference(self, key: str, value: Any):
        """Set a user preference"""
        with self.lock:
            self._context["user_preferences"][key] = value
            self.save_context()

    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self._context["user_preferences"].get(key, default)

    def update_system_info(self, info: Dict[str, Any]):
        """Update system information"""
        with self.lock:
            self._context["system_info"].update(info)
            self._context["system_info"]["last_updated"] = datetime.now().isoformat()
            self.save_context()

    def get_context_summary(self) -> str:
        """Get a summary of current context for the AI"""
        project = self.get_current_project()
        tasks = self.get_active_tasks()

        summary: list[str] = []

        if project:
            summary.append(f"Current project: {project['path']} ({project['type']})")

        if tasks:
            summary.append(f"Active tasks ({len(tasks)}):")
            for task in tasks[:3]:  # Show only first 3 tasks
                summary.append(f"  - {task['description']} [{task['priority']}]")

        recent_commands = self._context["recent_commands"][-3:]  # Last 3 commands
        if recent_commands:
            summary.append("Recent commands:")
            for cmd in recent_commands:
                status = "✅" if cmd["success"] else "❌"
                summary.append(f"  {status} {cmd['command']}")

        return "\n".join(summary) if summary else "No active context"

    def get_working_directory_for_project(self, project_name: str) -> Optional[str]:
        """Get the working directory for a specific project"""
        return self._context["working_directories"].get(project_name)

    def set_working_directory_for_project(self, project_name: str, directory: str):
        """Set the working directory for a specific project"""
        with self.lock:
            self._context["working_directories"][project_name] = directory
            self.save_context()

    def cleanup_old_data(self):
        """Clean up old data to prevent context file from growing too large"""
        with self.lock:
            # Remove completed tasks older than 7 days
            week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)

            self._context["active_tasks"] = [
                task
                for task in self._context["active_tasks"]
                if task["status"] == "pending"
                or datetime.fromisoformat(
                    task.get("completed", datetime.now().isoformat())
                ).timestamp()
                > week_ago
            ]

            # Keep only last 30 days of command history
            month_ago = datetime.now().timestamp() - (30 * 24 * 60 * 60)
            self._context["recent_commands"] = [
                cmd
                for cmd in self._context["recent_commands"]
                if datetime.fromisoformat(cmd["timestamp"]).timestamp() > month_ago
            ]

            self.save_context()


# Global context instance
system_context = SystemContext()
