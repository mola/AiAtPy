import time
from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, JSON,Boolean
from database.session import MainBase

class User(MainBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive
    is_admin = Column(Boolean, default=False)

class UserSession(MainBase):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    expires_at = Column(BigInteger, nullable=False)
    is_active = Column(Boolean, default=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
class AnalysisTask(MainBase):
    __tablename__ = 'analysis_tasks'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    data = Column(JSON)
    status = Column(String(20), default='pending')
    result = Column(Text)
    created_at = Column(BigInteger, default=lambda: int(time.time()))  # Current Unix timestamp

class ComparisonResult(MainBase):
    __tablename__ = 'comparison_results'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False, index=True)
    first_law_id = Column(Integer, nullable=False)
    first_section_id = Column(Integer, nullable=False)
    second_law_id = Column(Integer)
    second_section_id = Column(Integer)
    response = Column(JSON)
    contradiction = Column(Boolean)
    finish_time = Column(BigInteger, default=lambda: int(time.time())) 