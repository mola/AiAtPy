import threading
from PySide6.QtCore import QObject, Slot, QTimer
from bridge import Bridge
from pipeline.paradox_detector import ParadoxDetector
from pipeline.paradox2_detector import Paradox2Detector
from pipeline.rag_detector import EnhancedRAGDetector
from llm_connectors.deepseek_chat import DeepSeekChat
from fastapi_app import create_fastapi_app, get_ssl_context
from fastapi_server.websocket_manager import manager
import asyncio
import datetime
from typing import Optional, List, Dict, Any
class AppManager(QObject):
    def __init__(self, settings,searcher):
        super().__init__()
        self.bridge = Bridge()
        self.settings = settings
        self.fastapi_app = None
        self.paradox_detector = ParadoxDetector(self,searcher)
        self.paradox2_detector = Paradox2Detector(self)
        self.rag_detector = EnhancedRAGDetector(self)
        self.bridge.new_analysis_task.connect(self.handle_new_task)
        self.dummy_timer = None
        self.deepseek_chat = DeepSeekChat()
        self.searcher = searcher

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
        
        # Import and store the WebSocket manager
        self.fastapi_app.state.websocket_manager = manager

        ssl_context = get_ssl_context()

        # Start FastAPI in a separate thread
        import uvicorn
        self.fastapi_thread = threading.Thread(
            target=lambda: uvicorn.run(
                self.fastapi_app,
                host="0.0.0.0",
                port=8000,
                log_level="info",
                ssl_certfile="ssl/cert.pem" if ssl_context else None,
                ssl_keyfile="ssl/key.pem" if ssl_context else None
            ),
            daemon=True
        )
        self.fastapi_thread.start()
        print("FastAPI server started in a separate thread." + (" (HTTPS)" if ssl_context else " (HTTP)"))

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

    @Slot(int)
    def add_rag_task(self, data):
        print(f"New RAG task received task id: {data}")
        self.rag_detector.process_task(data)

    def chat(self, message: str) -> Dict[str, Any]:
        """Send a chat message and get the assistant's response with references"""
        try:
            # Get the response from your chat service
            response_text = self.deepseek_chat.send_message(message)
            
            # Extract references from the response (you'll need to implement this)
            references = self.extract_references(response_text)
            
            return {
                "response": response_text,
                "references": references
            }
        except Exception as e:
            print(f"Error in chat: {str(e)}")
            return {
                "response": "Failed to process your message",
                "references": []
            }


    def extract_references(self, response_text: str) -> List[Dict]:
        """
        Extract references from the response text.
        This is a placeholder - implement your own logic based on your domain.
        """
        references = []
                
        return references
        
    async def send_custom_log_to_user_async(self, user_id: int, log_message: str) -> bool:
        """Async version for use within async contexts"""
        try:
            if not hasattr(self.fastapi_app.state, 'websocket_manager'):
                return False
            
            manager = self.fastapi_app.state.websocket_manager
            
            custom_message = {
                "type": "log",
                "message": log_message,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            
            await manager.send_to_user(user_id, custom_message)
            return True
            
        except Exception as e:
            print(f"Error sending async log to user {user_id}: {str(e)}")
            return False

    def send_custom_log_to_user(self, user_id: int, log_message: str) -> bool:
        """Synchronous wrapper for the async method"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.send_custom_log_to_user_async(user_id, log_message)
            )
            loop.close()
            return result
        except Exception as e:
            print(f"Error in sync wrapper: {str(e)}")
            return False

    def send_dict_to_user(self, user_id: int, message_dict: dict) -> bool:
        """Synchronous wrapper for sending dictionaries directly to user"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.send_dict_to_user_async(user_id, message_dict)
            )
            loop.close()
            return result
        except Exception as e:
            print(f"Error in send_dict_to_user sync wrapper: {str(e)}")
            return False

    async def send_dict_to_user_async(self, user_id: int, message_dict: dict) -> bool:
        """Send a dictionary message directly to a specific user"""
        try:
            await self.fastapi_app.state.websocket_manager.send_to_user(user_id, message_dict)
            return True
        except Exception as e:
            print(f"Error sending dict to user {user_id}: {str(e)}")
            return False

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

    def get_sections_search_results(self, query):
        section_ids = self.searcher.get_section_ids(query)
        return section_ids
