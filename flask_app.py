import os
import shutil
import time
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from aiatconfig import AiAtConfig

from flask_server.rules import rbp
from flask_server import routes as api_routes

def create_flask_app(settings):
    # Create Flask app and use the read static folder path (and an empty URL path)
    static_folder = settings.value("flask/static_folder", "frontend")
    app = Flask(__name__, static_folder=static_folder, static_url_path="")
    
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "supports_credentials": True,
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
    app.register_blueprint(api_routes.bp)
    app.register_blueprint(rbp)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve(path):
        """
        Serve the frontend's static files. If the requested path doesn't exist,
        serve the index.html for client-side routing.

        :param path: The path of the requested file.
        :return: The requested file or index.html.
        """
        print(path)
        # Check if the requested path is a static file (e.g., CSS, JS, images)
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)

        # Serve index.html for all other routes (client-side routing)
        return send_from_directory(app.static_folder, "index.html")

    # -------------------------------
    # Handle 404 Errors
    # -------------------------------

    @app.errorhandler(404)
    def page_not_found(e):
        """
        Handle 404 errors by serving index.html.
        This allows the frontend's client-side router to handle the routing.
        """
        return send_from_directory(app.static_folder, "index.html"), 200

    return app

def start_flask(app):
    """
    Run the Flask app using Flask's built-in server.
    Suitable for development and testing purposes.
    """
    app.run(host='0.0.0.0', port=8000, use_reloader=False, threaded=True, debug=False)
