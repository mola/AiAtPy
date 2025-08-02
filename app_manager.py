import threading
from PySide6.QtCore import QObject, Slot, QTimer
from bridge import Bridge
from pipeline.paradox_detector import ParadoxDetector
from pipeline.paradox2_detector import Paradox2Detector
from webserver.http_server import HttpServer
from webserver.websocket_server import WebSocketServer
from webserver.session_manager import SessionManager

class AppManager(QObject):
    def __init__(self, settings):
        super().__init__()
        self.bridge = Bridge()
        self.settings = settings
        self.paradox_detector = ParadoxDetector(self)
        self.paradox2_detector = Paradox2Detector(self)
        self.session_manager = SessionManager()
        self.http_server = None
        self.ws_server = None
        
        self.bridge.new_analysis_task.connect(self.handle_new_task)
        self.dummy_timer = None

    def initialize(self):
        print("Initializing application...")
        self.setup_dummy_timer()
        
        # Initialize servers
        self.http_server = HttpServer(
            self.session_manager, 
            self.bridge, 
            self.settings.value("http_port", 8080)
        )
        self.ws_server = WebSocketServer(
            self.session_manager, 
            self.bridge, 
            self.settings.value("ws_port", 8081)
        )
        
        # Start servers
        if not self.http_server.start():
            print("Failed to start HTTP server")
        if not self.ws_server.start():
            print("Failed to start WebSocket server")
        
        # Initialize other components
        self.paradox_detector.initialize()
        print("Application initialized")

    def setup_dummy_timer(self):
        self.dummy_timer = QTimer()
        self.dummy_timer.start(1000)  # fire every 1000ms
        self.dummy_timer.timeout.connect(lambda: None)

    def add_analysis_task(self, task_id):
        """Add a new analysis task to be processed"""
        print(f"Adding analysis task to queue: {task_id}")
        self.bridge.add_analysis_task(task_id)
        
    @Slot(int)
    def handle_new_task(self, task_id):
        print(f"New analysis task received: {task_id}")
        self.paradox_detector.process_task(task_id)

    @Slot(int)
    def add_analysis_rules_task(self, data):
        print(f"New analysis task received: {data}")
        self.paradox2_detector.process_task(data)

    def cleanup(self):
        print("Cleaning up application...")

        # Stop servers first
        if self.http_server:
            self.http_server.stop()
        if self.ws_server:
            self.ws_server.stop()

        # Cleanup resources
        if self.dummy_timer:
            self.dummy_timer.stop()
            self.dummy_timer.deleteLater()
            self.dummy_timer = None

        self.paradox_detector.cleanup()
        print("Application cleanup complete")
