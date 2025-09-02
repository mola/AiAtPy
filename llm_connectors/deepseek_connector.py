from PySide6.QtCore import QObject, Signal
from llm_connectors.base_connector import BaseConnector
from openai import OpenAI
from aiatconfig import AiAtConfig
import json

class DeepSeekConnector(BaseConnector):

    def __init__(self):
        super().__init__()

        self.system_prompt = "These messages contain law-related information. Compare these two law texts and identify if they contradict each other. Please identify and find contradictions in the text. Return as JSON with 'why' in persian language and 'is_contradiction' keys. 'is_contradiction' type as True or False"
        api_key = AiAtConfig.get_deepseek_api_key()
        # print("APIKEY : " ,api_key)
        self.client = OpenAI(api_key=api_key, base_url="http://alphapi.datall.ir")

    def setSystemPrompt(self, text):
        self.system_prompt = text
        
    def send_message(self, message1, message2):
        response = self.client.chat.completions.create(
            model="DeepSeek-V3.1",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message1},
                {"role": "user", "content": message2},
            ],
            stream=False,
            temperature=0.3
        )
        content = response.choices[0].message.content
        
        # Remove Markdown code block markers (```json and ```)
        if content.startswith('```json') and content.endswith('```'):
            content = content[7:-3].strip()  # Remove ```json and ```
        elif content.startswith('```') and content.endswith('```'):
            content = content[3:-3].strip()  # Remove ``` and ```
        
        # Try parsing JSON, return empty dict if invalid
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
