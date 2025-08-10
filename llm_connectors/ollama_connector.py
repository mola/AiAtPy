from llm_connectors.base_connector import BaseConnector
import requests
import json

class OllamaConnector(BaseConnector):

    def __init__(self):
        super().__init__()
        self.model_name = "deepseek-r1:latest"
        self.system_prompt = (
            "These messages contain law-related information. "
            "Compare these two law texts and identify if they contradict each other. "
            "Please identify and find contradictions in the text. Return as JSON with 'why' in persian language and 'Contradiction' keys. "
            "'Contradiction' type as True or False"
        )
        self.base_url = "http://localhost:11434"  # Set the appropriate URL for your Ollama server

    def setSystemPrompt(self, text):
        self.system_prompt = text

    def send_message(self, message1, message2):
        # Prepare the payload
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message1},
                {"role": "user", "content": message2}
            ],
            "stream":False
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            # Send a POST request to the Ollama server
            response = requests.post(f"{self.base_url}/api/chat", json=payload, headers=headers)
            response.raise_for_status()  # Raise an error for HTTP error responses
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return {}

        # Assuming the output is JSON formatted
        try:
            content = response.json()  # Parse the JSON response
            return content
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return {}

# Example usage
# if __name__ == "__main__":
#     connector = OllamaConnector(model_name="deepseek-r1:latest")
#     result = connector.send_message("Text message one.", "Text message two.")
#     print(result)