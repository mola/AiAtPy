from flask import jsonify, request, Blueprint
from database.law_repository import (
    get_lwlaw_by_id,
    search_laws_by_text,
    get_law_with_sections,
    search_laws_with_sections
)
from werkzeug.exceptions import BadRequest, NotFound
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
rbp = Blueprint('rbp', __name__, url_prefix='/api')

@rbp.route('/laws/<int:law_id>', methods=['GET'])
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
def get_law_sections(law_id):
    """
    Get a law with all its sections
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
        description: Law with sections
      404:
        description: Law not found
    """
    try:
        result = get_law_with_sections(law_id)
        if not result:
            raise NotFound(f"Law with ID {law_id} not found")

        return jsonify({
            "law": {
                "id": result["law"].ID,
                "caption": result["law"].CAPTION
            },
            "sections": [{
                "id": section.ID,
                "caption": section.CAPTION,
                "text": section.SECTIONTEXT,
                "order": section.TEXTORDER
            } for section in result["sections"]]
        })
    except Exception as e:
        logger.error(f"Error getting law sections {law_id}: {str(e)}")
        raise

@rbp.route('/laws/search/advanced', methods=['GET'])
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

@rbp.route('/laws/<int:law_id>/sections', methods=['GET'])
def get_sections_by_law_and_type(law_id):
    """
    Get sections by law ID and section type number
    ---
    tags:
      - Sections
    parameters:
      - name: law_id
        in: path
        type: integer
        required: true
        description: ID of the law
      - name: section_type_no
        in: query
        type: integer
        required: true
        description: Section type number to filter by
    responses:
      200:
        description: List of sections matching the criteria
      400:
        description: Missing required parameters
      404:
        description: Law not found or no sections found
    """
    try:
        section_type_no = request.args.get('section_type_no')
        if not section_type_no:
            raise BadRequest("section_type_no parameter is required")

        sections = get_sections_by_law_and_type(law_id, int(section_type_no))
        if not sections:
            raise NotFound(f"No sections found for law ID {law_id} with type {section_type_no}")

        return jsonify([{
            "id": section.ID,
            "caption": section.CAPTION,
            "section_text": section.SECTIONTEXT,
            "text_order": section.TEXTORDER,
            "section_type_no": section.SECTIONTYPENO
        } for section in sections])
    except ValueError:
        raise BadRequest("section_type_no must be an integer")
    except Exception as e:
        logger.error(f"Error getting sections: {str(e)}")
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
