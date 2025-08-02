# routers/analysis_router.py
import json
from .base_router import BaseRouter
from PySide6.QtCore import Slot
from PySide6.QtHttpServer import QHttpServer, QHttpServerRequest, QHttpServerResponse
from database.crud import create_analysis_task

class AnalysisRouter(BaseRouter):
    def setup_routes(self, server):
        server.route("/api/analyze", self.handle_analyze)
        server.route("/api/tasks", self.handle_get_tasks)
        server.route("/api/tasks/<arg>", self.handle_get_task)
    
    @Slot(QHttpServerRequest)
    def handle_analyze(self, request):

        # Check HTTP method
        method_check = self.require_method(request, [QHttpServerRequest.Method.Post])
        if method_check:
            return method_check

        # Authentication middleware
        auth_result = self.require_auth(request)
        if isinstance(auth_result, QHttpServerResponse):
            return auth_result
        session_id = auth_result

        try:
            data = request.body().data().decode('utf-8')
            json_data = json.loads(data)
            prompt = json_data.get('prompt')
            category = json_data.get('category')
            start_date = json_data.get('start_date')
            end_date = json_data.get('end_date')
        except:
            return QHttpServerResponse("Invalid request", 
                                       QHttpServerResponse.StatusCode.BadRequest)

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
            
            return QHttpServerResponse("application/json", 
                                       json.dumps({"task_id": task.id}).encode())
        except Exception as e:
            print(f"Analysis task creation error: {e}")
            return QHttpServerResponse("Internal Server Error", 
                                       QHttpServerResponse.StatusCode.InternalServerError)
        finally:
            db.close()

    @Slot(QHttpServerRequest)
    def handle_get_tasks(self, request):

        # Check HTTP method
        method_check = self.require_method(request, [QHttpServerRequest.Method.Get])
        if method_check:
            return method_check

        # Authentication middleware
        auth_result = self.require_auth(request)
        if isinstance(auth_result, QHttpServerResponse):
            return auth_result
        session_id = auth_result

        # Implementation for getting all tasks
        # ...

    @Slot(QHttpServerRequest, str)
    def handle_get_task(self, request, task_id):

        # Check HTTP method
        method_check = self.require_method(request, [QHttpServerRequest.Method.Get])
        if method_check:
            return method_check
            
        # Authentication middleware
        auth_result = self.require_auth(request)
        if isinstance(auth_result, QHttpServerResponse):
            return auth_result
        session_id = auth_result

        # Implementation for getting a specific task
        # ...