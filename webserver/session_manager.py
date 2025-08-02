# webserver/server.py
import json
import os
import random
import string
from datetime import datetime, timedelta
from http import cookies
from PySide6.QtCore import QObject, Signal, Slot

class SessionManager(QObject):
    def __init__(self):
        super().__init__()
        self.sessions = {}
        self.session_to_websocket = {}
        self.task_to_session = {}

    def create_session(self, user_id):
        session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        expires = datetime.now() + timedelta(hours=1)
        self.sessions[session_id] = {
            "user_id": user_id,
            "expires": expires
        }
        return session_id

    def get_user_id(self, session_id):
        session = self.sessions.get(session_id)
        if session and session['expires'] > datetime.now():
            return session['user_id']
        return None

    def invalidate_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def associate_websocket(self, session_id, websocket):
        self.session_to_websocket[session_id] = websocket

    def remove_websocket(self, session_id):
        if session_id in self.session_to_websocket:
            del self.session_to_websocket[session_id]

    def map_task_to_session(self, task_id, session_id):
        self.task_to_session[task_id] = session_id

    def get_websocket_for_task(self, task_id):
        session_id = self.task_to_session.get(task_id)
        if session_id:
            return self.session_to_websocket.get(session_id)
        return None

    def remove_task_mapping(self, task_id):
        if task_id in self.task_to_session:
            del self.task_to_session[task_id]