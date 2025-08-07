from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models_rules import (
        LWLaw, LWSection,LWLawsectionStatus,
        LWTopic, LWSectionTopic
    )
from database.session import RulesSessionLocal

def get_lwlaw_by_id(law_id: int) -> Optional[LWLaw]:
    """
    Get a single law by its ID
    """
    db = RulesSessionLocal()
    try:
        return db.query(LWLaw).filter(LWLaw.ID == law_id).first()
    finally:
        db.close()

def search_laws_by_text(search_text: str, topic_ids: list, limit: int = 10) -> List[LWLaw]:
    """
    Search laws using full-text search on section content
    Returns laws that have sections matching the search text and belong to the given topic IDs
    """
    db = RulesSessionLocal()
    try:
        # Join LWLaw with LWSection and LWSectionTopic to filter by topic
        laws = db.query(LWLaw).join(
            LWSection, LWSection.F_LWLAWID == LWLaw.ID
        ).join(
            LWSectionTopic, LWSectionTopic.F_SECTIONID == LWSection.ID
        ).filter(
            LWLaw.CAPTION.ilike(f"%{search_text}%"),
            LWSectionTopic.F_TOPICID.in_(topic_ids)  # Filter by topic_ids
        ).limit(limit).all()

        return laws
    finally:
        db.close()

def get_law_with_sections(law_id: int) -> dict:
    """
    Get a law with all its sections and full-text search highlights
    """
    db = RulesSessionLocal()
    try:
        law = db.query(LWLaw).filter(LWLaw.ID == law_id).first()
        if not law:
            return None

        # Get all sections for this law
        sections = db.query(LWSection).filter(
            LWSection.F_LWLAWID == law_id
        ).order_by(LWSection.TEXTORDER).all()

        return {
            "law": law,
            "sections": sections
        }
    finally:
        db.close()

def search_laws_with_sections(search_text: str, limit: int = 5) -> List[dict]:
    """
    Search laws with matching sections and include section highlights
    """
    db = RulesSessionLocal()
    try:
        # Find sections matching the search text
        matching_sections = db.query(
            LWSection.F_LWLawID,
            LWSection.ID,
            LWSection.CAPTION,
            func.snippet(fts_lwsection, '<b>', '</b>', '...', -1, 20).label('highlight')
        ).join(
            func.fts_lwsection,
            LWSection.ID == func.fts_lwsection.rowid
        ).filter(
            func.fts_lwsection.match(search_text)
        ).subquery()

        # Get laws with their matching sections
        laws = db.query(LWLaw).join(
            matching_sections,
            LWLaw.ID == matching_sections.c.F_LWLawID
        ).limit(limit).all()

        # Group sections by law
        results = []
        for law in laws:
            sections = db.query(
                matching_sections.c.ID,
                matching_sections.c.CAPTION,
                matching_sections.c.highlight
            ).filter(
                matching_sections.c.F_LWLawID == law.ID
            ).all()

            results.append({
                "law": law,
                "matching_sections": sections
            })

        return results
    finally:
        db.close()

def get_sections_by_law_and_type(law_id: int, section_type_no: int) -> List[LWSection]:
    """
    Get sections by law ID and section type number
    Args:
        law_id: The ID of the law
        section_type_no: The section type number to filter by
    Returns:
        List of LWSection objects matching the criteria
    """
    db = RulesSessionLocal()
    try:
        return db.query(LWSection).filter(
            LWSection.F_LWLAWID == law_id,
            LWSection.SECTIONTYPENO == section_type_no
        ).order_by(LWSection.TEXTORDER).all()
    finally:
        db.close()

def search_section_by_id(section_id: int) -> Optional[dict]:
    """
    Get a single section by its ID with its status caption and topic captions
    Args:
        section_id: The ID of the section to retrieve
    Returns:
        Dictionary containing section, status_caption, and topics if found, None otherwise
    """
    db = RulesSessionLocal()
    try:
        # Get section with status caption
        result = db.query(
            LWSection,
            LWLawsectionStatus.CAPTION.label('status_caption'),
            func.group_concat(LWTopic.CAPTION).label('topic_captions')
        ).outerjoin(
            LWLawsectionStatus,
            LWSection.F_CMBASETABLEID_SECTIONSTATUS == LWLawsectionStatus.ID
        ).outerjoin(
            LWSectionTopic,
            LWSection.ID == LWSectionTopic.F_SECTIONID
        ).outerjoin(
            LWTopic,
            LWSectionTopic.F_TOPICID == LWTopic.ID
        ).filter(
            LWSection.ID == section_id
        ).group_by(
            LWSection.ID
        ).first()

        if not result:
            return None

        section, status_caption, topic_captions = result

        return {
            "section": section,
            "status_caption": status_caption,
            "topics": topic_captions.split(',') if topic_captions else []
        }
    finally:
        db.close()
