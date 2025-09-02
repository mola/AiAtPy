# routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity,
    create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies)
from database.crud import create_analysis_task, get_user_by_username
from database.session import MainSessionLocal, RulesSessionLocal
from database.models import AnalysisTask,ComparisonResult
from database.models_rules import LWSection, LWLaw
from .auth import authenticate_user
import uuid,logging,json
from datetime import datetime
from sqlalchemy import func 
# from utilities.persian_embedding import PersianEmbeddingSearch
# from .embedding_search_flask import create_embedding_search_instance

logger = logging.getLogger(__name__)
bp = Blueprint('api', __name__, url_prefix='/api')

# embedding_search = PersianEmbeddingSearch()

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = authenticate_user(username, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    resp = jsonify({'login': True})
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)

    print("Cookies being set in response:")
    print(resp.headers.getlist('Set-Cookie'))

    return resp, 200

@bp.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    # Create the new access token
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)

    # Set the JWT access cookie in the response
    resp = jsonify({'refresh': True})
    set_access_cookies(resp, access_token)
    return resp, 200

@bp.route('/token/remove', methods=['POST'])
def logout():
    resp = jsonify({'logout': True})
    unset_jwt_cookies(resp)
    return resp, 200

@bp.after_request
def after_request(response):
    # Ensure credentials are allowed
    # response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    # response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8000')
    # response.headers.add('Access-Control-Allow-Credentials', 'true')
    # response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    # response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

    # For preflight requests
    if request.method == 'OPTIONS':
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

    return response
@bp.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


# @bp.route('/search_similar', methods=['POST'])
# @jwt_required()
# def search_similar():
#     data = request.get_json()
#     user_id = get_jwt_identity()
#     query_text = data.get('query_text')
#     k = data.get('k', 20)  # Default to 20 if not specified
    
#     if not query_text:
#         return jsonify({"error": "query_text is required"}), 400
        
#     try:
#         distances, indices = embedding_search.find_similar(query_text, k)
#         return jsonify({
#             "status": "success",
#             "distances": distances.tolist(),  # Convert numpy array to list
#             "indices": indices.tolist()
#         }), 200
#     except Exception as e:
#         logger.exception("Error in similarity search")
#         return jsonify({
#             "status": "error",
#             "message": str(e)
#         }), 500
        
@bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_law():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    # Validate required fields for custom law analysis
    if 'prompt' not in data:
        return jsonify({"error": "Missing 'prompt' in request"}), 400
    if 'check_law_id' not in data:
        return jsonify({"error": "Missing 'check_law_id' in request"}), 400
    
    topic_ids = data.get('topic_ids', [])  # Default to an empty list if not provided

    # Create analysis task
    db = MainSessionLocal()
    try:
        # Store all relevant data in JSON format
        task_data = {
            "type": "custom",
            "prompt": data['prompt'],
            "prompt_title": data.get('prompt_title'),
            "system_prompt": data.get('system_prompt'),
            "check_law_id": data['check_law_id'],
            "compare_all": data['check_law_id'] == "*",
            "topic_ids": topic_ids # Store the list of topic_ids when compare all
        }
        
        # prompt = data['prompt']
        # emsrch = create_embedding_search_instance()
        # emsrch.get_section_ids(prompt)

        task = create_analysis_task(
            db=db,
            user_id=user_id,
            data=task_data
        )
        
        # Pass to AppManager
        current_app.app_manager.add_analysis_task(task.id)
        
        return jsonify({
            "message": "Custom law analysis started",
            "task_id": task.id
        }), 202
    except Exception as e:
        logger.exception("Error creating analysis task")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    data = request.get_json()
    user_id = get_jwt_identity()
    msg = data.get('msg')
    
    if not msg:
        return jsonify({"error": "Message is required"}), 400
        
    response = current_app.app_manager.chat(msg)
    return jsonify(response), 200 if response['status'] == 'success' else 500

