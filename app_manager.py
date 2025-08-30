import threading
from PySide6.QtCore import QObject, Slot, QTimer
from bridge import Bridge
from pipeline.paradox_detector import ParadoxDetector
from pipeline.paradox2_detector import Paradox2Detector
from llm_connectors.deepseek_chat import DeepSeekChat
from fastapi_app import create_fastapi_app  # Import the function

class AppManager(QObject):
    def __init__(self, settings):
        super().__init__()
        self.bridge = Bridge()
        self.settings = settings
        self.fastapi_app = None
        self.paradox_detector = ParadoxDetector(self)
        self.paradox2_detector = Paradox2Detector(self)
        self.bridge.new_analysis_task.connect(self.handle_new_task)
        self.dummy_timer = None
        self.deepseek_chat = DeepSeekChat()

    def initialize(self):
        self.setup_dummy_timer()
        self.setup_fastapi()
        # Initialize other components
        self.paradox_detector.initialize()

    def setup_dummy_timer(self):
        self.dummy_timer = QTimer()
        self.dummy_timer.start(1000)  # fire every 1000ms
        self.dummy_timer.timeout.connect(lambda: None)

    def setup_fastapi(self):
        self.fastapi_app = create_fastapi_app(self.settings)
        self.fastapi_app.state.app_manager = self  # Make AppManager accessible to FastAPI
        
        # Start FastAPI in a separate thread
        import uvicorn
        self.fastapi_thread = threading.Thread(
            target=lambda: uvicorn.run(
                self.fastapi_app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            ),
            daemon=True
        )
        self.fastapi_thread.start()
        print("FastAPI server started in a separate thread.")

    def add_analysis_task(self, task_id):
        """Add a new analysis task to be processed"""
        print(f"Adding analysis task to queue: {task_id}")
        self.bridge.add_analysis_task(task_id)
        
    @Slot(int)
    def handle_new_task(self, task_id):
        print(f"New analysis task received task id: {task_id}")
        self.paradox_detector.process_task(task_id)

    @Slot(int)
    def add_analysis_rules_task(self, data):
        print(f"New analysis task received task id: {data}")
        self.paradox2_detector.process_task(data)

    def chat(self, msg):
        """Send a chat message and get the assistant's response"""
        try:
            response = self.deepseek_chat.send_message(msg)
            return {
                "status": "success",
                "message": response
            }
        except Exception as e:
            print(f"Error in chat: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to process your message"
            }

    def chat_reset(self):
        """Reset the chat conversation history"""
        try:
            self.deepseek_chat.reset()
            return {
                "status": "success",
                "message": "Conversation reset successfully"
            }
        except Exception as e:
            print(f"Error resetting chat: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to reset conversation"
            }

    def cleanup(self):
        # Cleanup resources
        self.paradox_detector.cleanup()