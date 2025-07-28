import os
import shutil
import time
from flask import Flask, jsonify
from flask_cors import CORS
from aiatconfig import AiAtConfig

def create_flask_app(settings):
    # Create Flask app and use the read static folder path (and an empty URL path)
    static_folder = settings.value("flask/static_folder", os.path.join("frontend", "build"))
    app = Flask(__name__, static_folder=static_folder, static_url_path="")
    
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
        supports_credentials=True
    )

    app.secret_key = settings.value("flask/secret_key", "your_secret_key_here")

    # File upload configuration
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

    # Register Flask Blueprints
    ## app.register_blueprint(EXAMPLE API)

    return app

def start_flask(app):
    """
    Run the Flask app using Flask's built-in server.
    Suitable for development and testing purposes.
    """
    app.run(host='0.0.0.0', port=8000, use_reloader=False, threaded=True, debug=False)
