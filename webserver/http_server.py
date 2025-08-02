import json
import os
import random
import string
from datetime import datetime, timedelta
from http import cookies
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import (
    QTcpServer, QHostAddress, QTcpSocket)
from database.crud import create_analysis_task
from database.session import MainSessionLocal

class HttpServer(QObject):
    def __init__(self, session_manager, bridge, port=8080):
        super().__init__()
        self.session_manager = session_manager
        self.bridge = bridge
        self.port = port
        self.tcp_server = QTcpServer()
        self.active_connections = []

    def start(self):
        self.tcp_server.newConnection.connect(self.on_new_connection)
        if self.tcp_server.listen(QHostAddress.Any, self.port):
            print(f"HTTP server listening on port {self.port}")
            return True
        print(f"HTTP server failed: {self.tcp_server.errorString()}")
        return False

    def stop(self):
        print("Stopping HTTP server...")
        # Close all active connections
        for conn in self.active_connections:
            conn.abort()
        self.active_connections.clear()
        
        # Close the server
        self.tcp_server.close()
        print("HTTP server stopped")

    def on_new_connection(self):
        conn = self.tcp_server.nextPendingConnection()
        self.active_connections.append(conn)
        conn.readyRead.connect(lambda: self.handle_request(conn))
        conn.disconnected.connect(lambda: self.handle_disconnect(conn))

    def handle_disconnect(self, conn):
        if conn in self.active_connections:
            self.active_connections.remove(conn)
        conn.deleteLater()

    def handle_request(self, conn: QTcpSocket):
        try:
            data = conn.readAll().data().decode('utf-8')
            parts = data.split('\r\n\r\n', 1)
            headers = parts[0]
            body = parts[1] if len(parts) > 1 else ""

            header_lines = headers.split('\r\n')
            request_line = header_lines[0].split()
            if len(request_line) < 2:
                self.send_error(conn, 400, "Invalid request")
                return

            method, path = request_line[0], request_line[1]
            headers_dict = {}
            for line in header_lines[1:]:
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    headers_dict[key] = value

            if path == "/login" and method == "POST":
                self.handle_login(conn, body, headers_dict)
            elif path == "/logout" and method == "POST":
                self.handle_logout(conn, body, headers_dict)
            elif path == "/api/analyze" and method == "POST":
                self.handle_analyze(conn, body, headers_dict)
            else:
                self.send_error(conn, 404, "Not Found")
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_error(conn, 500, "Internal Server Error")

    def handle_login(self, conn, body, headers):
        try:
            data = json.loads(body)
            username = data['username']
            password = data['password']
        except:
            self.send_error(conn, 400, "Invalid JSON")
            return

        from database.crud import get_user_by_username
        from werkzeug.security import check_password_hash
        
        db = MainSessionLocal()
        try:
            user = get_user_by_username(db, username)
            if user and check_password_hash(user.password_hash, password):
                session_id = self.session_manager.create_session(user.id)
                cookie = cookies.SimpleCookie()
                cookie['session_id'] = session_id
                cookie['session_id']['httponly'] = True
                cookie['session_id']['path'] = '/'
                
                response = json.dumps({"status": "success"})
                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    f"Set-Cookie: {cookie.output(header='').strip()}\r\n"
                    f"Content-Length: {len(response)}\r\n\r\n{response}"
                )
                conn.write(headers.encode())
            else:
                self.send_error(conn, 401, "Invalid credentials")
        except Exception as e:
            print(f"Login error: {e}")
            self.send_error(conn, 500, "Internal Server Error")
        finally:
            db.close()
            conn.disconnectFromHost()

    def handle_logout(self, conn, body, headers):
        cookie_header = headers.get('Cookie', '')
        cookie = cookies.SimpleCookie()
        cookie.load(cookie_header)
        if 'session_id' in cookie:
            session_id = cookie['session_id'].value
            self.session_manager.invalidate_session(session_id)
        
        response = json.dumps({"status": "success"})
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Set-Cookie: session_id=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Path=/\r\n"
            f"Content-Length: {len(response)}\r\n\r\n{response}"
        )
        conn.write(headers.encode())
        conn.disconnectFromHost()

    def handle_analyze(self, conn, body, headers):
        cookie_header = headers.get('Cookie', '')
        cookie = cookies.SimpleCookie()
        cookie.load(cookie_header)
        session_id = cookie.get('session_id').value if 'session_id' in cookie else None
        
        if not session_id or not self.session_manager.get_user_id(session_id):
            self.send_error(conn, 401, "Unauthorized")
            return

        try:
            data = json.loads(body)
            prompt = data['prompt']
            category = data.get('category')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
        except:
            self.send_error(conn, 400, "Invalid request")
            return

        user_id = self.session_manager.get_user_id(session_id)
        db = MainSessionLocal()
        try:
            task = create_analysis_task(
                db, 
                user_id, 
                prompt, 
                category, 
                start_date, 
                end_date
            )
            db.commit()
            
            self.session_manager.map_task_to_session(task.id, session_id)
            self.bridge.add_analysis_task(task.id)
            
            response = json.dumps({"task_id": task.id})
            headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response)}\r\n\r\n{response}"
            )
            conn.write(headers.encode())
        except Exception as e:
            print(f"Analysis task creation error: {e}")
            self.send_error(conn, 500, "Internal Server Error")
        finally:
            db.close()
            conn.disconnectFromHost()

    def send_error(self, conn, code, message):
        response = json.dumps({"error": message})
        conn.write(
            f"HTTP/1.1 {code} {message}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(response)}\r\n\r\n"
            f"{response}".encode()
        )
        conn.disconnectFromHost()