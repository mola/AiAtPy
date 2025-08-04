from PySide6.QtCore import QObject, QThreadPool, Signal
from database.session import RulesSessionLocal, MainSessionLocal
from database.crud import update_task_status
from database.models import AnalysisTask,ComparisonResult
from .comparison_task import ComparisonTask
from database.models_rules import LWSection
from typing import Dict, List
import json

class ParadoxDetector(QObject):
    all_comparisons_complete = Signal(int, list)  # task_id, results

    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        self.thread_pool = QThreadPool.globalInstance()
        # Set max threads (e.g., 4-8 depending on system capabilities)
        self.thread_pool.setMaxThreadCount(4)
        self.active_tasks: Dict[int, Dict] = {}

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
            
            task_data = task.data
            
            # Update task status
            update_task_status(db, task_id, "processing")
            
            if task_data.get('compare_all', False):
                # TODO: Implement logic for comparing to all laws
                print("Comparing to all laws - implementation pending")
                update_task_status(db, task_id, "completed", "All laws comparison not yet implemented")
            else:
                # Case for comparing to one specific law
                law_id = task_data.get('check_law_id')
                if not law_id:
                    raise ValueError("No law_id specified for comparison")
                
                # Get all sections from the check_law_id
                sections = db_r.query(LWSection).filter(
                    LWSection.F_LWLAWID == law_id
                ).all()

                if not sections:
                    raise ValueError(f"No sections found for law {law_id}")

                # Initialize tracking for this task
                self.active_tasks[task_id] = {
                    'total': len(sections),
                    'completed': 0
                }

                # Create comparison tasks
                for section in sections:
                    comparison_task = ComparisonTask(
                        task_id=task_id,
                        new_law_text=task_data.get('prompt', ''),
                        existing_law_text=section.SECTIONTEXT,
                        detector=self,  # Pass reference to detector
                        section_data={
                            'first_law_id': law_id,
                            'first_section_id': int(section.ID),
                            'second_law_id': None,
                            'second_section_id': None
                        }
                    )
                    self.thread_pool.start(comparison_task)
                
                # update_task_status(db, task_id, "completed", f"Comparison tasks created for {len(sections)} sections")
                
        except Exception as e:
            print(f"Error processing task {task_id}: {str(e)}")
            update_task_status(db, task_id, "failed", str(e))
        finally:
            db.close()
            db_r.close()

    def cleanup(self):
        # Wait for all threads to finish
        self.thread_pool.waitForDone()

    def handle_comparison_complete(self, task_id: int, result: dict):
        """Called when a single comparison task completes"""
        if task_id not in self.active_tasks:
            return

        # Store the result in the database immediately
        db = MainSessionLocal()
        try:
            # Create new ComparisonResult record
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

            # Check if all tasks are complete
            if (self.active_tasks[task_id]['completed'] >= 
                self.active_tasks[task_id]['total']):
                
                # All tasks complete, emit signal
                self.all_comparisons_complete.emit(task_id, [])
                
                # Update main task status (no results in JSON anymore)
                update_task_status(db, task_id, "completed")
                
                # Clean up
                del self.active_tasks[task_id]
        except Exception as e:
            db.rollback()
            print(f"Error storing comparison result: {str(e)}")
            update_task_status(db, task_id, "failed", str(e))
        finally:
            db.close()