# main.py
import os
import sys
import signal
import threading
import functools
import asyncio
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
from flask_server.websocket_manager import WebSocketManager
import websockets

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

# Global to hold manager and loop
websocket_loop = None
websocket_thread = None

def start_websocket_server():
    global websocket_loop
    websocket_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(websocket_loop)

    manager = WebSocketManager()
    port = 8001

    # In start_websocket_server() function:
    async def websocket_handler(websocket):
        await manager.handler(websocket)  # Now only one argument

    async def server():
        async with websockets.serve(
            websocket_handler, "", port
        ):
            print(f"WebSocket server running on ws://localhost:{port}/ws")
            await asyncio.Future()  # Run forever

    websocket_loop.run_until_complete(server())
    websocket_loop.run_forever()



def sigint_handler(sig, frame):
    print("\nShutting down gracefully...")
    if websocket_loop and websocket_loop.is_running():
        websocket_loop.call_soon_threadsafe(websocket_loop.stop)
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
        if websocket_thread and websocket_thread.is_alive():
            websocket_thread.join()
        app_manager.cleanup()
        print("Application terminated.")

if __name__ == "__main__":
    initialize_settings()
    settings = QSettings(os.path.join(CONF_DIR, "settings.ini"), QSettings.IniFormat)

    init_db()
    
    qt_app = QCoreApplication([])
    app_manager = AppManager(settings)
    app_manager.initialize()


    # Start WebSocket server in background thread
    websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
    websocket_thread.start()

    run()
