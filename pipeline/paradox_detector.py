from PySide6.QtCore import QObject, QThreadPool
from database.session import RulesSessionLocal, MainSessionLocal
from database.crud import update_task_status
from database.models import AnalysisTask
from .comparison_task import ComparisonTask

class ParadoxDetector(QObject):
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        self.thread_pool = QThreadPool.globalInstance()
        # Set max threads (e.g., 4-8 depending on system capabilities)
        self.thread_pool.setMaxThreadCount(4)

    def initialize(self):
        # Initialize any resources needed
        pass

    def process_task(self, task_id):
        db = MainSessionLocal()
        db_r = RulesSessionLocal()
        try:
            task = db.query(AnalysisTask).get(task_id)
            if not task:
                print(f"Task {task_id} not found")
                return
            
            # Update task status
            update_task_status(db, task_id, "processing")
            
            # Get relevant laws from database
            existing_laws = []
            # existing_laws = get_laws_by_category_and_date(
            #     db=db,
            #     category=task.category,
            #     start_date=task.start_date,
            #     end_date=task.end_date
            # )
            
            # Create comparison tasks
            for law in existing_laws:
                comparison_task = ComparisonTask(
                    task_id=task_id,
                    new_law_text=task.prompt,
                    existing_law_text=law.text
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
