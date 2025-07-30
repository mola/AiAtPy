from PySide6.QtCore import QObject, QThreadPool
from database.session import RulesSessionLocal, MainSessionLocal
from database.crud import update_task_status
from database.models import AnalysisTask
from .comparison_task import ComparisonTask
from database.models_rules import LWSection

class Paradox2Detector(QObject):
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        self.thread_pool = QThreadPool.globalInstance()
        # Set max threads (e.g., 4-8 depending on system capabilities)
        self.thread_pool.setMaxThreadCount(4)

    def initialize(self):
        # Initialize any resources needed
        pass

    def process_task(self, data):
        db = MainSessionLocal()
        db_r = RulesSessionLocal()
        try:

            # Extract data from JSON
            law_id = data.get('law_id')
            section_no = data.get('section_no')
            check_law_id = data.get('check_law_id')
            task_id = 0

            # Get the section text for the current law/section
            current_section = db_r.query(LWSection.SECTIONTEXT).filter(LWSection.F_LWLAWID == law_id,LWSection.SECTIONTYPENO == section_no).first()

            if not current_section:
                raise ValueError("Section not found")

            task_prompt = current_section.SECTIONTEXT

            # Get all sections from the check_law_id
            existing_laws = db_r.query(LWSection).filter(
                LWSection.F_LWLAWID == check_law_id
            ).all()

            print (task_prompt)
            # Create comparison tasks
            for law in existing_laws:
                comparison_task = ComparisonTask(
                    task_id=task_id,
                    new_law_text=task_prompt,
                    existing_law_text=law.SECTIONTEXT
                )
                self.thread_pool.start(comparison_task)
                
        except Exception as e:
            print(f"Error processing task {task_id}: {str(e)}")
            update_task_status(db, task_id, "failed", str(e))
        finally:
            db.close()

    def cleanup(self):
        # Wait for all threads to finish
        self.thread_pool.waitForDone()
