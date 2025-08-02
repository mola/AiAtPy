# webserver/server.py
import json
import os
import string
from http import cookies
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import (
    QTcpServer, QHostAddress, QTcpSocket)
from PySide6.QtWebSockets import QWebSocket, QWebSocketServer
from database.session import MainSessionLocal

class WebSocketServer(QObject):
    task_completed = Signal(int, str)  # task_id, result

    def __init__(self, session_manager, bridge, port=8081):
        super().__init__()
        self.session_manager = session_manager
        self.bridge = bridge
        self.port = port
        self.ws_server = QWebSocketServer(
            "LawAnalyzer", QWebSocketServer.NonSecureMode
        )
        self.active_connections = []
        self.bridge.task_completed.connect(self.send_task_result)

    def start(self):
        if self.ws_server.listen(QHostAddress.Any, self.port):
            print(f"WebSocket server listening on port {self.port}")
            self.ws_server.newConnection.connect(self.on_new_connection)
            return True
        print(f"WebSocket server failed: {self.ws_server.errorString()}")
        return False

    def stop(self):
        print("Stopping WebSocket server...")
        # Close all active connections
        for conn in self.active_connections:
            conn.close(QWebSocket.CloseCodeGoingAway, "Server shutting down")
        self.active_connections.clear()
        
        # Close the server
        self.ws_server.close()
        print("WebSocket server stopped")

    def on_new_connection(self):
        websocket = self.ws_server.nextPendingConnection()
        self.active_connections.append(websocket)
        request = websocket.request()
        
        cookie_bytes = request.rawHeader("Cookie")
        cookie_header = cookie_bytes.data().decode() if not cookie_bytes.isEmpty() else ""
        
        session_id = None
        if cookie_header:
            try:
                cookie = cookies.SimpleCookie()
                cookie.load(cookie_header)
                session_id = cookie.get('session_id').value if 'session_id' in cookie else None
            except Exception as e:
                print(f"Cookie parsing error: {e}")

        if session_id and self.session_manager.get_user_id(session_id):
            self.session_manager.associate_websocket(session_id, websocket)
            websocket.textMessageReceived.connect(
                lambda msg: self.handle_message(websocket, msg)
            )
            websocket.disconnected.connect(
                lambda: self.handle_disconnect(websocket, session_id)
            )
            websocket.sendTextMessage("CONNECTED")
        else:
            websocket.close(QWebSocket.CloseCodeNormal, "Unauthorized")

    def handle_message(self, websocket, message):
        # Optional: Handle incoming WebSocket messages
        # For now, just log and respond with acknowledgment
        print(f"Received WebSocket message: {message}")
        websocket.sendTextMessage("ACK")

    def handle_disconnect(self, websocket, session_id):
        self.session_manager.remove_websocket(session_id)
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        websocket.deleteLater()

    @Slot(int, str)
    def send_task_result(self, task_id, result):
        websocket = self.session_manager.get_websocket_for_task(task_id)
        if websocket:
            try:
                message = json.dumps({
                    "type": "result",
                    "task_id": task_id,
                    "data": result
                })
                websocket.sendTextMessage(message)
                
                # Update task status in database
                db = MainSessionLocal()
                try:
                    update_task_status(db, task_id, "completed", result)
                    db.commit()
                except Exception as e:
                    print(f"Error updating task status: {e}")
                finally:
                    db.close()
            except Exception as e:
                print(f"Error sending task result: {e}")
        self.session_manager.remove_task_mapping(task_id)