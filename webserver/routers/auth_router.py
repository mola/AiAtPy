# routers/auth_router.py
import json
from .base_router import BaseRouter
from PySide6.QtCore import Slot
from PySide6.QtHttpServer import QHttpServer, QHttpServerRequest, QHttpServerResponse
from database.crud import get_user_by_username
from werkzeug.security import check_password_hash

class AuthRouter(BaseRouter):
    def setup_routes(self, server):
        server.route("/login", self.handle_login)
        server.route("/logout", self.handle_logout)
    
    @Slot(QHttpServerRequest)
    def handle_login(self, request):

        # Only handle POST requests
        if request.method() != QHttpServerRequest.Method.Post:
            return QHttpServerResponse("Method not allowed", 
                                       QHttpServerResponse.StatusCode.MethodNotAllowed)
        try:
            data = request.body().data().decode('utf-8')
            json_data = json.loads(data)
            username = json_data.get('username')
            password = json_data.get('password')
        except:
            return QHttpServerResponse("Invalid JSON", 
                                       QHttpServerResponse.StatusCode.BadRequest)

        db = MainSessionLocal()
        try:
            user = get_user_by_username(db, username)
            if user and check_password_hash(user.password_hash, password):
                session_id = self.session_manager.create_session(user.id)
                
                response = QHttpServerResponse("application/json", 
                                              b'{"status":"success"}')
                response.setHeader("Set-Cookie", 
                    f"session_id={session_id}; HttpOnly; Path=/; SameSite=Lax")
                return response
            return QHttpServerResponse("Invalid credentials", 
                                       QHttpServerResponse.StatusCode.Unauthorized)
        except Exception as e:
            print(f"Login error: {e}")
            return QHttpServerResponse("Internal Server Error", 
                                       QHttpServerResponse.StatusCode.InternalServerError)
        finally:
            db.close()

    @Slot(QHttpServerRequest)
    def handle_logout(self, request):
        
        # Only handle POST requests
        if request.method() != QHttpServerRequest.Method.Post:
            return QHttpServerResponse("Method not allowed", 
                                       QHttpServerResponse.StatusCode.MethodNotAllowed)
        session_id = self.get_session_id(request)
        if session_id:
            self.session_manager.invalidate_session(session_id)
        
        response = QHttpServerResponse("application/json", 
                                      b'{"status":"success"}')
        response.setHeader("Set-Cookie", 
            "session_id=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Path=/")
        return response