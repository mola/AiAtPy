from PySide6.QtCore import QObject, QRunnable, Slot, Signal
from database.session import MainSessionLocal
from database.crud import update_task_status
from llm_connectors.deepseek_connector import DeepSeekConnector
from llm_connectors.ollama_connector import OllamaConnector

class ComparisonTask(QObject,QRunnable):
    comparisonComplete = Signal(int, dict)

    def __init__(self, task_id, new_law_text, existing_law_text, section_data):
        super().__init__()
        QRunnable.__init__(self)
        self.task_id = task_id
        self.new_law_text = new_law_text
        self.existing_law_text = existing_law_text
        # self.detector = detector
        self.section_data = section_data
        self.llm_connector = DeepSeekConnector()
        # self.llm_connector = OllamaConnector()

        sc = section_data.get("system_prompt")
        if (sc and len(sc)>0):
            self.llm_connector.setSystemPrompt(sc)

    def run(self):
        result = {}
        try:
            # Format the prompt for LLM comparison
            # prompt = self._format_comparison_prompt()
            
            # Get LLM response
            print("processing: " , self.new_law_text , self.existing_law_text[:100])
            response = self.llm_connector.send_message(self.new_law_text, self.existing_law_text)

            # import random

            # # Randomly select between 0 and 1
            # random_choice = random.choice([0, 1])
            # response = {}
            # # Conditional assignment based on the random number
            # if random_choice == 1:
            #     response = {
            #         "why": "This statement seems questionable.",
            #         "is_contradiction": True
            #     }
            # else:
            #     response = {
            #         "why": "This statement doesn't seem questionable.",
            #         "is_contradiction": False
            #     }

            contradiction = response.get('is_contradiction', False)  # Default to False if missing
            
            # Create result dictionary
            result = {
                **self.section_data,
                'reason': response,
                'contradiction': contradiction
            }

            # self.detector.handle_comparison_complete(self.task_id, result)
            # print(response)
        except Exception as e:
            result= {"failed":e}
            print(f"Comparison failed: {str(e)}")
        
        self.comparisonComplete.emit(self.task_id, result)

    def _format_comparison_prompt(self):
        return (
            "Compare the following two legal texts and identify any logical paradoxes:\n\n"
            f"NEW LAW TEXT:\n{self.new_law_text}\n\n"
            f"EXISTING LAW TEXT:\n{self.existing_law_text}\n\n"
            "ANALYSIS:"
        )
