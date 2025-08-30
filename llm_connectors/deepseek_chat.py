from PySide6.QtCore import QObject, Signal
from llm_connectors.base_connector import BaseConnector
from openai import OpenAI
from aiatconfig import AiAtConfig
import json

class DeepSeekChat(BaseConnector):

    def __init__(self):
        super().__init__()
        self.system_prompt = "You are a helpful AI assistant."
        self.conversation_history = []
        api_key = AiAtConfig.get_deepseek_api_key()
        self.client = OpenAI(api_key=api_key, base_url="http://alphapi.datall.ir/v1")

    def setSystemPrompt(self, text):
        self.system_prompt = text
        
    def send_message(self, message):
        # Prepare messages including system prompt and conversation history
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model="DeepSeek-V3",
            messages=messages,
            stream=False,
            temperature=0.3
        )
        
        # Get assistant's reply
        assistant_reply = response.choices[0].message.content
        
        # Add both user message and assistant reply to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": assistant_reply})
        
        return assistant_reply

    def reset(self):
        """Reset the conversation history while keeping the system prompt"""
        self.conversation_history = []