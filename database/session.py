from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from aiatconfig import AiAtConfig
from werkzeug.security import generate_password_hash

Base = declarative_base()
engine = create_engine(AiAtConfig.get_db_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

    # Create admin user if doesn't exist
    db = SessionLocal()
    try:
        from .models import User
        from .crud import get_user_by_username
        
        admin_username = "admin"
        admin_user = get_user_by_username(db, admin_username)
        
        if admin_user is None:
            # Create admin user
            from .crud import create_user
            hashed_password = generate_password_hash("admin_password")  # Change to strong password
            create_user(
                db, 
                username=admin_username,
                password_hash=hashed_password,
                email="admin@lawanalyzer.ir"
            )
            db.commit()
            print("Admin user created successfully")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()