from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from aiatconfig import AiAtConfig
from werkzeug.security import generate_password_hash

# Base classes for each database
MainBase = declarative_base()
RulesBase = declarative_base()

# Create engines
main_engine = create_engine(AiAtConfig.get_db_url())
rules_engine = create_engine("sqlite:///rules.db")

MainSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=main_engine)
RulesSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=rules_engine)

def init_db():
    # Create all tables in both databases
    MainBase.metadata.create_all(bind=main_engine)
    # RulesBase.metadata.create_all(bind=rules_engine)


    # Create admin user if doesn't exist
    db = MainSessionLocal()
    try:
        from .models import User
        from .crud import get_user_by_username
        
        admin_username = "admin"
        admin_user = get_user_by_username(db, admin_username)
        
        if admin_user is None:
            # Create admin user
            from .crud import create_user
            hashed_password = generate_password_hash("admin")  # Change to strong password
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
