from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from database.session import MainSessionLocal
from database.crud import get_user_by_username
from database.models import User, UserSession
from aiatconfig import AiAtConfig
from pydantic import BaseModel
from fastapi import Request
import time
import uuid

# Password hashing
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token", auto_error=False)

# Create router
auth_router = APIRouter(prefix="/api", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class SessionInfo(BaseModel):
    session_id: str
    created_at: int
    expires_at: int
    is_active: bool
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    db = MainSessionLocal()
    try:
        user = get_user_by_username(db, username)
        if user and verify_password(password, user.password_hash) and user.is_active == 1:
            return user
        return None
    finally:
        db.close()

def generate_session_id():
    return str(uuid.uuid4())

def create_user_session(user_id: int, user_agent: Optional[str] = None, ip_address: Optional[str] = None) -> str:
    """Create a new session"""
    db = MainSessionLocal()
    try:
        # For admin users, terminate all existing sessions first
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_admin:
            db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({"is_active": False})
        
        # Create new session
        session_id = generate_session_id()
        expires_at = int(time.time()) + (4 * 60 * 60)  # 4 hours from now
        
        new_session = UserSession(
            user_id=user_id,
            session_id=session_id,
            expires_at=expires_at,
            is_active=True,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        db.add(new_session)
        db.commit()
        
        return session_id
    finally:
        db.close()

def validate_session(session_id: str) -> bool:
    """Check if session is valid and not expired"""
    db = MainSessionLocal()
    try:
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return False
        
        # Check if session is expired
        current_time = int(time.time())
        if current_time > session.expires_at:
            # Mark session as inactive
            session.is_active = False
            db.commit()
            return False
        
        return True
    finally:
        db.close()

def get_user_sessions(user_id: int) -> List[UserSession]:
    """Get all active sessions for a user"""
    db = MainSessionLocal()
    try:
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).all()
        return sessions
    finally:
        db.close()

def terminate_session(session_id: str, user_id: int) -> bool:
    """Terminate a specific session"""
    db = MainSessionLocal()
    try:
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user_id
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            return True
        return False
    finally:
        db.close()

def terminate_all_sessions(user_id: int):
    """Terminate all sessions for a user"""
    db = MainSessionLocal()
    try:
        db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).update({"is_active": False})
        db.commit()
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=4)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, AiAtConfig.get_jwt_secret(), algorithm="HS256")
    return encoded_jwt

