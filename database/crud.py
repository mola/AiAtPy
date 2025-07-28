from sqlalchemy.orm import Session
from database.models import Law, User, AnalysisTask
from datetime import datetime

def create_law(db: Session, title: str, text: str, category: str, enactment_date: datetime):
    db_law = Law(
        title=title,
        text=text,
        category=category,
        enactment_date=enactment_date
    )
    db.add(db_law)
    db.commit()
    db.refresh(db_law)
    return db_law

def get_laws_by_category_and_date(db: Session, category: str, start_date: int = None, end_date: int = None):
    query = db.query(Law).filter(Law.category == category)
    
    if start_date:
        # Convert Unix timestamp to datetime for comparison
        start_dt = datetime.utcfromtimestamp(start_date)
        query = query.filter(Law.enactment_date >= start_dt)
    
    if end_date:
        # Convert Unix timestamp to datetime for comparison
        end_dt = datetime.utcfromtimestamp(end_date)
        query = query.filter(Law.enactment_date <= end_dt)
    
    return query.all()

def create_user(db: Session, username: str, password_hash: str, email: str = None):
    db_user = User(
        username=username,
        password_hash=password_hash,
        email=email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_analysis_task(db: Session, user_id: int, prompt: str, category: str = None, 
                         start_date: str = None, end_date: str = None):
    # Convert date strings to Unix timestamps
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp()) if start_date else None
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()) if end_date else None
    
    db_task = AnalysisTask(
        user_id=user_id,
        prompt=prompt,
        category=category,
        start_date=start_ts,
        end_date=end_ts
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task_status(db: Session, task_id: int, status: str, result: str = None):
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if task:
        task.status = status
        if result:
            task.result = result
        db.commit()
        return task
    return None