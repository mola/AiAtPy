import threading
from PySide6.QtCore import QObject, Slot, QTimer
from flask_app import create_flask_app, start_flask
from bridge import Bridge
from pipeline.paradox_detector import ParadoxDetector
from pipeline.paradox2_detector import Paradox2Detector

class AppManager(QObject):
    def __init__(self, settings):
        super().__init__()
        self.bridge = Bridge()
        self.settings = settings
        self.flask_thread = None
        self.flask_app = None
        self.paradox_detector = ParadoxDetector(self)
        self.paradox2_detector = Paradox2Detector(self)
        self.bridge.new_analysis_task.connect(self.handle_new_task)
        self.dummy_timer = None

    def initialize(self):
        self.setup_dummy_timer()
        self.setup_flask()
        # Initialize other components
        self.paradox_detector.initialize()

    def setup_dummy_timer(self):
        self.dummy_timer = QTimer()
        self.dummy_timer.start(1000)  # fire every 1000ms
        self.dummy_timer.timeout.connect(lambda: None)


    def setup_flask(self):
        self.flask_app = create_flask_app(self.settings)
        self.flask_app.app_manager = self  # Make AppManager accessible to Flask
        self.flask_app.bridge = self.bridge
        

        # Configure JWT
        from flask_server.auth import configure_jwt
        configure_jwt(self.flask_app)
        
        self.flask_thread = threading.Thread(target=start_flask, args=(self.flask_app,), daemon=True)
        self.flask_thread.start()
        print("Flask server started in a separate thread.")

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
        # Cleanup resources
        self.paradox_detector.cleanup()