async def get_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    if token is None:
        # Fallback to cookie if no header
        token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    try:
        payload = jwt.decode(token, AiAtConfig.get_jwt_secret(), algorithms=["HS256"])
        user_id: str = payload.get("sub")
        session_id: str = payload.get("sid")
        
        if user_id is None or session_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        
        # Validate the session
        if not validate_session(session_id):
            raise HTTPException(status_code=401, detail="Session expired or invalid")
        
        # Fetch user from DB
        db = MainSessionLocal()
        user = db.query(User).filter(User.id == int(user_id)).first()
        db.close()
        
        if user is None or user.is_active != 1:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
            
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@auth_router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None, request: Request = None):
    """Login endpoint that accepts form data"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Get user agent and IP address for session tracking
    user_agent = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    
    # Create new session (admin users will automatically terminate existing sessions)
    session_id = create_user_session(user.id, user_agent, ip_address)
    
    # Create access token with session ID
    access_token = create_access_token(data={"sub": str(user.id), "sid": session_id})
    
    # Set cookie with the access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=4 * 60 * 60,
        samesite="none",
        secure=True
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/login", response_model=Token)
async def login_with_json(login_request: LoginRequest, response: Response, request: Request):
    """Login endpoint that accepts JSON data"""
    user = authenticate_user(login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Get user agent and IP address for session tracking
    user_agent = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    
    # Create new session (admin users will automatically terminate existing sessions)
    session_id = create_user_session(user.id, user_agent, ip_address)
    
    # Create access token with session ID
    access_token = create_access_token(data={"sub": str(user.id), "sid": session_id})
    
    # Set cookie with the access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=4 * 60 * 60,
        samesite="none",
        secure=True
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/sessions", response_model=List[SessionInfo])
async def get_my_sessions(current_user: User = Depends(get_current_user)):
    """Get all active sessions for the current user"""
    sessions = get_user_sessions(current_user.id)
    return [
        SessionInfo(
            session_id=session.session_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_active=session.is_active,
            user_agent=session.user_agent,
            ip_address=session.ip_address
        )
        for session in sessions
    ]

@auth_router.delete("/sessions/{session_id}")
async def terminate_my_session(session_id: str, current_user: User = Depends(get_current_user)):
    """Terminate a specific session (user can only terminate their own sessions)"""
    success = terminate_session(session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session terminated successfully"}

@auth_router.post("/sessions/terminate-all")
async def terminate_all_my_sessions(current_user: User = Depends(get_current_user)):
    """Terminate all sessions for the current user"""
    terminate_all_sessions(current_user.id)
    return {"message": "All sessions terminated successfully"}

# Add these functions to handle permanent session deletion
def delete_session(session_id: str, user_id: int) -> bool:
    """Permanently delete a specific session"""
    db = MainSessionLocal()
    try:
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user_id
        ).first()
        
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    finally:
        db.close()

def delete_all_sessions(user_id: int):
    """Permanently delete all sessions for a user"""
    db = MainSessionLocal()
    try:
        db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        db.commit()
    finally:
        db.close()

# Add these new API endpoints after the existing session management endpoints

@auth_router.delete("/sessions/{session_id}/delete")
async def delete_my_session(session_id: str, current_user: User = Depends(get_current_user)):
    """Permanently delete a specific session (user can only delete their own sessions)"""
    success = delete_session(session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted permanently"}

@auth_router.post("/sessions/delete-all")
async def delete_all_my_sessions(current_user: User = Depends(get_current_user)):
    """Permanently delete all sessions for the current user"""
    delete_all_sessions(current_user.id)
    return {"message": "All sessions deleted permanently"}

# Admin endpoints for permanent deletion
@auth_router.delete("/admin/sessions/{user_id}/{session_id}/delete")
async def delete_user_session_admin(user_id: int, session_id: str, current_user: User = Depends(get_current_user)):
    """Permanently delete a specific session for a user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = delete_session(session_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted permanently"}

@auth_router.post("/admin/sessions/{user_id}/delete-all")
async def delete_all_user_sessions_admin(user_id: int, current_user: User = Depends(get_current_user)):
    """Permanently delete all sessions for a user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    delete_all_sessions(user_id)
    return {"message": "All sessions deleted permanently"}

@auth_router.post("/logout")
async def logout(response: Response, request: Request,current_user: User = Depends(get_current_user)):
    """Logout endpoint that clears the current session"""
    # Get session ID from token
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    if not token:
        token = request.cookies.get("access_token")
    
    if token:
        try:
            payload = jwt.decode(token, AiAtConfig.get_jwt_secret(), algorithms=["HS256"])
            session_id = payload.get("sid")
            if session_id:
                terminate_session(session_id, current_user.id)
        except JWTError:
            pass
    
    # Clear the cookie
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@auth_router.post("/force-logout")
async def force_logout(current_user: User = Depends(get_current_user)):
    """Force logout from all devices (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    terminate_all_sessions(current_user.id)
    return {"message": "All sessions terminated successfully"}

# Admin endpoints for managing all user sessions
@auth_router.get("/admin/sessions/{user_id}", response_model=List[SessionInfo])
async def get_user_sessions_admin(user_id: int, current_user: User = Depends(get_current_user)):
    """Get all sessions for a specific user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    sessions = get_user_sessions(user_id)
    return [
        SessionInfo(
            session_id=session.session_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_active=session.is_active,
            user_agent=session.user_agent,
            ip_address=session.ip_address
        )
        for session in sessions
    ]

@auth_router.delete("/admin/sessions/{user_id}/{session_id}")
async def terminate_user_session_admin(user_id: int, session_id: str, current_user: User = Depends(get_current_user)):
    """Terminate a specific session for a user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = terminate_session(session_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session terminated successfully"}

@auth_router.post("/admin/sessions/{user_id}/terminate-all")
async def terminate_all_user_sessions_admin(user_id: int, current_user: User = Depends(get_current_user)):
    """Terminate all sessions for a user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    terminate_all_sessions(user_id)
    return {"message": "All sessions terminated successfully"}

@auth_router.get("/health")
async def health_check():
    return {"status": "healthy"}

@auth_router.get("/protected")
async def protected(current_user: User = Depends(get_current_user)):
    return {"logged_in_as": current_user.username, "user_id": current_user.id, "is_admin": current_user.is_admin}

@auth_router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

# Add session cleanup function
def cleanup_expired_sessions():
    """Remove expired sessions"""
    db = MainSessionLocal()
    try:
        current_time = int(time.time())
        db.query(UserSession).filter(
            UserSession.expires_at < current_time,
            UserSession.is_active == True
        ).update({"is_active": False})
        db.commit()
    finally:
        db.close()