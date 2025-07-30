from PySide6.QtCore import QRunnable, Slot
from database.session import MainSessionLocal
from database.crud import update_task_status
from llm_connectors.deepseek_connector import DeepSeekConnector

class ComparisonTask(QRunnable):
    def __init__(self, task_id, new_law_text, existing_law_text):
        super().__init__()
        self.task_id = task_id
        self.new_law_text = new_law_text
        self.existing_law_text = existing_law_text
        self.llm_connector = DeepSeekConnector()

    def run(self):
        try:
            # Format the prompt for LLM comparison
            # prompt = self._format_comparison_prompt()
            
            # Get LLM response
            response = self.llm_connector.send_message(self.new_law_text, self.existing_law_text)
            # response = "hello"
            print(response)
            # Process response and update task

            self._process_response(response)
        except Exception as e:
            print(f"Comparison failed: {str(e)}")
            db = MainSessionLocal()
            try:
                update_task_status(db, self.task_id, "failed", str(e))
            finally:
                db.close()

    def _format_comparison_prompt(self):
        return (
            "Compare the following two legal texts and identify any logical paradoxes:\n\n"
            f"NEW LAW TEXT:\n{self.new_law_text}\n\n"
            f"EXISTING LAW TEXT:\n{self.existing_law_text}\n\n"
            "ANALYSIS:"
        )

    def _process_response(self, response):
        db = MainSessionLocal()
        try:
            # Update task with partial result
            update_task_status(db, self.task_id, "processing", response)
        finally:
            db.close()