@bp.route('/chat_reset', methods=['POST'])
@jwt_required()
def chat_reset():
    user_id = get_jwt_identity()
    response = current_app.app_manager.chat_reset()
    return jsonify(response), 200 if response['status'] == 'success' else 500


@bp.route('/analyze_rules', methods=['POST'])
@jwt_required()
def analyze_rules():
    data = request.get_json()
    user_id = get_jwt_identity()

    # Validate required fields for existing law analysis
    required_fields = ['law_id', 'section_no', 'check_law_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing '{field}' in request"}), 400

    topic_ids = data.get('topic_ids', [])  # Default to an empty list if not provided

    # Create analysis task
    db = MainSessionLocal()
    try:
        # Store all relevant data in JSON format
        task_data = {
            "type": "existing",
            "law_id": data['law_id'],
            "section_no": data['section_no'],
            "check_law_id": data['check_law_id'],
            "compare_all": data['check_law_id'] == "*",
            "topic_ids": topic_ids # Store the list of topic_ids when compare all
        }
        
        task = create_analysis_task(
            db=db,
            user_id=user_id,
            data=task_data
        )
        
        # Pass to AppManager with task ID
        current_app.app_manager.add_analysis_rules_task(task.id)
        
        return jsonify({
            "message": "Existing law analysis started",
            "task_id": task.id
        }), 202
    except Exception as e:
        logger.exception("Error creating analysis task")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@bp.route('/task/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    # Get optional timestamp and contradiction filter parameters from query string
    since_timestamp = request.args.get('since', type=int)
    contradiction_filter = request.args.get('contradiction', type=str)

    db = MainSessionLocal()
    db_r = RulesSessionLocal()
    
    try:
        # Get the main task
        task = db.query(AnalysisTask).filter(
            AnalysisTask.id == task_id,
            AnalysisTask.user_id == get_jwt_identity()
        ).first()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        # Retrieve section_ids from task data
        section_ids = task.data.get('section_ids', [])

        # Query comparison results with optional timestamp and contradiction filter
        results_query = db.query(ComparisonResult).filter(
            ComparisonResult.task_id == task_id
        )

        if since_timestamp is not None:
            results_query = results_query.filter(
                ComparisonResult.finish_time > since_timestamp
            )
        
        if contradiction_filter is not None:
            # Convert contradiction_filter to boolean value
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

            # Extract why from response JSON (no parsing needed now)
            why_value = result.response.get('why', '') if result.response else ''
            
            first_section_id = int(result.first_section_id)

            # print(f"First Section ID: {result.first_section_id}, Type: {type(result.first_section_id)}")
            results_data.append({
                'id': result.id,
                'first_law_id': result.first_law_id,
                'first_law_caption': first_law_caption,
                'first_section_id': first_section_id,
                'first_section_caption': first_section_caption,
                'second_law_id': result.second_law_id,
                'second_law_caption': second_law_caption,
                'second_section_id': result.second_section_id,
                'second_section_caption': second_section_caption,
                'response': why_value,
                'contradiction': result.contradiction,
                'finish_time': result.finish_time
            })
        
        section_id_to_index = {int(section_id): index for index, section_id in enumerate(section_ids)}

        sorted_results_data = sorted(
            results_data, 
            key=lambda x: section_id_to_index.get(int(x['first_section_id']), float('inf'))
        )

        # Get the latest timestamp for client-side tracking
        latest_timestamp = max(
            [r.finish_time for r in comparison_results] or [0]
        )
        
        return jsonify({
            "task_id": task.id,
            "status": task.status,
            "created_at": task.created_at,
            "results": sorted_results_data,
            "latest_timestamp": latest_timestamp
        })
    finally:
        db.close()
        db_r.close()


@bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    db = MainSessionLocal()
    db_r = RulesSessionLocal()
    try:
        user_id = get_jwt_identity()
        
        # Get all tasks for the current user
        tasks = db.query(AnalysisTask).filter(
            AnalysisTask.user_id == user_id
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
        
        return jsonify(tasks_data)
    finally:
        db.close()
        db_r.close()