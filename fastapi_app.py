import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request, status, Form, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, List, Union
from database.session import MainSessionLocal
from database.crud import get_user_by_username
from fastapi_server.auth import auth_router
from fastapi_server.rules import router as rules_router
from fastapi_server.routers import router as tasks_router
from aiatconfig import AiAtConfig
from database.models import User


def create_fastapi_app(settings):
    app = FastAPI(title="AIAT API", version="1.0.0")
    
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


    # Get static folder path
    static_folder = settings.value("flask/static_folder", "frontend")
    static_path = Path(static_folder)
    
    # Mount static files if the directory exists
    if static_path.exists() and static_path.is_dir():
        app.mount("/static", StaticFiles(directory=static_folder), name="static")
    
    # # Serve frontend files
    # @app.get("/{full_path:path}")
    # async def serve_frontend(full_path: str):
    #     # Check if the file exists in static folder
    #     file_path = static_path / full_path
    #     if file_path.exists() and file_path.is_file():
    #         return FileResponse(file_path)
        
    #     # Serve index.html for SPA routing
    #     index_path = static_path / "index.html"
    #     if index_path.exists():
    #         return FileResponse(index_path)
        
    #     raise HTTPException(status_code=404, detail="File not found")


    return app


async def get_db():
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()