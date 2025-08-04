# routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity,
    create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies)
from database.crud import create_analysis_task, get_user_by_username
from database.session import MainSessionLocal
from database.session import RulesSessionLocal
from database.models import AnalysisTask
from .auth import authenticate_user
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
bp = Blueprint('api', __name__, url_prefix='/api')

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
    
    # Create analysis task
    db = MainSessionLocal()
    try:
        # Store all relevant data in JSON format
        task_data = {
            "type": "custom",
            "prompt": data['prompt'],
            "check_law_id": data['check_law_id'],
            "compare_all": data['check_law_id'] == "*"
        }
        
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

    # Create analysis task
    db = MainSessionLocal()
    try:
        # Store all relevant data in JSON format
        task_data = {
            "type": "existing",
            "law_id": data['law_id'],
            "section_no": data['section_no'],
            "check_law_id": data['check_law_id'],
            "compare_all": data['check_law_id'] == "*"
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
    db = MainSessionLocal()
    try:
        task = db.query(AnalysisTask).filter(
            AnalysisTask.id == task_id,
            AnalysisTask.user_id == get_jwt_identity()
        ).first()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
            
        # Returning the task status along with the result (if available)
        return jsonify({
            "task_id": task.id,
            "status": task.status,
            "result": task.result if task.result else "Result not available yet",
            "created_at": task.created_at
        })
    finally:
        db.close()

        
