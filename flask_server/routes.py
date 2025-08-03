from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity,
    create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies)
from database.crud import create_analysis_task, get_user_by_username
from database.session import MainSessionLocal
from database.session import RulesSessionLocal
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
    response.headers.add('Access-Control-Allow-Credentials', 'true')

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
    
    # Validate required fields
    if 'data' not in data:
        return jsonify({"error": "Missing 'data' in request"}), 400
       
    # Create analysis task
    db = MainSessionLocal()
    try:
        task = create_analysis_task(
            db=db,
            user_id=user_id,
            prompt=data['data'],
        )
        
        # FIX: Use current_app instead of app
        if hasattr(current_app, 'app_manager'):
            current_app.app_manager.add_analysis_task(task.id)
        else:
            logger.error("AppManager not available in Flask app context")
            return jsonify({"error": "Internal server error"}), 500
        
        return jsonify({
            "message": "Analysis started",
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

    # Validate required fields
    # "law_id" ,"section_no", "check_law_id"
    if 'law_id' not in data:
        return jsonify({"error": "Missing 'law_id' in request"}), 400

    if 'section_no' not in data:
        return jsonify({"error": "Missing 'section_no' in request"}), 400

    if 'check_law_id' not in data:
        return jsonify({"error": "Missing 'check_law_id' in request"}), 400

    # Create analysis task
    # db = RulesSessionLocal()
    try:
        # task = create_analysis_rules_task(
        #     db=db,
        #     user_id=user_id,
        #     law_id=data['law_id'],
        #     section=data['section_no'],
        #     law_id_check=data['check_law_id'],
        # )

        # FIX: Use current_app instead of app
        if hasattr(current_app, 'app_manager'):
            current_app.app_manager.add_analysis_rules_task(data)
        else:
            logger.error("AppManager not available in Flask app context")
            return jsonify({"error": "Internal server error"}), 500

        return jsonify({
            "message": "Analysis rules started",
            "task_id": 0
        }), 202
    except Exception as e:
        logger.exception("Error creating analysis task")
        return jsonify({"error": str(e)}), 500


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
            
        return jsonify({
            "task_id": task.id,
            "status": task.status,
            "result": task.result,
            "created_at": task.created_at.isoformat()
        })
    finally:
        db.close()
        
