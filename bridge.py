# bridge.py
from PySide6.QtCore import QObject, Signal

class Bridge(QObject):
    configUpdated = Signal() # signal for connection config updates
    tagsUpdated = Signal()  # signal for tag updates
    timeSignal = Signal(int) # signal for time updates

    def __init__(self):
        super().__init__()