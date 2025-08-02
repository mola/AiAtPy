# routers/base_router.py
from PySide6.QtCore import Slot
from PySide6.QtHttpServer import QHttpServer, QHttpServerRequest, QHttpServerResponse
from database.session import MainSessionLocal

class BaseRouter:
    def __init__(self, session_manager, bridge):
        self.session_manager = session_manager
        self.bridge = bridge
    
    def setup_routes(self, server):
        """Override this method to register routes"""
        pass
    
    def get_session_id(self, request):
        """Extract session ID from request cookies"""
        cookie_header = request.value("Cookie")
        if not cookie_header:
            return None
        
        cookies = cookie_header.split(';')
        for cookie in cookies:
            if 'session_id' in cookie:
                return cookie.split('=')[1].strip()
        return None
    
    def require_auth(self, request):
        """Middleware for authentication"""
        session_id = self.get_session_id(request)
        if not session_id or not self.session_manager.get_user_id(session_id):
            return QHttpServerResponse("Unauthorized", 
                                       QHttpServerResponse.StatusCode.Unauthorized)
        return session_id

    def require_method(self, request, allowed_methods):
        """Check if request method is allowed"""
        if request.method() not in allowed_methods:
            allowed = ", ".join([m.name.decode() for m in allowed_methods])
            return QHttpServerResponse(
                f"Method not allowed. Allowed: {allowed}",
                QHttpServerResponse.StatusCode.MethodNotAllowed
            )
        return None