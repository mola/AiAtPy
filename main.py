# main.py
import os
import sys
import signal
from PySide6.QtCore import QCoreApplication, QSettings

# FIRST: Set up configuration paths
CONF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf")
os.makedirs(CONF_DIR, exist_ok=True)

MAIN_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")
RULES_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")
os.makedirs(MAIN_DB_DIR, exist_ok=True)

# SECOND: Initialize AiAtConfig before any other imports
from aiatconfig import AiAtConfig
AiAtConfig.set_conf_dir(CONF_DIR)
AiAtConfig.set_conf_dbdir(MAIN_DB_DIR)

# Force initialization of settings
AiAtConfig.initialize_config()

# NOW it's safe to import other modules that might depend on AiAtConfig
from database.session import init_db
from app_manager import AppManager

def initialize_settings():
    """Initialize QSettings with default values"""
    settings_path = os.path.join(CONF_DIR, "settings.ini")
    settings = QSettings(settings_path, QSettings.IniFormat)

    defaults = {
        "flask/secret_key": "your_secret_key_here",
        "flask/static_folder": os.path.join("frontend", "build"),
    }

    for key, value in defaults.items():
        if not settings.contains(key):
            settings.setValue(key, value)

    settings.sync()

def sigint_handler(sig, frame):
    print("\nShutting down gracefully...")
    app_manager.cleanup()
    qt_app.quit()

def run():
    global qt_app, app_manager

    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)

    try:
        qt_app.exec()
    except Exception as e:
        print(f"Exception in Qt event loop: {e}")
    finally:
        app_manager.cleanup()
        print("Application terminated.")

if __name__ == "__main__":
    initialize_settings()
    settings = QSettings(os.path.join(CONF_DIR, "settings.ini"), QSettings.IniFormat)

    init_db()
    
    qt_app = QCoreApplication([])
    app_manager = AppManager(settings)
    app_manager.initialize()

    run()
