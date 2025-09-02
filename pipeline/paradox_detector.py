from PySide6.QtCore import QObject, QThreadPool, Signal
from database.session import RulesSessionLocal, MainSessionLocal
from database.crud import update_task_status
from database.models import AnalysisTask, ComparisonResult
from .comparison_task import ComparisonTask
from database.models_rules import LWSection
from typing import Dict, List
import json
import time
import numpy as np

class ParadoxDetector(QObject):
    all_comparisons_complete = Signal(int, list)  # task_id, results

    def __init__(self, app_manager, searcher):
        super().__init__()
        self.sections = []
        self.app_manager = app_manager
        self.thread_pool = QThreadPool.globalInstance()
        # Set max threads (e.g., 4-8 depending on system capabilities)
        self.thread_pool.setMaxThreadCount(96)
        self.active_tasks: Dict[int, Dict] = {}
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
            
            self.task_data = task.data
            
            # Update task status
            update_task_status(db, task_id, "processing")
            
            # Send initial log to user
            self.send_log_to_user(task.user_id, f"Starting analysis task {task_id}...")
            
            if self.task_data.get('compare_all', False):
                prompt = self.task_data.get('prompt')
                self.send_log_to_user(task.user_id, f"Searching for relevant sections...")
                search_start = time.time()
                section_ids = self.searcher.get_section_ids(prompt)
                search_end = time.time()
                print("section ids: " , section_ids)
                print(f"---- search time : {search_end - search_start} -----")
                print("ids:" , section_ids)

                # Save the section_ids into task.data
                # Convert section_ids from numpy.int64 to Python int
                section_ids_numpy = [int(section_id) if isinstance(section_id, np.int64) else section_id for section_id in section_ids]
        
                self.task_data['section_ids'] = section_ids_numpy
                task.data = self.task_data
                db.commit()
                print("ids:", section_ids)
                
                # Send search completion log
                self.send_log_to_user(task.user_id, f"Found {len(section_ids)} relevant sections in {search_end - search_start:.2f} seconds")
                
                # Fetch the corresponding ORM models (LWSection instances)
                sections = db_r.query(LWSection).filter(LWSection.ID.in_(section_ids)).all()
                if not sections:
                    error_msg = "No corresponding sections found for comparison."
                    self.send_log_to_user(task.user_id, error_msg)
                    raise ValueError(error_msg)

                print(f"Retrieved sections: {len(sections)}")
                self.send_log_to_user(task.user_id, f"Starting comparison of {len(sections)} sections...")

            else:
                # Case for comparing to one specific law
                law_id = self.task_data.get('check_law_id')
                if not law_id:
                    error_msg = "No law_id specified for comparison"
                    self.send_log_to_user(task.user_id, error_msg)
                    raise ValueError(error_msg)
                
                # Get all sections from the check_law_id
                sections = db_r.query(LWSection).filter(
                    LWSection.F_LWLAWID == law_id
                ).all()

                if not sections:
                    error_msg = f"No sections found for law {law_id}"
                    self.send_log_to_user(task.user_id, error_msg)
                    raise ValueError(error_msg)
                
                self.send_log_to_user(task.user_id, f"Starting comparison of {len(sections)} sections from law {law_id}...")

            # Initialize tracking for this task with its own current_section_index
            self.active_tasks[task_id] = {
                'total': len(sections),
                'completed': 0,
                'processed': 0,
                'current_section_index': 0,  # Each task has its own index
                'user_id': task.user_id,
                'sections': sections  # Store sections per task
            }
            self.start_task_batch(task_id, batch_size=1000)
           
        except Exception as e:
            print(f"Error processing task {task_id}: {str(e)}")
            update_task_status(db, task_id, "failed", str(e))
            if task:
                self.send_log_to_user(task.user_id, f"Task failed: {str(e)}")
        finally:
            db.close()
            db_r.close()

    def start_task_batch(self, task_id, batch_size=1000):
        """Start a batch of tasks from current position in sections for specific task"""
        if task_id not in self.active_tasks:
            return
            
        task_info = self.active_tasks[task_id]
        sections = task_info['sections']
        current_index = task_info['current_section_index']
        
        batch = []
        remaining = len(sections) - current_index
        current_batch_size = min(batch_size, remaining)
        
        prompt = self.task_data.get('prompt', '')
        for i in range(current_batch_size):
            section = sections[current_index]
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
            current_index += 1
        
        # Update the task's current section index
        self.active_tasks[task_id]['current_section_index'] = current_index
        
        # Start all tasks in batch
        for t in batch:
            self.thread_pool.start(t)

    def send_log_to_user(self, user_id: int, message: str):
        """Send log message to user via WebSocket"""
        try:
            if hasattr(self.app_manager, 'send_custom_log_to_user'):
                success = self.app_manager.send_custom_log_to_user(user_id, message)
                if not success:
                    print(f"Failed to send log to user {user_id}: {message}")
        except Exception as e:
            print(f"Error sending log to user {user_id}: {str(e)}")

    def cleanup(self):
        # Wait for all threads to finish
        self.thread_pool.waitForDone()

    def handle_comparison_complete(self, task_id: int, result: dict):
        """Called when a single comparison task completes"""
        if task_id not in self.active_tasks:
            print("Task not found in active tasks")
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
            
            # Send progress update to user every 100 completions or when significant
            user_id = self.active_tasks[task_id]['user_id']
            total = self.active_tasks[task_id]['total']
            completed = self.active_tasks[task_id]['completed']
            
            if completed % 100 == 0 or completed == total:
                progress = (completed / total) * 100
                self.send_log_to_user(user_id, 
                                    f"Progress: {progress:.1f}% ({completed}/{total})")
            
            # Check if we need to start a new batch
            if (self.active_tasks[task_id]['processed'] < total and
                self.active_tasks[task_id]['completed'] < 1000):
                
                # Start another task from the remaining sections
                self.start_task_batch(task_id, batch_size=1)
            
            # Check if all tasks are complete
            if completed >= total:
                user_id = self.active_tasks[task_id]['user_id']
                self.send_log_to_user(user_id, f"Analysis task {task_id} completed successfully!")
                
                self.all_comparisons_complete.emit(task_id, [])
                update_task_status(db, task_id, "completed")
                
                # Clean up task data
                del self.active_tasks[task_id]
                
        except Exception as e:
            db.rollback()
            error_msg = f"Error storing comparison result: {str(e)}"
            print(error_msg)
            update_task_status(db, task_id, "failed", str(e))
            
            # Send error log to user
            if task_id in self.active_tasks:
                user_id = self.active_tasks[task_id]['user_id']
                self.send_log_to_user(user_id, error_msg)
        finally:
            db.close()