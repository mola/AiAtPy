from flask import jsonify, request, Blueprint
from database.law_repository import (
    get_lwlaw_by_id,
    search_laws_by_text,
    get_law_with_sections,
    search_laws_with_sections
)
from flask_jwt_extended import (
    jwt_required
    )
from werkzeug.exceptions import BadRequest, NotFound
import logging
from database.models_rules import LWTopic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
rbp = Blueprint('rbp', __name__, url_prefix='/api')

@rbp.route('/laws/<int:law_id>', methods=['GET'])
@jwt_required()
def get_law(law_id):
    """
    Get a single law by its ID
    ---
    tags:
      - Laws
    parameters:
      - name: law_id
        in: path
        type: integer
        required: true
        description: ID of the law to retrieve
    responses:
      200:
        description: Law details
      404:
        description: Law not found
    """
    try:
        law = get_lwlaw_by_id(law_id)
        if not law:
            raise NotFound(f"Law with ID {law_id} not found")

        return jsonify({
            "id": law.ID,
            "caption": law.CAPTION,
            "law_no": law.LAWNO,
            "approve_date": law.APPROVEDATE,
            "content_text": law.CONTENTTEXT
        })
    except Exception as e:
        logger.error(f"Error getting law {law_id}: {str(e)}")
        raise

@rbp.route('/laws/search', methods=['GET'])
@jwt_required()
def search_laws():
    """
    Search laws by text content
    ---
    tags:
      - Laws
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search query text
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
        description: Maximum number of results to return
    responses:
      200:
        description: List of matching laws
      400:
        description: Missing search query
    """
    try:
        search_text = request.args.get('q')
        if not search_text:
            raise BadRequest("Search query parameter 'q' is required")

        limit = int(request.args.get('limit', 10))
        laws = search_laws_by_text(search_text, limit)

        return jsonify([{
            "id": law.ID,
            "caption": law.CAPTION,
            "law_no": law.LAWNO,
            "approve_date": law.APPROVEDATE
        } for law in laws])
    except Exception as e:
        logger.error(f"Error searching laws: {str(e)}")
        raise

@rbp.route('/laws/<int:law_id>/sections', methods=['GET'])
@jwt_required()
def get_law_sections(law_id):
    """
    Get all sections for a specific law
    ---
    tags:
      - Laws
    parameters:
      - name: law_id
        in: path
        type: integer
        required: true
        description: ID of the law
    responses:
      200:
        description: List of all sections for the law
      404:
        description: Law not found or no sections available
    """
    try:
        result = get_law_with_sections(law_id)
        if not result or not result.get("sections"):
            raise NotFound(f"No sections found for law ID {law_id}")

        return jsonify({
            "law": {
            "id": result["law"].ID,
            "caption": result["law"].CAPTION
            },
            "sections": [{
            "id": section.ID,
            "caption": section.CAPTION,
            "text": section.SECTIONTEXT,
            "order": section.TEXTORDER,
            "section_no": section.SECTIONTYPENO
            } for section in result["sections"]]
        })
    except Exception as e:
        logger.error(f"Error getting sections for law {law_id}: {str(e)}")
        raise

@rbp.route('/laws/<int:law_id>/sections/<int:section_no>', methods=['GET'])
@jwt_required()
def get_specific_section(law_id, section_no):
    """
    Get a specific section from a law by section number
    ---
    tags:
      - Laws
    parameters:
      - name: law_id
        in: path
        type: integer
        required: true
        description: ID of the law
      - name: section_no
        in: path
        type: integer
        required: true
        description: Section number to retrieve
    responses:
      200:
        description: Section details
      404:
        description: Law or section not found
    """
    try:
        result = get_law_with_sections(law_id)
        if not result:
            raise NotFound(f"Law with ID {law_id} not found")

        section = next((s for s in result["sections"] if s.SECTIONTYPENO == section_no), None)
        if not section:
            raise NotFound(f"Section {section_no} not found in law {law_id}")

        return jsonify({
            "id": section.ID,
            "caption": section.CAPTION,
            "text": section.SECTIONTEXT,
            "order": section.TEXTORDER,
            "section_no": section.SECTIONTYPENO
        })
    except Exception as e:
        logger.error(f"Error getting section {section_no} from law {law_id}: {str(e)}")
        raise

@rbp.route('/laws/search/advanced', methods=['GET'])
@jwt_required()
def advanced_search():
    """
    Advanced search with highlighted matches
    ---
    tags:
      - Laws
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search query text
      - name: limit
        in: query
        type: integer
        required: false
        default: 5
        description: Maximum number of results to return
    responses:
      200:
        description: List of laws with matching highlighted sections
      400:
        description: Missing search query
    """
    try:
        search_text = request.args.get('q')
        if not search_text:
            raise BadRequest("Search query parameter 'q' is required")

        limit = int(request.args.get('limit', 5))
        results = search_laws_with_sections(search_text, limit)

        return jsonify([{
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
        } for result in results])
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        raise

@rbp.errorhandler(NotFound)
def handle_not_found(e):
    return jsonify({"error": str(e)}), 404

@rbp.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({"error": str(e)}), 400

@rbp.errorhandler(Exception)
def handle_exception(e):
    logger.exception("An unexpected error occurred")
    return jsonify({"error": "Internal server error"}), 500

@rbp.route('/topics', methods=['GET'])
@jwt_required()
def get_topics():
    """
    Get all topics or search by caption
    ---
    tags:
      - Topics
    parameters:
      - name: q
        in: query
        type: string
        required: false
        description: Search query for topic caption
      - name: limit
        in: query
        type: integer
        required: false
        default: 100
        description: Maximum number of results to return
    responses:
      200:
        description: List of topics
    """
    try:
        search_text = request.args.get('q')
        limit = int(request.args.get('limit', 100))

        # Query the database
        query = LWTopic.query

        if search_text:
            query = query.filter(LWTopic.CAPTION.ilike(f'%{search_text}%'))

        topics = query.limit(limit).all()

        return jsonify([{
            "id": topic.ID,
            "code": topic.CODE,
            "caption": topic.CAPTION,
            "parent_id": topic.F_PARENTID,
            "hierarchy": topic.HIERARCHY
        } for topic in topics])

    except Exception as e:
        logger.error(f"Error getting topics: {str(e)}")
        raise

@rbp.route('/topics/<int:topic_id>', methods=['GET'])
@jwt_required()
def get_topic(topic_id):
    """
    Get a single topic by its ID
    ---
    tags:
      - Topics
    parameters:
      - name: topic_id
        in: path
        type: integer
        required: true
        description: ID of the topic to retrieve
    responses:
      200:
        description: Topic details
      404:
        description: Topic not found
    """
    try:
        topic = LWTopic.query.get(topic_id)
        if not topic:
            raise NotFound(f"Topic with ID {topic_id} not found")

        return jsonify({
            "id": topic.ID,
            "code": topic.CODE,
            "caption": topic.CAPTION,
            "parent_id": topic.F_PARENTID,
            "hierarchy": topic.HIERARCHY,
            "old_id": topic.OLDID
        })
    except Exception as e:
        logger.error(f"Error getting topic {topic_id}: {str(e)}")
        raise
