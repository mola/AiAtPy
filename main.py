# main.py
import os
import sys
import signal
import threading
import functools
import asyncio
from PySide6.QtCore import QCoreApplication, QSettings, QTimer

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
    }

    for key, value in defaults.items():
        if not settings.contains(key):
            settings.setValue(key, value)

    settings.sync()

def handle_sigint(signum, frame):
    """Signal handler for SIGINT (Ctrl+C)."""
    print("\nSIGINT received, exiting gracefully...")
    QCoreApplication.quit()

if __name__ == "__main__":
    initialize_settings()
    settings = QSettings(os.path.join(CONF_DIR, "settings.ini"), QSettings.IniFormat)

    init_db()
    
    qt_app = QCoreApplication([])
    app_manager = AppManager(settings)
    app_manager.initialize()

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_sigint)
    
    # Set up a timer to periodically check for signals
    # (Qt doesn't always handle signals immediately in event loop)
    timer = QTimer()
    timer.start(500)  # Check every 500ms
    timer.timeout.connect(lambda: None)  # Let the event loop process events

    try:
        print("Starting application event loop...")
        ret = qt_app.exec()
        print(f"Application exited with code {ret}")
    except Exception as e:
        print(f"Exception in Qt event loop: {e}")
    finally:
        app_manager.cleanup()
        print("Application terminated.")
