from PySide6.QtCore import QObject, Signal
from llm_connectors.base_connector import BaseConnector
from openai import OpenAI
from aiatconfig import AiAtConfig

class DeepSeekConnector(BaseConnector):

    def __init__(self):
        super().__init__()

        api_key = AiAtConfig.get_deepseek_api_key()
        print("APIKEY : " ,api_key)
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def send_message(self, message1, message2):
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "These messages contain law-related information. Compare these two law texts and identify if they contradict each other. Please identify and find contradictions in the text. Return as JSON with 'why' in persian language and 'Contradiction' keys. 'Contradiction' type as True or False"},
                {"role": "user", "content": message1},
                {"role": "user", "content": message2},
            ],
            stream=False,
            temperature=0.3
        )
        return response.choices[0].message.content
        # self.on_message_received(response.choices[0].message.content)


