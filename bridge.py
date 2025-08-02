# bridge.py
from PySide6.QtCore import QObject, Signal
from queue import Queue

class Bridge(QObject):
    new_analysis_task = Signal(int)  # task_id
    task_completed = Signal(int, str)  # task_id, result
    
    def __init__(self):
        super().__init__()
        self.task_queue = Queue()
    
    def add_analysis_task(self, task_id):
        self.task_queue.put(task_id)
        self.new_analysis_task.emit(task_id)
    
    def get_next_task(self):
        try:
            return self.task_queue.get_nowait()
        except:
            return None