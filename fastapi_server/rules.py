from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional, List, Any
import logging
from pydantic import BaseModel

from database.session import RulesSessionLocal
from database.law_repository import (
    get_lwlaw_by_id,
    search_laws_by_text,
    get_law_with_sections,
    search_laws_with_sections,
    search_section_by_id
)
from fastapi_server.auth import get_current_user
from database.models_rules import LWTopic, LWSection, LWLaw
from database.models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["laws","topics"])

# Pydantic models for request/response
class LawResponse(BaseModel):
    id: int
    caption: str
    law_no: Optional[int] = None
    approve_date: Optional[str] = None
    content_text: Optional[str] = None

class SectionResponse(BaseModel):
    id: int
    caption: str
    text: str
    order: Optional[int] = None
    section_no: Optional[int] = None
    section_level: Optional[int] = None
    full_path: str
    law_id: int
    parent_id: Optional[int] = None
    status_caption: Optional[str] = None
    topics: List[Any] = []

class SearchRequest(BaseModel):
    q: str
    limit: Optional[int] = 10
    topic_ids: Optional[List[int]] = None

class AdvancedSearchRequest(BaseModel):
    q: str
    limit: Optional[int] = 5

class MatchingSection(BaseModel):
    id: int
    caption: str
    highlight: Optional[str] = None

class AdvancedSearchResult(BaseModel):
    law: LawResponse
    matching_sections: List[MatchingSection]

class TopicResponse(BaseModel):
    ID: int
    CAPTION: str
    children: List['TopicResponse'] = []

class SectionBasic(BaseModel):
    id: int
    caption: str
    text: str
    order: Optional[int] = None
    section_no: Optional[int] = None

class LawWithSectionsResponse(BaseModel):
    law: dict
    sections: List[SectionBasic]

@router.get("/laws/{law_id}", response_model=LawResponse)
async def get_law(law_id: int, current_user: User = Depends(get_current_user)):
    """
    Get a single law by its ID
    """
    try:
        law = get_lwlaw_by_id(law_id)
        if not law:
            raise HTTPException(status_code=404, detail=f"Law with ID {law_id} not found")

        return {
            "id": law.ID,
            "caption": law.CAPTION,
            "law_no": law.LAWNO,
            "approve_date": law.APPROVEDATE,
            "content_text": law.CONTENTTEXT
        }
    except Exception as e:
        logger.error(f"Error getting law {law_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/laws/search", response_model=List[LawResponse])
async def search_laws(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search laws by text content and filter by topic IDs
    """
    try:
        if not search_request.q:
            raise HTTPException(status_code=400, detail="Search query parameter 'q' is required")
        
        laws = search_laws_by_text(search_request.q, search_request.topic_ids, search_request.limit)

        return [{
            "id": law.ID,
            "caption": law.CAPTION,
            "law_no": law.LAWNO if law.LAWNO is not None else 0,
            "approve_date": law.APPROVEDATE
        } for law in laws]
    except Exception as e:
        logger.error(f"Error searching laws: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/laws/search/advanced", response_model=List[AdvancedSearchResult])
async def advanced_search(
    q: str = Query(..., description="Search query text"),
    limit: int = Query(5, description="Maximum number of results to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Advanced search with highlighted matches
    """
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Search query parameter 'q' is required")

        results = search_laws_with_sections(q, limit)

        return [{
            "law": {
                "id": result["law"].ID,
                "caption": result["law"].CAPTION,
                "law_no": result["law"].LAWNO
            },
            "matching_sections": [{
                "id": section.ID,
                "caption": section.CAPTION,
                "highlight": section.highlight
            } for section in result["matching_sections"]]
        } for result in results]
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get a single section by its ID with topics
    """
    try:
        result = search_section_by_id(section_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Section with ID {section_id} not found")

        section = result["section"]
        status_caption = result["status_caption"]

        return {
            "id": section.ID,
            "caption": section.CAPTION,
            "text": section.SECTIONTEXT,
            "order": section.TEXTORDER,
            "section_no": section.SECTIONTYPENO,
            "section_level": section.SECTIONLEVEL,
            "full_path": section.FULLPATH,
            "law_id": section.F_LWLAWID,
            "parent_id": section.F_PARENTID,
            "status_caption": status_caption,
            "topics": result["topics"]
        }
    except Exception as e:
        logger.error(f"Error getting section {section_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/laws/{law_id}/sections", response_model=LawWithSectionsResponse)
async def get_law_with_all_sections(
    law_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get a law with all its sections
    """
    try:
        result = get_law_with_sections(law_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Law with ID {law_id} not found")

        return {
            "law": {
                "id": result["law"].ID,
                "caption": result["law"].CAPTION
            },
            "sections": [{
                "id": section.ID,
                "caption": section.CAPTION if section.CAPTION is not None else "",
                "text": section.SECTIONTEXT if section.SECTIONTEXT is not None else "",
                "order": section.TEXTORDER,
                "section_no": int(section.SECTIONTYPENO) if section.SECTIONTYPENO is not None else None
            } for section in result["sections"]]
        }
            
    except Exception as e:
        logger.error(f"Error getting law sections {law_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def build_topic_tree(topic_id: int, db_r):
    topic = db_r.query(LWTopic).filter(LWTopic.ID == topic_id).first()
    if not topic:
        return None
    topic_data = {'ID': int(topic.ID), 'CAPTION': topic.CAPTION, 'children': []}
    children = db_r.query(LWTopic).filter(LWTopic.F_PARENTID == topic_id).all()
    for child in children:
        child_tree = build_topic_tree(child.ID, db_r)
        if child_tree:
            topic_data['children'].append(child_tree)
    return topic_data

# Add the /topics endpoint (with optional tag override if you want it separate in docs)
@router.get("/topics", response_model=List[TopicResponse], tags=["topics"])  # Optional: Overrides router-level tags for this endpoint
async def get_topics(current_user: User = Depends(get_current_user)):
    try:
        with RulesSessionLocal() as db_r:
            top_level_topics = db_r.query(LWTopic).filter(LWTopic.F_PARENTID == None).all()
            topic_tree = [build_topic_tree(top.ID, db_r) for top in top_level_topics if build_topic_tree(top.ID, db_r)]
        if not topic_tree:
            raise HTTPException(status_code=404, detail="No topics found")
        return topic_tree
    except Exception as e:
        logger.error(f"Error getting topics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")