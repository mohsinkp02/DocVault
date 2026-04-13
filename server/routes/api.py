"""API routes for DocVault"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

try:
    from ..storage.manager import StorageManager
    from ..utils.validators import PathValidator
    from ..utils.logger import setup_logger
    from ..config import DEFAULT_USER_ID, ALLOWED_EXTENSIONS
except ImportError:
    from storage.manager import StorageManager
    from utils.validators import PathValidator
    from utils.logger import setup_logger
    from config import DEFAULT_USER_ID, ALLOWED_EXTENSIONS

api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = setup_logger(__name__)


def get_user_id_from_request():
    """Extract user_id from request headers or use default"""
    return request.headers.get('X-User-ID', DEFAULT_USER_ID)


def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "DocVault"}), 200


@api_bp.route('/create-folder', methods=['POST'])
def create_folder():
    """Create a new folder"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}
        
        folder_path = data.get('folder_path', '').strip()
        
        if not folder_path:
            return jsonify({"success": False, "error": "folder_path is required"}), 400
        
        result = StorageManager.create_folder(user_id, folder_path)
        status_code = 201 if result['success'] else 400
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in create_folder: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/delete-folder', methods=['POST'])
def delete_folder():
    """Delete a folder"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}
        
        folder_path = data.get('folder_path', '').strip()
        force = data.get('force', False)
        
        if not folder_path:
            return jsonify({"success": False, "error": "folder_path is required"}), 400
        
        result = StorageManager.delete_folder(user_id, folder_path, force=force)
        status_code = 200 if result['success'] else 400
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in delete_folder: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/delete-file', methods=['POST'])
def delete_file():
    """Delete a file"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}

        file_path = data.get('file_path', '').strip()

        if not file_path:
            return jsonify({"success": False, "error": "file_path is required"}), 400

        result = StorageManager.delete_file(user_id, file_path)
        status_code = 200 if result['success'] else 400

        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error in delete_file: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/upload-file', methods=['POST'])
def upload_file():
    """Upload a file to a folder"""
    try:
        user_id = get_user_id_from_request()
        folder_path = request.form.get('folder_path', '').strip()
        
        if folder_path is None:
            return jsonify({"success": False, "error": "folder_path is required"}), 400
        
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        filename = secure_filename(file.filename)
        result = StorageManager.upload_file(user_id, folder_path, filename, file)
        status_code = 201 if result['success'] else 400
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/list', methods=['GET'])
def list_contents():
    """List files and folders in a directory"""
    try:
        user_id = get_user_id_from_request()
        # Accept both 'folder_path' (new) and 'path' (old) parameters for compatibility
        folder_path = request.args.get('folder_path', request.args.get('path', '')).strip()
        
        result = StorageManager.list_contents(user_id, folder_path)
        status_code = 200 if result['success'] else 400
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in list_contents: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/rename', methods=['POST'])
def rename_item():
    """Rename a file or folder"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}
        
        item_path = data.get('item_path', '').strip()
        new_name = data.get('new_name', '').strip()
        
        if not item_path or not new_name:
            return jsonify({"success": False, "error": "item_path and new_name are required"}), 400
        
        result = StorageManager.rename_item(user_id, item_path, new_name)
        status_code = 200 if result['success'] else 400
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in rename_item: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/storage-stats', methods=['GET'])
def storage_stats():
    """Get storage statistics"""
    try:
        user_id = get_user_id_from_request()
        result = StorageManager.get_storage_stats(user_id)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in storage_stats: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/download/<path:file_path>', methods=['GET'])
def download_file(file_path):
    """Download a file"""
    try:
        from flask import send_file
        import os
        
        user_id = get_user_id_from_request()
        
        if not PathValidator.is_valid_path(user_id, file_path):
            return jsonify({"success": False, "error": "Invalid file path"}), 400
        
        safe_path = PathValidator.get_safe_path(user_id, file_path)
        
        if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
            return jsonify({"success": False, "error": "File not found"}), 404
        
        return send_file(safe_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error in download_file: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"success": False, "error": "Internal server error"}), 500
