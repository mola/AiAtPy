# routers/auth_router.py

import json
from http import cookies
from .base_router import BaseRouter

from PySide6.QtCore import Slot, QByteArray
from PySide6.QtNetwork import QHttpHeaders
from PySide6.QtHttpServer import (
    QHttpServerRequest,
    QHttpServerResponse,
    QHttpServerResponder,
)

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
    def _handle_login(self, request: QHttpServerRequest):
        if request.method() != QHttpServerRequest.Method.Post:
            return QHttpServerResponse(
                "Method not allowed", QHttpServerResponder.StatusCode.MethodNotAllowed
            )

        try:
            data = request.body().data().decode("utf-8")
            json_data = json.loads(data)
            username = json_data.get("username")
            password = json_data.get("password")
        except Exception as e:
            print(f"JSON parsing error: {e}")
            return QHttpServerResponse(
                "Invalid JSON", QHttpServerResponder.StatusCode.BadRequest
            )

        db = MainSessionLocal()
        try:
            user = get_user_by_username(db, username)
            if user and check_password_hash(user.password_hash, password):
                print("valid login")
                session_id = self.session_manager.create_session(user.id)

                cookie = cookies.SimpleCookie()
                cookie["session_id"] = session_id
                cookie["session_id"]["httponly"] = True
                cookie["session_id"]["path"] = "/"

                response_body = QByteArray(
                    json.dumps({"status": "success"}).encode("utf-8")
                )
                response = QHttpServerResponse(
                    response_body, QHttpServerResponder.StatusCode.Forbidden
                )
                
                headers = QHttpHeaders()
                headers.append("Content-Type", "application/json")
                headers.append("Set-Cookie", cookie.output(header="", sep="").strip())
                response.setHeaders(headers)
                
                print(str(response))
                return response

            return QHttpServerResponse(
                "Invalid credentials", QHttpServerResponder.StatusCode.Unauthorized
            )
        except Exception as e:
            print(f"Login error: {e}")
            return QHttpServerResponse(
                "Internal Server Error",
                QHttpServerResponder.StatusCode.InternalServerError,
            )
        finally:
            db.close()

    @Slot(QHttpServerRequest)
    def _handle_logout(self, request: QHttpServerRequest):
        if request.method() != QHttpServerRequest.Method.Post:
            return QHttpServerResponse(
                "Method not allowed", QHttpServerResponder.StatusCode.MethodNotAllowed
            )

        # Parse cookie to find session_id
        cookie_header = request.headers().value("Cookie")
        if cookie_header:
            cookie = cookies.SimpleCookie()
            cookie.load(cookie_header)
            if "session_id" in cookie:
                session_id = cookie["session_id"].value
                self.session_manager.invalidate_session(session_id)

        # Expire the cookie
        expired_cookie = (
            "session_id=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Path=/"
        )

        response_body = QByteArray(
            json.dumps({"status": "success"}).encode("utf-8")
        )
        response = QHttpServerResponse(
            response_body, QHttpServerResponder.StatusCode.Ok
        )

        headers = QHttpHeaders()
        headers.append("Content-Type", "application/json")
        headers.append("Set-Cookie", expired_cookie)
        response.setHeaders(headers)

        return response
