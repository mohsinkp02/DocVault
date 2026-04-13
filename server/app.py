"""DocVault - Offline-First Document Storage System"""

from flask import Flask, jsonify, send_file, render_template_string
from flask_cors import CORS
import os

try:
    from .config import SECRET_KEY, DEBUG, MAX_CONTENT_LENGTH
    from .routes.api import api_bp
    from .utils.logger import setup_logger
except ImportError:
    from config import SECRET_KEY, DEBUG, MAX_CONTENT_LENGTH
    from routes.api import api_bp
    from utils.logger import setup_logger

logger = setup_logger(__name__)

# Get the root directory (parent of server directory)
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder=None)
    
    # Configuration
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS for local development
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Cache busting headers for all responses
    @app.after_request
    def add_cache_headers(response):
        if response.content_type and ('text/html' in response.content_type or 
                                      'text/javascript' in response.content_type or
                                      'application/javascript' in response.content_type or
                                      'text/css' in response.content_type):
            response.cache_control.max_age = 0
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    
    # Global error handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            "success": False,
            "error": f"File too large. Maximum size: {MAX_CONTENT_LENGTH / (1024 * 1024):.0f}MB"
        }), 413
    
    # Serve static frontend files with no-cache headers
    @app.route('/<path:filename>')
    def serve_static(filename):
        """Serve static files from root directory"""
        filepath = os.path.join(ROOT_DIR, filename)
        if os.path.exists(filepath) and os.path.isfile(filepath):
            return send_file(filepath)
        return jsonify({"error": "Not found"}), 404
    
    @app.route('/', methods=['GET'])
    def index():
        """Serve index.html for root path"""
        index_path = os.path.join(ROOT_DIR, 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Fallback to API documentation if index.html doesn't exist
        return jsonify({
            "name": "DocVault",
            "version": "1.0.0",
            "description": "Offline-First Document Storage System",
            "endpoints": {
                "GET /api/health": "Health check",
                "POST /api/create-folder": "Create folder",
                "POST /api/delete-folder": "Delete folder",
                "POST /api/delete-file": "Delete file",
                "POST /api/upload-file": "Upload file",
                "GET /api/list": "List contents",
                "POST /api/rename": "Rename file/folder",
                "GET /api/storage-stats": "Storage statistics",
                "GET /api/download/<file_path>": "Download file"
            },
            "documentation": "See README.md for detailed API documentation"
        }), 200
    
    @app.route('/docs', methods=['GET'])
    def docs():
        """API documentation in detail"""
        docs_text = """
        <html>
        <head>
            <title>DocVault API Documentation</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                h2 { color: #666; margin-top: 30px; }
                code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
                pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>DocVault API Documentation</h1>
            <p>Offline-First Document Storage System</p>
            
            <h2>Available Endpoints</h2>
            
            <h3>POST /api/create-folder</h3>
            <p>Create a new folder (including nested folders)</p>
            <pre>
{
  "folder_path": "Documents/MyProject"
}
            </pre>
            
            <h3>POST /api/delete-folder</h3>
            <p>Delete a folder</p>
            <pre>
{
  "folder_path": "Documents/MyProject",
  "force": true
}
            </pre>

            <h3>POST /api/delete-file</h3>
            <p>Delete a file</p>
            <pre>
{
  "file_path": "Documents/report.pdf"
}
            </pre>
            
            <h3>POST /api/upload-file</h3>
            <p>Upload a file to a folder</p>
            <p>Form data: file (binary), folder_path (string)</p>
            
            <h3>GET /api/list</h3>
            <p>List files and folders</p>
            <p>Query: folder_path (optional)</p>
            
            <h3>POST /api/rename</h3>
            <p>Rename a file or folder</p>
            <pre>
{
  "item_path": "Documents/OldName",
  "new_name": "NewName"
}
            </pre>
            
            <h3>GET /api/storage-stats</h3>
            <p>Get storage statistics</p>
            
            <h3>GET /api/download/&lt;file_path&gt;</h3>
            <p>Download a file</p>
            
            <h2>Headers</h2>
            <p>Optional: X-User-ID (defaults to 'default_user')</p>
            
            <h2>Error Responses</h2>
            <pre>
{
  "success": false,
  "error": "Error message"
}
            </pre>
        </body>
        </html>
        """
        return docs_text, 200, {'Content-Type': 'text/html'}
    
    logger.info("DocVault application initialized")
    return app


if __name__ == '__main__':
    app = create_app()
    logger.info(f"Starting DocVault on http://localhost:5000 (DEBUG: {DEBUG})")
    app.run(debug=DEBUG, host='0.0.0.0', port=5000)
