from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
import json
from datetime import datetime
from sqlalchemy import func, delete
from pydantic import BaseModel

from database.session import MainSessionLocal, RulesSessionLocal
from database.crud import create_analysis_task
from database.models import AnalysisTask, ComparisonResult, User
from database.models_rules import LWSection, LWLaw
from fastapi_server.auth import get_current_user
from utilities.persian_embedding import PersianEmbeddingSearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tasks"])

# Initialize embedding search
embedding_search = PersianEmbeddingSearch()

# Pydantic models for request/response
class SearchSimilarRequest(BaseModel):
    query_text: str
    k: Optional[int] = 20

class AnalyzeLawRequest(BaseModel):
    prompt: str
    check_law_id: str
    prompt_title: Optional[str] = None
    system_prompt: Optional[str] = None
    topic_ids: Optional[List[int]] = None

class AnalyzeRulesRequest(BaseModel):
    law_id: int
    section_no: str
    check_law_id: str
    topic_ids: Optional[List[int]] = None

class TaskResponse(BaseModel):
    task_id: int
    status: str
    created_at: datetime
    results: List[dict]
    latest_timestamp: int

class TaskListItem(BaseModel):
    task_id: int
    type: str
    compare_all: bool
    check_law_id: str
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None
    result: Optional[dict] = None
    title: Optional[str] = None

