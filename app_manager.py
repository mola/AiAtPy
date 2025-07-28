import threading
from PySide6.QtCore import QObject, QTimer
from flask_app import create_flask_app, start_flask
from bridge import Bridge
#from aiatconfig import AiAtConfig

class AppManager(QObject):
    def __init__(self, settings):
        super().__init__()
        self.bridge = None
        self.settings = settings
        self.flask_thread = None
        self.flask_app = None
        self.dummy_timer = None

    def initialize(self):
        self.setup_dummy_timer()
        self.setup_flask()

    def setup_dummy_timer(self):
        self.dummy_timer = QTimer()
        self.dummy_timer.start(1000)  # fire every 1000ms
        self.dummy_timer.timeout.connect(lambda: None)


    def setup_flask(self):
        self.flask_app = create_flask_app(self.settings)
        self.bridge = Bridge()
        self.flask_app.bridge = self.bridge  # Attach bridge to Flask app
        self.flask_thread = threading.Thread(target=start_flask, args=(self.flask_app,), daemon=True)
        self.flask_thread.start()
        print("Flask server started in a separate thread.")

    def cleanup(self):
        pass
