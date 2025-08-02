# http_server.py
from PySide6.QtCore import QObject
from PySide6.QtNetwork import QHostAddress, QTcpServer
from PySide6.QtHttpServer import QHttpServer
from webserver.routers.auth_router import AuthRouter
from webserver.routers.analysis_router import AnalysisRouter

class HttpServer(QObject):
    def __init__(self, session_manager, bridge, port=8080):
        super().__init__()
        self.session_manager = session_manager
        self.bridge = bridge
        self.port = port
        self.server = QHttpServer()
        self.tcp_server = QTcpServer()
        self.routers = []
        self.setup_routers()

    def setup_routers(self):
        # Create and register routers
        auth_router = AuthRouter(self.session_manager, self.bridge)
        analysis_router = AnalysisRouter(self.session_manager, self.bridge)
        
        auth_router.setup_routes(self.server)
        analysis_router.setup_routes(self.server)
        
        # Store references to prevent garbage collection
        self.routers = [auth_router, analysis_router]

    def start(self):
        if self.tcp_server.listen(QHostAddress.Any, self.port):
            print(f"HTTP server listening on port {self.port}")
            self.server.bind(self.tcp_server)
            return True
        print(f"HTTP server failed: {self.tcp_server.errorString()}")
        return False

    def stop(self):
        print("Stopping HTTP server...")
        self.tcp_server.close()
        print("HTTP server stopped")