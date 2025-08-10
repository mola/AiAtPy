from PySide6.QtCore import QObject, QThreadPool, Signal
from database.session import RulesSessionLocal, MainSessionLocal
from database.crud import update_task_status
from database.models import AnalysisTask, ComparisonResult
from .comparison_task import ComparisonTask
from database.models_rules import LWSection

class Paradox2Detector(QObject):
    all_comparisons_complete = Signal(int, list)  # task_id, results

    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        self.thread_pool = QThreadPool()
        # Set max threads (e.g., 4-8 depending on system capabilities)
        self.thread_pool.setMaxThreadCount(8)
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
                # Extract data from JSON
                law_id = task_data.get('law_id')
                section_no = task_data.get('section_no')
                check_law_id = task_data.get('check_law_id')
                system_prompt = task_data.get('system_prompt')
                merge_sections = task_data.get('merge_sections', False)

                # Get the section text for the current law/section
                current_section = db_r.query(LWSection.SECTIONTEXT).filter(
                    LWSection.F_LWLAWID == law_id,
                    LWSection.SECTIONTYPENO == section_no
                ).first()

                if not current_section:
                    raise ValueError("Section not found")

                task_prompt = current_section.SECTIONTEXT

                # Get all sections from the check_law_id excluding F_LWLAWSTRUCTUREID = 57
                sections = db_r.query(LWSection).filter(
                    LWSection.F_LWLAWID == check_law_id,
                    LWSection.F_LWLAWSTRUCTUREID != 57
                ).all()

                # Create a dictionary to organize sections by parent-child relationships
                section_dict = {section.ID: section for section in sections}

                task_list = []
                counter = 0 
                
                # Create comparison tasks
                for section in sections:
                    if merge_sections:
                        # If merging is enabled, follow parent-child relationship
                        if section.F_PARENTID is None or section.F_PARENTID not in section_dict:
                            # Start with the current section's text
                            combined_text = section.SECTIONTEXT or ""
                            
                            # Find all child sections
                            child_sections = [s for s in sections if s.F_PARENTID == section.ID]
                            
                            # Append child sections' text
                            for child in child_sections:
                                if child.SECTIONTEXT:
                                    combined_text += "\n\n" + child.SECTIONTEXT
                            
                            # Create comparison task with combined text
                            comparison_task = ComparisonTask(
                                task_id=task_id,
                                new_law_text=task_prompt,
                                existing_law_text=combined_text,
                                detector=self,
                                section_data={
                                    'first_law_id': law_id,
                                    'first_section_id': int(section.ID),
                                    'second_law_id': law_id,
                                    'second_section_id': int(section_no),
                                    'system_prompt': system_prompt
                                }
                            )
                            task_list.append(comparison_task)
                    else:
                        # If merging is disabled, treat each section independently
                        comparison_task = ComparisonTask(
                            task_id=task_id,
                            new_law_text=task_prompt,
                            existing_law_text=section.SECTIONTEXT or "",
                            detector=self,
                            section_data={
                                'first_law_id': law_id,
                                'first_section_id': int(section.ID),
                                'second_law_id': law_id,
                                'second_section_id': int(section_no),
                                'system_prompt': system_prompt
                            }
                        )
                        task_list.append(comparison_task)

                # Initialize tracking for this task
                self.active_tasks[task_id] = {
                    'total': len(task_list),
                    'completed': 0
                }
                for t in task_list:
                    self.thread_pool.start(t)
        except Exception as e:
            print(f"Error processing task {task_id}: {str(e)}")
            update_task_status(db, task_id, "failed", str(e))
        finally:
            db.close()

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