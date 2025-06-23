# src/chatbot.py
import json
import typing as tp

import typing_extensions as tpe
from openai.types.chat.chat_completion_message_param import \
    ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import \
    ChatCompletionToolParam
from src.typedefs import JSON, ChatbotKwargs, Component

from .context import system_context
from .logger import StatusLogger
from .terminal import Terminal
from .utils import chunk_sentences

TOOLS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "system_action",
            "description": (
                "Run a shell command on macOS. Use this for:\n"
                "• File operations\n"
                "• Git, dev tools, and scripts\n"
                "• Process or network management\n"
                "• App control or install\n"
                "• Text parsing with grep, awk, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run as-is.",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Short reason for the command.",
                    },
                    "requires_confirmation": {
                        "type": "boolean",
                        "description": "True if the command is risky or non-reversible.",
                    },
                },
                "required": ["command", "explanation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_task",
            "description": (
                "Run a sequence of commands to complete a multi-step task. Use this for:\n"
                "• Project setup\n"
                "• Dev environment provisioning\n"
                "• Install & configure workflows\n"
                "• File or repo operations in batches"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name": {
                        "type": "string",
                        "description": "Label for the overall task.",
                    },
                    "commands": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "Shell command to run.",
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Short action description.",
                                },
                                "continue_on_error": {
                                    "type": "boolean",
                                    "description": "If true, continues even if this step fails.",
                                },
                            },
                            "required": ["command", "description"],
                        },
                        "description": "Commands to execute, in order.",
                    },
                },
                "required": ["task_name", "commands"],
            },
        },
    },
]

iterm = Terminal()
logger = StatusLogger()


class ChatBot(Component[ChatbotKwargs]):
    messages: list[ChatCompletionMessageParam]

    def __init__(self):
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are **llmOS**, the control layer between natural language and macOS.\n\n"
                    "🎯 PURPOSE:\n"
                    "• Turn user intent into immediate system actions\n"
                    "• Respond in plain, concise language\n"
                    "• Prioritize doing over explaining\n"
                    "• Automate complex tasks when appropriate\n\n"
                    "🧩 CAPABILITIES:\n"
                    "• File and folder management\n"
                    "• Terminal command execution\n"
                    "• App launching and control\n"
                    "• Git and package management\n"
                    "• Script and automation workflows\n"
                    "• System insights: CPU, memory, network, etc.\n\n"
                    "🗣️ BEHAVIOR:\n"
                    "• Speak less, do more\n"
                    "• Skip unnecessary steps\n"
                    "• Chain related actions automatically\n"
                    "• Fill in details intelligently when obvious\n"
                    "• React fast, like a real-time shell with intuition\n\n"
                    "🧠 CONTEXT:\n"
                    "• Track current working directory and recent commands\n"
                    "• Remember ongoing workflows\n"
                    "• Detect intent from phrasing and act on it\n\n"
                    "Your job is not to simulate a shell — you *are* the OS interface."
                ),
            }
        ]

    def run(self, **kwargs: tpe.Unpack[ChatbotKwargs]) -> tp.Generator[str, None, None]:
        # Add context to user message
        client = kwargs["client"]
        content = kwargs["content"]
        context_summary = system_context.get_context_summary()
        enhanced_content = (
            f"{content}\n\n[SYSTEM CONTEXT]\n{context_summary}"
            if context_summary.strip() != "No active context"
            else content
        )

        self.messages.append({"role": "user", "content": enhanced_content})
        logger.generating_text()

        response = client.chat.completions.create(
            messages=self.messages,
            model="gemini-2.5-flash",
            tools=TOOLS,
            tool_choice="auto",
            stream=True,
            temperature=0.2,
        )

        buffer = ""
        full_response = ""
        for chunk in response:
            delta = chunk.choices[0].delta

            # Handle streamed content
            if delta.content:
                buffer += delta.content
                full_response += delta.content
                for text_chunk in chunk_sentences(buffer):
                    yield text_chunk
                    buffer = ""

            # Handle tool calls
            if delta.tool_calls:
                for tool_call in delta.tool_calls:
                    if tool_call.function and tool_call.function.name:
                        try:
                            if tool_call.function.arguments:
                                args = json.loads(tool_call.function.arguments)

                                if tool_call.function.name == "system_action":
                                    self._handle_single_command(args)
                                elif tool_call.function.name == "system_task":
                                    self._handle_multi_step_task(args)

                        except Exception as e:
                            error_msg = f"Tool execution error: {str(e)}"
                            logger.error(error_msg)
                            self.messages.append(
                                {"role": "system", "content": error_msg}
                            )
                            yield error_msg

        # Final leftover buffer
        if buffer.strip():
            yield buffer.strip()
            full_response += buffer.strip()

        # Save the assistant's full message
        if full_response.strip():
            self.messages.append(
                {"role": "assistant", "content": full_response.strip()}
            )
            logger.text_complete(full_response.strip())
            logger.assistant_response(full_response.strip())

    def _handle_single_command(self, args: JSON):
        command = args.get("command") or ""
        command = command.strip()
        explanation = args.get("explanation", "")
        requires_confirmation = args.get("requires_confirmation", False)

        if not command:
            return

        if requires_confirmation:
            logger.info(f"⚠️  This command requires confirmation: {explanation}")
            # In a real implementation, you'd want to add confirmation logic here

        logger.executing_command(command)
        logger.info(explanation)

        success = True
        result_text = ""

        for result in iterm.run(content=command):
            self.messages.append({"role": "system", "content": result})
            logger.command_result(result)
            result_text += result + "\n"
            if "❌" in result:
                success = False

        # Add to context history
        system_context.add_command_to_history(command, result_text, success)

    def _handle_multi_step_task(self, args: JSON):
        task_name = args.get("task_name", "Multi-step task")
        commands = args.get("commands", [])

        logger.info(f"🔄 Starting task: {task_name}")

        for i, cmd_info in enumerate(commands, 1):
            command = cmd_info.get("command", "")
            description = cmd_info.get("description", "")
            continue_on_error = cmd_info.get("continue_on_error", False)

            if not command:
                continue

            logger.info(f"Step {i}/{len(commands)}: {description}")
            logger.executing_command(command)

            try:
                for result in iterm.run(content=command):
                    self.messages.append({"role": "system", "content": result})
                    logger.command_result(result)

                    # Check for errors if continue_on_error is False
                    if not continue_on_error and "error" in result.lower():
                        logger.error(f"Task stopped due to error in step {i}")
                        return

            except Exception as e:
                error_msg = f"Error in step {i}: {str(e)}"
                logger.error(error_msg)
                if not continue_on_error:
                    return

        logger.info(f"✅ Task completed: {task_name}")
