from PySide6.QtCore import QObject, QThreadPool, Signal
from database.session import RulesSessionLocal, MainSessionLocal
from database.crud import update_task_status
from database.models import AnalysisTask,ComparisonResult
from .comparison_task import ComparisonTask
from database.models_rules import LWSection
from typing import Dict, List
import json
import time

class ParadoxDetector(QObject):
    all_comparisons_complete = Signal(int, list)  # task_id, results

    def __init__(self, app_manager,searcher):
        super().__init__()
        self.sections = []
        self.app_manager = app_manager
        self.thread_pool = QThreadPool.globalInstance()
        # Set max threads (e.g., 4-8 depending on system capabilities)
        self.thread_pool.setMaxThreadCount(32)
        self.active_tasks: Dict[int, Dict] = {}
        self.current_section_index = 0
        self.task_data = None
        self.searcher = searcher

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
            
            self.task_data  = task.data
            
            # Update task status
            update_task_status(db, task_id, "processing")
            
            if self.task_data.get('compare_all', False):
                # TODO: Implement logic for comparing to all laws
                print("Comparing to all laws - implementation pending")
                prompt = self.task_data.get('prompt')
                search_start = time.time()
                section_ids = self.searcher.get_section_ids(prompt)
                search_end = time.time()
                print(f"---- search time : {search_end - search_start} -----")
                print("ids:" , section_ids)
                # Fetch the corresponding ORM models (LWSection instances)
                self.sections = db_r.query(LWSection).filter(LWSection.ID.in_(section_ids)).all()
                if not self.sections:
                    raise ValueError("No corresponding sections found for comparison.")

                print(f"Retrieved sections: {len(self.sections)}")

                # update_task_status(db, task_id, "completed", "All laws comparison not yet implemented")
                # self.sections = db_r.query(LWSection).filter(
                #     LWSection.FULLPATH.ilike(f"%ماده%")
                # ).all()

            else:
                # Case for comparing to one specific law
                law_id = self.task_data.get('check_law_id')
                if not law_id:
                    raise ValueError("No law_id specified for comparison")
                
                # Get all sections from the check_law_id
                self.sections = db_r.query(LWSection).filter(
                    LWSection.F_LWLAWID == law_id
                ).all()

                if not self.sections:
                    raise ValueError(f"No sections found for law {law_id}")

            # Initialize tracking for this task
            self.active_tasks[task_id] = {
                'total': len(self.sections),
                'completed': 0,
                'processed': 0
            }
            self.start_task_batch(task_id, batch_size=1000)
           
        except Exception as e:
            print(f"Error processing task {task_id}: {str(e)}")
            update_task_status(db, task_id, "failed", str(e))
        finally:
            db.close()
            db_r.close()

    def start_task_batch(self, task_id, batch_size=1000):
        """Start a batch of tasks from current position in sections"""
        batch = []
        remaining = len(self.sections) - self.current_section_index
        current_batch_size = min(batch_size, remaining)
        
        prompt=self.task_data.get('prompt', '')
        for i in range(current_batch_size):
            section = self.sections[self.current_section_index]
            comparison_task = ComparisonTask(
                task_id=task_id,
                new_law_text=prompt,
                existing_law_text=section.SECTIONTEXT,
                section_data={
                    'first_law_id': int(section.F_LWLAWID),
                    'first_section_id': int(section.ID),
                    'second_law_id': None,
                    'second_section_id': None
                }
            )
            comparison_task.comparisonComplete.connect(self.handle_comparison_complete)
            batch.append(comparison_task)
            self.current_section_index += 1
        
        # Start all tasks in batch
        for t in batch:
            self.thread_pool.start(t)

    def cleanup(self):
        # Wait for all threads to finish
        self.thread_pool.waitForDone()

    def handle_comparison_complete(self, task_id: int, result: dict):
        """Called when a single comparison task completes"""
        if task_id not in self.active_tasks:
            print("Not Finished but return ")
            return

        # Store the result in the database immediately
        db = MainSessionLocal()
        try:
            comparison_result = ComparisonResult(
                task_id=task_id,
                first_law_id=result['first_law_id'],
                first_section_id=result['first_section_id'],
                second_law_id=result.get('second_law_id'),
                second_section_id=result.get('second_section_id'),
                response=result['reason'],
                contradiction=result['contradiction']
            )
            db.add(comparison_result)
            db.commit()
            
            # Track completion
            self.active_tasks[task_id]['completed'] += 1
            self.active_tasks[task_id]['processed'] += 1
            
            # Check if we need to start a new batch
            if (self.active_tasks[task_id]['processed'] < 
                self.active_tasks[task_id]['total'] and
                self.active_tasks[task_id]['completed'] < 1000):
                
                # Start another task from the remaining sections
                self.start_task_batch(task_id, batch_size=1)
            
            # Check if all tasks are complete
            if (self.active_tasks[task_id]['completed'] >= self.active_tasks[task_id]['total']):
                
                self.all_comparisons_complete.emit(task_id, [])
                update_task_status(db, task_id, "completed")
                del self.active_tasks[task_id]
                self.current_section_index = 0
                
        except Exception as e:
            db.rollback()
            print(f"Error storing comparison result: {str(e)}")
            update_task_status(db, task_id, "failed", str(e))
        finally:
            db.close()