@router.post("/search_similar")
async def search_similar(
    request: SearchSimilarRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for similar sections using embedding search
    """
    if not request.query_text:
        raise HTTPException(status_code=400, detail="query_text is required")
    
    try:
        distances, indices = embedding_search.find_similar(request.query_text, request.k)
        return {
            "status": "success",
            "distances": distances.tolist(),
            "indices": indices.tolist()
        }
    except Exception as e:
        logger.exception("Error in similarity search")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_law(
    request: AnalyzeLawRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze custom law text
    """
    db = MainSessionLocal()
    try:
        # Store all relevant data in JSON format
        task_data = {
            "type": "custom",
            "prompt": request.prompt,
            "prompt_title": request.prompt_title,
            "system_prompt": request.system_prompt,
            "check_law_id": request.check_law_id,
            "compare_all": request.check_law_id == "*",
            "topic_ids": request.topic_ids
        }
        
        task = create_analysis_task(
            db=db,
            user_id=current_user.id,
            data=task_data
        )
        
        # Pass to AppManager (assuming it's available in app state)
        # app.state.app_manager.add_analysis_task(task.id)
        
        return {
            "message": "Custom law analysis started",
            "task_id": task.id
        }
    except Exception as e:
        logger.exception("Error creating analysis task")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/analyze_rules")
async def analyze_rules(
    request: AnalyzeRulesRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze existing law sections
    """
    db = MainSessionLocal()
    try:
        # Store all relevant data in JSON format
        task_data = {
            "type": "existing",
            "law_id": request.law_id,
            "section_no": request.section_no,
            "check_law_id": request.check_law_id,
            "compare_all": request.check_law_id == "*",
            "topic_ids": request.topic_ids
        }
        
        task = create_analysis_task(
            db=db,
            user_id=current_user.id,
            data=task_data
        )
        
        # Pass to AppManager
        # app.state.app_manager.add_analysis_rules_task(task.id)
        
        return {
            "message": "Existing law analysis started",
            "task_id": task.id
        }
    except Exception as e:
        logger.exception("Error creating analysis task")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/task/{task_id}")
async def get_task_status(
    task_id: int,
    since_timestamp: Optional[int] = Query(None),
    contradiction_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get task status and results
    """
    db = MainSessionLocal()
    db_r = RulesSessionLocal()
    
    try:
        # Get the main task
        task = db.query(AnalysisTask).filter(
            AnalysisTask.id == task_id,
            AnalysisTask.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Query comparison results with optional timestamp and contradiction filter
        results_query = db.query(ComparisonResult).filter(
            ComparisonResult.task_id == task_id
        )

        if since_timestamp is not None:
            results_query = results_query.filter(
                ComparisonResult.finish_time > since_timestamp
            )
        
        if contradiction_filter is not None:
            if contradiction_filter.lower() == 'true':
                results_query = results_query.filter(
                    ComparisonResult.contradiction == True
                )
            elif contradiction_filter.lower() == 'false':
                results_query = results_query.filter(
                    ComparisonResult.contradiction == False
                )
        
        comparison_results = results_query.order_by(
            ComparisonResult.finish_time.asc()
        ).all()
        
        # Format results as array of JSON objects with additional captions
        results_data = []

        for result in comparison_results:
            # Get first section caption
            first_section = db_r.query(LWSection.FULLPATH).filter(
                LWSection.ID == result.first_section_id
            ).first()
            first_section_caption = first_section.FULLPATH if first_section else None

            # Get second section caption
            second_section = db_r.query(LWSection.FULLPATH).filter(
                LWSection.ID == result.second_section_id
            ).first()
            second_section_caption = second_section.FULLPATH if second_section else None

            # Get first law caption
            first_law = db_r.query(LWLaw.CAPTION).filter(
                LWLaw.ID == result.first_law_id
            ).first()
            first_law_caption = first_law.CAPTION if first_law else None

            # Get second law caption
            second_law = db_r.query(LWLaw.CAPTION).filter(
                LWLaw.ID == result.second_law_id
            ).first()
            second_law_caption = second_law.CAPTION if second_law else None

            # Extract why from response JSON
            why_value = result.response.get('why', '') if result.response else ''
            
            results_data.append({
                'id': result.id,
                'first_law_id': result.first_law_id,
                'first_law_caption': first_law_caption,
                'first_section_id': result.first_section_id,
                'first_section_caption': first_section_caption,
                'second_law_id': result.second_law_id,
                'second_law_caption': second_law_caption,
                'second_section_id': result.second_section_id,
                'second_section_caption': second_section_caption,
                'response': why_value,
                'contradiction': result.contradiction,
                'finish_time': result.finish_time
            })
        
        # Get the latest timestamp for client-side tracking
        latest_timestamp = max(
            [r.finish_time for r in comparison_results] or [0]
        )
        
        return {
            "task_id": task.id,
            "status": task.status,
            "data": task.data,
            "created_at": task.created_at,
            "results": results_data,
            "latest_timestamp": latest_timestamp
        }
    finally:
        db.close()
        db_r.close()

@router.get("/tasks")
async def get_tasks(current_user: User = Depends(get_current_user)):
    """
    Get all tasks for the current user
    """
    db = MainSessionLocal()
    db_r = RulesSessionLocal()
    try:
        # Get all tasks for the current user
        tasks = db.query(AnalysisTask).filter(
            AnalysisTask.user_id == current_user.id
        ).order_by(AnalysisTask.created_at.desc()).all()
        
        tasks_data = []
        for task in tasks:
            # Parse task data JSON
            task_json = task.data if task.data else {}
            
            # Get the latest finish time from comparison results
            latest_comparison = db.query(
                func.max(ComparisonResult.finish_time)
            ).filter(
                ComparisonResult.task_id == task.id
            ).scalar()
            
            # Determine title based on task type
            title = None
            if task_json.get('type') == 'custom':
                title = task_json.get('prompt_title')
            elif task_json.get('type') == 'existing':
                law_id = task_json.get('law_id')
                if law_id:
                    law = db_r.query(LWLaw.CAPTION).filter(
                        LWLaw.ID == law_id
                    ).first()
                    title = law.CAPTION if law else None
            
            tasks_data.append({
                'task_id': task.id,
                'type': task_json.get('type'),
                'compare_all': task_json.get('compare_all', False),
                'check_law_id': task_json.get('check_law_id'),
                'status': task.status,
                'created_at': task.created_at,
                'finished_at': latest_comparison,
                'result': task.result,
                'title': title
            })
        
        return tasks_data
    finally:
        db.close()
        db_r.close()

@router.delete("/task/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a task and all its comparison results
    """
    db = MainSessionLocal()
    
    try:
        # First verify the task exists and belongs to the current user
        task = db.query(AnalysisTask).filter(
            AnalysisTask.id == task_id,
            AnalysisTask.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Delete all comparison results for this task
        delete_comparison_stmt = delete(ComparisonResult).where(
            ComparisonResult.task_id == task_id
        )
        db.execute(delete_comparison_stmt)
        
        # Delete the task itself
        db.delete(task)
        
        # Commit the transaction
        db.commit()
        
        return {
            "message": "Task and all related comparison results deleted successfully",
            "task_id": task_id
        }
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error deleting task {task_id}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")
    finally:
        db.close()