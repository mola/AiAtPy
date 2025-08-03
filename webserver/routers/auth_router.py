# routers/auth_router.py
import json
from .base_router import BaseRouter
from PySide6.QtCore import Slot, QByteArray
from PySide6.QtNetwork import QHttpHeaders
from PySide6.QtHttpServer import QHttpServer, QHttpServerRequest, QHttpServerResponse, QHttpServerResponder
from database.session import MainSessionLocal
from database.crud import get_user_by_username
from werkzeug.security import check_password_hash

class AuthRouter(BaseRouter):
    def setup_routes(self, server):

        self.handle_login = self._handle_login
        self.handle_logout = self._handle_logout
        server.route("/login", self.handle_login)
        server.route("/logout", self.handle_logout)
    
    @Slot(QHttpServerRequest)
    def _handle_login(self, request):

        # Only handle POST requests
        if request.method() != QHttpServerRequest.Method.Post:
            return QHttpServerResponse("Method not allowed", 
                                       QHttpServerResponder.StatusCode.MethodNotAllowed)
        try:
            data = request.body().data().decode('utf-8')
            json_data = json.loads(data)
            username = json_data.get('username')
            password = json_data.get('password')
            print("got the details -- " , username , password)
        except:
            print(f"JSON parsing error: {e}")
            return QHttpServerResponse("Invalid JSON", 
                                       QHttpServerResponder.StatusCode.BadRequest)

        db = MainSessionLocal()
        try:
            user = get_user_by_username(db, username)
            print("got user ", user)
            if user and check_password_hash(user.password_hash, password):
                print("valid login")
                session_id = self.session_manager.create_session(user.id)
                
                # Create response
                response_data = json.dumps({"status": "success"}).encode('utf-8')
                response = QHttpServerResponse(
                    QByteArray(response_data),
                    QHttpServerResponder.StatusCode.Ok
                )
                
                # Create headers and set them
                headers = QHttpHeaders()
                headers.append("Content-Type", "application/json")
                headers.append("Set-Cookie", f"session_id={session_id}; HttpOnly; Path=/; SameSite=Lax")
                response.setHeaders(headers)
                
                print("--response---" , response)
                return response

            return QHttpServerResponse("Invalid credentials", 
                                       QHttpServerResponder.StatusCode.Unauthorized)
        except Exception as e:
            print(f"Login error: {e}")
            return QHttpServerResponse("Internal Server Error", 
                                       QHttpServerResponder.StatusCode.InternalServerError)
        finally:
            db.close()

    @Slot(QHttpServerRequest)
    def _handle_logout(self, request):
        
        # Only handle POST requests
        if request.method() != QHttpServerRequest.Method.Post:
            return QHttpServerResponse("Method not allowed", 
                                       QHttpServerResponder.StatusCode.MethodNotAllowed)
        session_id = self.get_session_id(request)
        if session_id:
            self.session_manager.invalidate_session(session_id)
        
        # Create response
        response_data = json.dumps({"status": "success"}).encode('utf-8')
        response = QHttpServerResponse(
            QByteArray(response_data),
            QHttpServerResponder.StatusCode.Ok
        )
        
        # Create headers and set them
        headers = QHttpHeaders()
        headers.append("Content-Type", "application/json")
        headers.append("Set-Cookie", "session_id=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Path=/")
        response.setHeaders(headers)
        
        return response

    def create_error_response(self, message, status):
        """Create an error response with consistent formatting"""
        response_data = json.dumps({"error": message}).encode('utf-8')
        return QHttpServerResponse(
            QByteArray(response_data),
            status
        )