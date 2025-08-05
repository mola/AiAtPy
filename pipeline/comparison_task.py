from PySide6.QtCore import QRunnable, Slot
from database.session import MainSessionLocal
from database.crud import update_task_status
from llm_connectors.deepseek_connector import DeepSeekConnector

class ComparisonTask(QRunnable):
    def __init__(self, task_id, new_law_text, existing_law_text, detector, section_data):
        super().__init__()
        self.task_id = task_id
        self.new_law_text = new_law_text
        self.existing_law_text = existing_law_text
        self.detector = detector
        self.section_data = section_data
        self.llm_connector = DeepSeekConnector()

    def run(self):
        try:
            # Format the prompt for LLM comparison
            # prompt = self._format_comparison_prompt()
            
            # Get LLM response
            response = self.llm_connector.send_message(self.new_law_text, self.existing_law_text)
            
            # Extract values with defaults
            why_text = response.get('why', 'No explanation provided')
            contradiction = response.get('Contradiction', False)  # Default to False if missing
            
            # Create result dictionary
            result = {
                **self.section_data,
                'reason': why_text,
                'contradiction': contradiction
            }

            self.detector.handle_comparison_complete(self.task_id, result)
            # print(response)
        except Exception as e:
            print(f"Comparison failed: {str(e)}")

    def _format_comparison_prompt(self):
        return (
            "Compare the following two legal texts and identify any logical paradoxes:\n\n"
            f"NEW LAW TEXT:\n{self.new_law_text}\n\n"
            f"EXISTING LAW TEXT:\n{self.existing_law_text}\n\n"
            "ANALYSIS:"
        )
