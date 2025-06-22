# src/chatbot.py
import json
import typing as tp
from openai import OpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from .terminal import Terminal
from .utils import chunk_sentences

TOOL: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "iTerm",
        "description": (
            "Use this tool when the user asks to perform a task that can be done via the terminal "
            "on macOS using zsh. This includes running scripts, checking system status, modifying files, "
            "or any shell-related operation.\n\n"
            "Do not use this tool unless a command is clearly required. "
            "The 'command' string will be directly piped into zsh."
        ),
        "parameters": {
            "command": {
                "type": "string",
                "description": "The exact shell command to run (e.g., 'ls -la', 'brew install git', 'cd ~/Documents && code .').",
            }
        },
    },
}


iterm = Terminal()


class ChatBot:
    messages: list[ChatCompletionMessageParam]

    def __init__(self):
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are llmOS, a voice-driven operating system assistant running on a MacBook Air. "
                    "Your job is to help the user control their computer using natural language. "
                    "You can perform tasks like running terminal commands, creating files, installing packages, "
                    "scaffolding projects, summarizing logs, and automating workflows, just by interpreting the user's intent.\n\n"
                    "Respond clearly and concisely. If the user gives a command (e.g., 'turn off Wi-Fi', 'list Python files', "
                    "'git clone...'), decide whether to execute it by calling the iTerm tool.\n\n"
                    "Your response must always start by explaining what you're doing before executing anything. "
                    "For example: 'Sure, I'll disable Wi-Fi now.' or 'Running: ls -la'.\n\n"
                    "Once commands are executed, summarize the result if needed, and continue the conversation naturally.\n\n"
                    "When no command is needed, just respond as a helpful assistant with actionable guidance."
                ),
            }
        ]

    def run(self, *, content: str, client: OpenAI) -> tp.Generator[str, None, None]:
        self.messages.append({"role": "user", "content": content})

        response = client.chat.completions.create(
            messages=self.messages,
            model="gemini-2.5-flash",
            tools=[TOOL],
            tool_choice="auto",
            stream=True,
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
                    if tool_call.function and tool_call.function.arguments:
                        try:
                            args = json.loads(tool_call.function.arguments)
                            command = args.get("command", "").strip()
                            if command:
                                print(command)
                                print("\n")
                                for result in iterm.run(command):
                                    self.messages.append(
                                        {"role": "system", "content": result}
                                    )
                                    print(result)
                        except Exception as e:
                            error_msg = f"Failed to parse tool call: {e}"
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
