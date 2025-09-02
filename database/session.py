from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from aiatconfig import AiAtConfig
import os
from passlib.context import CryptContext

# Password hashing context (same as in auth.py)
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def get_password_hash(password):
    """Create a password hash using sha256_crypt"""
    return pwd_context.hash(password)

# Database configuration
DB_CONFIG = {
    'postgresql': {
        'host': '127.0.0.1',
        'port': '5432',
        'user': 'postgres',
        'password': '',
        'database': 'diar',
        'url': 'postgresql://{user}:{password}@{host}:{port}/{database}'
    },
    'sqlite': {
        'url': 'sqlite:///{file}'
    }
}


def get_main_db_url(db_type='postgresql', **kwargs):
    """Get main database URL with optional overrides"""
    config = DB_CONFIG.get(db_type.lower(), DB_CONFIG['postgresql'])
    config.update(kwargs)  # Allow overriding any config parameter
    
    if db_type.lower() == 'sqlite':
        # Set default SQLite file if not provided
        if 'file' not in kwargs:
            config['file'] = 'database.db'
        # Ensure directory exists
        db_dir = os.path.dirname(config['file'])
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    return config['url'].format(**config)

def get_rules_db_url():
    """Always return SQLite URL for rules database"""
    # Ensure directory exists
    if not os.path.exists('rules.db'):
        open('rules.db', 'a').close()
    return 'sqlite:///rules.db'    

# Base classes for each database
MainBase = declarative_base()
RulesBase = declarative_base()

# Create engines
main_engine = create_engine(get_main_db_url('postgresql'))
rules_engine = create_engine(get_rules_db_url())

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
            # Create admin user using sha256_crypt hashing
            from .crud import create_user
            hashed_password = get_password_hash("admin")  # Use consistent hashing
            create_user(
                db, 
                username=admin_username,
                password_hash=hashed_password,
                email="admin@lawanalyzer.ir"
            )
            db.commit()
            print("Admin user created successfully")
            print(f"Admin password hash: {hashed_password}")
        else:
            print("Admin user already exists")
            print(f"Current admin password hash: {admin_user.password_hash}")
            
            # Update existing admin password to use consistent sha256_crypt hashing
            if not admin_user.password_hash.startswith('$2'):  # If not sha256_crypt
                print("Updating admin password to use sha256_crypt...")
                admin_user.password_hash = get_password_hash("admin")
                db.commit()
                print("Admin password updated to sha256_crypt")
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()