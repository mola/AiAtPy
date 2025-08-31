import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request, status, Form, Body, Query, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, List, Union
from database.session import MainSessionLocal
from database.crud import get_user_by_username
from fastapi_server.auth import auth_router, get_current_user, oauth2_scheme
from fastapi_server.rules import router as rules_router
from fastapi_server.routers import router as tasks_router
from fastapi_server.websocket_manager import manager
from fastapi_server.user_management import user_router
from aiatconfig import AiAtConfig
from database.models import User
import logging
import datetime
import asyncio
import ssl
from jose import JWTError, jwt  # Add this import

logger = logging.getLogger(__name__)

def create_fastapi_app(settings):
    app = FastAPI(title="Diar API", 
    version="1.0.0",
    description="DIAR Application API Documentation",
    )
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173",
                       "http://127.0.0.1:5173",
                       "http://localhost:8000",
                       "http://127.0.0.1:8000",
                       ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(rules_router)
    app.include_router(tasks_router)
    app.include_router(user_router)
    
    # Store the WebSocket manager in app state for access from AppManager
    app.state.websocket_manager = manager

    # Get static folder path
    static_folder = settings.value("flask/static_folder", "frontend")
    static_path = Path(static_folder)
    
    # Mount static files if the directory exists
    if static_path.exists() and static_path.is_dir():
        app.mount("/static", StaticFiles(directory=static_folder), name="static")
    
    # Serve frontend files
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Check if the file exists in static folder
        file_path = static_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Serve index.html for SPA routing
        index_path = static_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="File not found")

    @app.get("/sample-function")
    async def sample_function():
        # A simple example endpoint
        return {
            "status": "ok",
            "time_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "note": "This is a sample HTTP endpoint"
        }

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
        try:
            # Verify token first
            if not token:
                await websocket.close(code=1008, reason="Token required")
                return
            
            try:
                # Decode token and validate session
                payload = jwt.decode(token, AiAtConfig.get_jwt_secret(), algorithms=["HS256"])
                user_id = payload.get("sub")
                session_id = payload.get("sid")
                
                if not user_id or not session_id:
                    await websocket.close(code=1008, reason="Invalid token")
                    return
                
                # Validate session
                from fastapi_server.auth import validate_session
                if not validate_session(session_id):
                    await websocket.close(code=1008, reason="Session expired")
                    return
                    
            except JWTError:
                await websocket.close(code=1008, reason="Invalid token")
                return
            
            # Create a simple request-like object for auth
            class WebSocketRequest:
                def __init__(self, token):
                    self.cookies = {"access_token": token}
                    self.headers = {}
            
            # Use your existing auth function
            user = await get_current_user(WebSocketRequest(token), token)
            
            if not user:
                await websocket.close(code=1008, reason="Invalid token")
                return
                
            user_id = user.id
            
            # Connect using manager (this handles accept() and connection tracking)
            await manager.connect(websocket, user_id)
            logger.info(f"User {user_id} connected via WebSocket")
            
            try:
                while True:
                    try:
                        # Wait for message with timeout
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        
                        # Process the received data
                        await websocket.send_json({"echo": data, "length": len(data)})
                        
                    except asyncio.TimeoutError:
                        # Send ping to check connection health
                        try:
                            await websocket.send_json({"type": "ping"})
                        except:
                            break  # Connection failed
                            
            except WebSocketDisconnect:
                logger.info(f"User {user_id} disconnected normally")
            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {str(e)}")
            finally:
                # Use manager's disconnect method for proper cleanup
                manager.disconnect(user_id)
                
        except HTTPException as auth_err:
            logger.warning(f"WebSocket authentication failed: {str(auth_err)}")
            try:
                await websocket.close(code=1008, reason="Authentication failed")
            except:
                pass  # Already closed
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket: {str(e)}")
            try:
                await websocket.close(code=1011, reason="Internal error")
            except:
                pass
    return app

def get_ssl_context():
    """Create SSL context for HTTPS"""
    # Path to your SSL certificate and key files
    cert_file = "ssl/cert.pem"
    key_file = "ssl/key.pem"
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_file, key_file)
        return ssl_context
    else:
        logger.warning("SSL certificate files not found. Using HTTP instead.")
        return None

async def get_db():
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()