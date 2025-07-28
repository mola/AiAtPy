from flask_jwt_extended import JWTManager
from werkzeug.security import check_password_hash
from database.crud import get_user_by_username
from database.session import SessionLocal
from database.models import User
from aiatconfig import AiAtConfig

jwt = JWTManager()

def configure_jwt(app):
    app.config["JWT_SECRET_KEY"] =  AiAtConfig.get_jwt_secret()
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour
    app.config["JWT_IDENTITY_CLAIM"] = "sub"
    jwt.init_app(app)

def authenticate_user(username, password):
    db = SessionLocal()
    try:
        user = get_user_by_username(db, username)
        print("user " , user.password_hash)
        print("psw " , password)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
    finally:
        db.close()

@jwt.user_identity_loader
def user_identity_lookup(user):
    """Convert user object to identity string"""
    print("user-----------" , user)
    return str(user.id)  # Ensure we return a string

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Convert identity string back to user object"""
    identity = jwt_data["sub"]
    
    if not identity:
        return None
        
    try:
        user_id = int(identity)
    except ValueError:
        return None
        
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()