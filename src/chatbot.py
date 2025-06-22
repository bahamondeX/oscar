# src/chatbot.py
import json
from openai import OpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from .terminal import Terminal

TOOL: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "iTerm",
        "description": "A zsh SHELL environment of a MacBook Air where you can execute commands to perform actions, the command property of this tool will be directly piped to the stdin of iTerm.",
        "parameters": {"command": {"type": "string"}},
    },
}


iterm = Terminal()

class ChatBot:
    messages:list[ChatCompletionMessageParam]

    def __init__(self):
        self.messages = [
            {
                "role": "system", 
                "content": """You are llmOS an operating system in which the user can control it's own computer and execute infinite actions just by interacting with you, the llm. You enable accesibility for new users to perform automations, coding, project scaffolding, monitoring or just toying with the Operating System via zsh SHELL environment."""
            }
        ]

    def run(self, *, content: str, client: OpenAI):
        self.messages.append({"role": "user", "content": content})
        response = client.chat.completions.create(
			messages=self.messages, model="gemini-2.5-flash", tools=[TOOL],tool_choice="auto"
		)
        
        # Handle case where response is a string instead of completion object
        if isinstance(response, str):
            self.messages.append({"role":"assistant","content":response})
            return response
            
        calls = response.choices[0].message.tool_calls
        if not calls or len(calls)==0:
            pass
        else:
            for call in calls:
                if call.function and call.function.name and call.function.arguments:
                    data = json.loads(call.function.arguments)
                    for result in iterm.run(content=data['command']):
                        self.messages.append({"role":"system","content":result})
                        print(result)
        data = response.choices[0].message.content
        if not data:
            raise ValueError("No content")
        self.messages.append({"role":"assistant","content":data})
        return data
