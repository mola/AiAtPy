import threading
from PySide6.QtCore import QObject, Slot
from flask_app import create_flask_app, start_flask
from bridge import Bridge
from database.session import SessionLocal
from database.crud import get_laws_by_category_and_date, update_task_status
from pipeline.paradox_detector import ParadoxDetector

class AppManager(QObject):
    def __init__(self, settings):
        super().__init__()
        self.bridge = Bridge()
        self.settings = settings
        self.flask_thread = None
        self.flask_app = None
        self.paradox_detector = ParadoxDetector(self)
        self.bridge.new_analysis_task.connect(self.handle_new_task)

    def initialize(self):
        self.setup_flask()
        # Initialize other components
        self.paradox_detector.initialize()

    def setup_flask(self):
        self.flask_app = create_flask_app(self.settings)
        self.flask_app.app_manager = self  # Make AppManager accessible to Flask
        self.flask_app.bridge = self.bridge
        
        # Register blueprints
        from flask_server import routes as api_routes
        self.flask_app.register_blueprint(api_routes.bp)
        
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

    def cleanup(self):
        # Cleanup resources
        self.paradox_detector.cleanup()