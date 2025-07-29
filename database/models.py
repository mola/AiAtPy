import time
from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, JSON
from database.session import Base

class Law(Base):
    __tablename__ = 'laws'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    category = Column(JSON)
    enactment_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive

class AnalysisTask(Base):
    __tablename__ = 'analysis_tasks'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    category = Column(String(100))
    start_date = Column(BigInteger)  # Store as Unix timestamp
    end_date = Column(BigInteger)    # Store as Unix timestamp
    status = Column(String(20), default='pending')
    result = Column(Text)
    created_at = Column(BigInteger, default=lambda: int(time.time()))  # Current Unix timestamp
