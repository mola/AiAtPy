from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, status, Form, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from database.session import MainSessionLocal
from database.crud import get_user_by_username
from database.models import User  # Import User model
from aiatconfig import AiAtConfig
from pydantic import BaseModel
from fastapi import Request

# Password hashing
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# OAuth2 scheme - update tokenUrl if needed
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token", auto_error=False)

# Create router
auth_router = APIRouter(prefix="/api", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    db = MainSessionLocal()
    try:
        user = get_user_by_username(db, username)
        if user and verify_password(password, user.password_hash):
            return user
        return None
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=4)  # 4 hours default
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
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        # Fetch user from DB using user_id
        db = MainSessionLocal()
        user = db.query(User).filter(User.id == int(user_id)).first()
        db.close()
        if user is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@auth_router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None):
    """Login endpoint that accepts form data (OAuth2 compatible)"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Set cookie with the access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=4 * 60 * 60,  # 4 hours in seconds
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/login", response_model=Token)
async def login_with_json(login_request: LoginRequest, response: Response):
    """Login endpoint that accepts JSON data"""
    user = authenticate_user(login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Set cookie with the access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=4 * 60 * 60,  # 4 hours in seconds
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Additional endpoints for compatibility with existing frontend
@auth_router.post("/logout")
async def logout(response: Response):
    """Logout endpoint that clears the access token cookie"""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@auth_router.get("/health")
async def health_check():
    return {"status": "healthy"}

@auth_router.get("/protected")
async def protected(request: Request,current_user: User = Depends(get_current_user)):
    return {"logged_in_as": current_user.username, "user_id": current_user.id}

@auth_router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }

# File upload endpoint (example)
@auth_router.post("/upload")
async def upload_file(current_user: User = Depends(get_current_user)):
    # Implement file upload logic here
    return {"message": "File upload endpoint"}
