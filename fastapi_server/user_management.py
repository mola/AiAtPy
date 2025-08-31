# user_management.py
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from database.session import MainSessionLocal
from database.models import User
from fastapi_server.auth import get_current_user, get_password_hash
from pydantic import BaseModel

# Create router
user_router = APIRouter(prefix="/api/users", tags=["users"])

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_admin: bool = False

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: int
    is_admin: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# CRUD functions
def create_user(db, username: str, email: str, password: str, is_admin: bool = False):
    """Create a new user"""
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        if existing_user.username == username:
            raise ValueError("Username already exists")
        else:
            raise ValueError("Email already exists")
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        is_admin=is_admin,
        is_active=1
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def update_user(db, user_id: int, update_data: dict):
    """Update user information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    
    # Check if new username or email already exists (excluding current user)
    if 'username' in update_data:
        existing_user = db.query(User).filter(
            User.username == update_data['username'],
            User.id != user_id
        ).first()
        if existing_user:
            raise ValueError("Username already exists")
    
    if 'email' in update_data:
        existing_user = db.query(User).filter(
            User.email == update_data['email'],
            User.id != user_id
        ).first()
        if existing_user:
            raise ValueError("Email already exists")
    
    # Update fields
    for key, value in update_data.items():
        if key == 'password':
            setattr(user, 'password_hash', get_password_hash(value))
        elif key == 'is_active':
            setattr(user, 'is_active', value)
        elif key == 'is_admin':
            setattr(user, 'is_admin', value)
        else:
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

def delete_user(db, user_id: int):
    """Delete a user and all their sessions"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    
    # First delete all user sessions
    from fastapi_server.auth import terminate_all_sessions
    terminate_all_sessions(user_id)
    
    # Then delete the user
    db.delete(user)
    db.commit()
    return True

def get_all_users(db):
    """Get all users"""
    return db.query(User).all()

def get_user_by_id(db, user_id: int):
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

# API endpoints
@user_router.post("/admin", response_model=UserResponse)
async def create_new_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = MainSessionLocal()
    try:
        new_user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            is_admin=user_data.is_admin
        )
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            is_active=new_user.is_active,
            is_admin=new_user.is_admin,
            created_at=new_user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@user_router.get("/admin", response_model=List[UserResponse])
async def get_all_users_list(current_user: User = Depends(get_current_user)):
    """Get all users (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = MainSessionLocal()
    try:
        users = get_all_users(db)
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at
            )
            for user in users
        ]
    finally:
        db.close()

@user_router.get("/admin/{user_id}", response_model=UserResponse)
async def get_user_details(user_id: int, current_user: User = Depends(get_current_user)):
    """Get user details by ID (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = MainSessionLocal()
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at
        )
    finally:
        db.close()

@user_router.put("/admin/{user_id}", response_model=UserResponse)
async def update_user_details(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user details (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = MainSessionLocal()
    try:
        # Prepare update data
        update_data = {}
        if user_data.username is not None:
            update_data['username'] = user_data.username
        if user_data.email is not None:
            update_data['email'] = user_data.email
        if user_data.password is not None:
            update_data['password'] = user_data.password
        if user_data.is_active is not None:
            update_data['is_active'] = user_data.is_active
        if user_data.is_admin is not None:
            update_data['is_admin'] = user_data.is_admin
        
        updated_user = update_user(db, user_id, update_data)
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            is_active=updated_user.is_active,
            is_admin=updated_user.is_admin,
            created_at=updated_user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@user_router.delete("/admin/{user_id}")
async def delete_user_account(user_id: int, current_user: User = Depends(get_current_user)):
    """Delete a user account (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db = MainSessionLocal()
    try:
        success = delete_user(db, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@user_router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile (non-admin fields only)"""
    db = MainSessionLocal()
    try:
        # Regular users can only update username, email, and password
        update_data = {}
        if user_data.username is not None:
            update_data['username'] = user_data.username
        if user_data.email is not None:
            update_data['email'] = user_data.email
        if user_data.password is not None:
            update_data['password'] = user_data.password
        
        # Non-admin users cannot change is_active or is_admin
        if user_data.is_active is not None and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Cannot change active status")
        if user_data.is_admin is not None and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Cannot change admin status")
        
        # If user is admin, allow updating all fields
        if current_user.is_admin:
            if user_data.is_active is not None:
                update_data['is_active'] = user_data.is_active
            if user_data.is_admin is not None:
                update_data['is_admin'] = user_data.is_admin
        
        updated_user = update_user(db, current_user.id, update_data)
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            is_active=updated_user.is_active,
            is_admin=updated_user.is_admin,
            created_at=updated_user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@user_router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at
    )