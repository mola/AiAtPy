from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime

from database.session import MainSessionLocal
from database.models import User, ChatSession, ChatMessage, ChatFeedback
from fastapi_server.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Pydantic Models
class ChatRequest(BaseModel):
    msg: str
    session_id: Optional[int] = None

class FeedbackRequest(BaseModel):
    message_id: int
    rating: bool  # True=like, False=dislike
    feedback_text: Optional[str] = None

class SessionTitleRequest(BaseModel):
    title: str

class SessionSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

class MessageResponse(BaseModel):
    id: int
    is_user: bool
    content: str
    timestamp: datetime
    liked: Optional[bool] = None
    references: Optional[List[Dict]] = None

class SessionDetails(BaseModel):
    id: int
    title: str
    messages: List[MessageResponse]
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/message")
async def send_chat_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a chat message - creates new session if no active session
    """
    try:
        db = MainSessionLocal()
        
        # Get or create active session
        if chat_request.session_id:
            session = db.query(ChatSession).filter(
                ChatSession.id == chat_request.session_id,
                ChatSession.user_id == current_user.id
            ).first()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            session = db.query(ChatSession).filter(
                ChatSession.user_id == current_user.id,
                ChatSession.is_active == True
            ).first()
            
            if not session:
                session = ChatSession(
                    user_id=current_user.id,
                    title=chat_request.msg[:50] + "..." if len(chat_request.msg) > 50 else chat_request.msg,
                    is_active=True
                )
                db.add(session)
                db.flush()
        
        # Get response from AppManager
        app_manager = request.app.state.app_manager
        response_data = app_manager.chat(chat_request.msg)
        response_text = response_data if isinstance(response_data, str) else response_data.get('response', '')
        references = []
        
        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            user_id=current_user.id,
            message=chat_request.msg,
            is_user_message=True,
            created_at=datetime.now()
        )
        db.add(user_message)
        
        # Save AI response
        ai_response = ChatMessage(
            session_id=session.id,
            user_id=current_user.id,
            message="",
            response=response_text,
            is_user_message=False,
            references=references,
            created_at=datetime.now()
        )
        db.add(ai_response)
        
        # Update session timestamp
        session.updated_at = datetime.now()
        
        db.commit()
        
        return JSONResponse(status_code=200, content={
            "session_id": session.id,
            "message_id": ai_response.id,
            "response": response_text,
            "references": references
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")
    finally:
        db.close()

@router.post("/feedback")
async def provide_feedback(
    feedback_request: FeedbackRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Provide feedback (like/dislike) for a chat message
    """
    db = MainSessionLocal()
    try:
        # Check if message exists and belongs to user
        message = db.query(ChatMessage).filter(
            ChatMessage.id == feedback_request.message_id,
            ChatMessage.user_id == current_user.id,
            ChatMessage.is_user_message == False  # Only allow feedback on AI responses
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Update message rating
        message.liked = feedback_request.rating
        
        # Create or update feedback record
        feedback = db.query(ChatFeedback).filter(
            ChatFeedback.message_id == feedback_request.message_id
        ).first()
        
        if feedback:
            # Update existing feedback
            feedback.rating = feedback_request.rating
            feedback.feedback_text = feedback_request.feedback_text
        else:
            # Create new feedback
            feedback = ChatFeedback(
                message_id=feedback_request.message_id,
                rating=feedback_request.rating,
                feedback_text=feedback_request.feedback_text
            )
            db.add(feedback)
        
        db.commit()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Feedback recorded successfully",
            "rating": feedback_request.rating
        })
        
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")
    finally:
        db.close()

@router.get("/feedback/{message_id}")
async def get_feedback(
    message_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get feedback for a specific message
    """
    db = MainSessionLocal()
    try:
        # Check if message exists and belongs to user
        message = db.query(ChatMessage).filter(
            ChatMessage.id == message_id,
            ChatMessage.user_id == current_user.id,
            ChatMessage.is_user_message == False
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Get feedback record
        feedback = db.query(ChatFeedback).filter(
            ChatFeedback.message_id == message_id
        ).first()
        
        return JSONResponse(status_code=200, content={
            "message_id": message_id,
            "liked": message.liked,
            "feedback": {
                "rating": feedback.rating if feedback else None,
                "feedback_text": feedback.feedback_text if feedback else None,
                "created_at": feedback.created_at.isoformat() if feedback else None
            } if feedback else None
        })
        
    finally:
        db.close()

@router.delete("/feedback/{message_id}")
async def delete_feedback(
    message_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete feedback for a message (reset like/dislike)
    """
    db = MainSessionLocal()
    try:
        # Check if message exists and belongs to user
        message = db.query(ChatMessage).filter(
            ChatMessage.id == message_id,
            ChatMessage.user_id == current_user.id,
            ChatMessage.is_user_message == False
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Reset message rating
        message.liked = None
        
        # Delete feedback record
        feedback = db.query(ChatFeedback).filter(
            ChatFeedback.message_id == message_id
        ).first()
        
        if feedback:
            db.delete(feedback)
        
        db.commit()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Feedback removed successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove feedback")
    finally:
        db.close()

@router.post("/sessions/{session_id}/title")
async def update_session_title(
    session_id: int,
    title_request: SessionTitleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update chat session title
    """
    db = MainSessionLocal()
    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.title = title_request.title
        session.updated_at = datetime.now()
        
        db.commit()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Title updated successfully"
        })
        
    finally:
        db.close()

@router.get("/sessions")
async def get_chat_sessions(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    Get list of chat sessions for the user
    """
    db = MainSessionLocal()
    try:
        offset = (page - 1) * limit
        
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit).all()
        
        session_summaries = []
        for session in sessions:
            message_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).count()
            
            session_summaries.append({
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": message_count
            })
        
        has_more = len(sessions) == limit
        
        return JSONResponse(status_code=200, content={
            "sessions": session_summaries,
            "has_more": has_more
        })
        
    finally:
        db.close()

@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get full details of a specific chat session
    """
    db = MainSessionLocal()
    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        message_data = []
        for msg in messages:
            message_data.append({
                "id": msg.id,
                "is_user": msg.is_user_message,
                "content": msg.message if msg.is_user_message else msg.response,
                "timestamp": msg.created_at.isoformat(),
                "liked": msg.liked if not msg.is_user_message else None,
                "references": msg.references if not msg.is_user_message else None
            })
        
        return JSONResponse(status_code=200, content={
            "id": session.id,
            "title": session.title,
            "messages": message_data,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        })
        
    finally:
        db.close()

@router.post("/reset")
async def reset_chat(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Reset chat - deactivates current session
    """
    db = MainSessionLocal()
    try:
        session = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id,
            ChatSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
        
        app_manager = request.app.state.app_manager
        app_manager.chat_reset()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Chat reset successfully"
        })
        
    except Exception as e:
        logger.error(f"Error resetting chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset chat")
    finally:
        db.close()

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a chat session and all its messages
    """
    db = MainSessionLocal()
    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        db.delete(session)
        db.commit()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Session deleted successfully"
        })
        
    finally:
        db.close()