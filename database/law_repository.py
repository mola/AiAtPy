from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models_rules import LWLaw, LWSection
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

def search_laws_by_text(search_text: str, limit: int = 10) -> List[LWLaw]:
    """
    Search laws using full-text search on section content
    Returns laws that have sections matching the search text
    """
    db = RulesSessionLocal()
    try:
        return db.query(LWLaw).filter(
            LWLaw.CAPTION.ilike(f"%{search_text}%")
        ).limit(limit).all()
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
