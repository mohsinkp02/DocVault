"""API routes for DocVault"""

from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context
from werkzeug.utils import secure_filename
import os

try:
    from ..storage.factory import get_storage
    from ..utils.validators import PathValidator
    from ..utils.logger import setup_logger
    from ..config import DEFAULT_USER_ID, ALLOWED_EXTENSIONS, STORAGE_MODE, HF_TOKEN
except ImportError:
    from server.storage.factory import get_storage
    from server.utils.validators import PathValidator
    from server.utils.logger import setup_logger
    from server.config import DEFAULT_USER_ID, ALLOWED_EXTENSIONS, STORAGE_MODE, HF_TOKEN

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
    return jsonify({"status": "healthy", "service": "DocVault", "storage": STORAGE_MODE}), 200

@api_bp.route('/create-folder', methods=['POST'])
def create_folder():
    """Create a new folder"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}
        folder_path = data.get('folder_path', '').strip()
        
        logger.info(f"[CREATE_FOLDER] START | user={user_id} | path={folder_path}")
        
        if not folder_path:
            logger.warning(f"[CREATE_FOLDER] FAIL | user={user_id} | reason=empty_path")
            return jsonify({"success": False, "error": "folder_path is required"}), 400
        
        result = get_storage().create_folder(user_id, folder_path)
        
        if result['success']:
            logger.info(f"[CREATE_FOLDER] SUCCESS | user={user_id} | path={folder_path}")
        else:
            logger.warning(f"[CREATE_FOLDER] FAIL | user={user_id} | path={folder_path} | error={result.get('error')}")
        
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        logger.error(f"[CREATE_FOLDER] EXCEPTION | user={user_id} | error={str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/delete-folder', methods=['POST'])
def delete_folder():
    """Delete a folder"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}
        folder_path = data.get('folder_path', '').strip()
        
        logger.info(f"[DELETE_FOLDER] START | user={user_id} | path={folder_path}")
        
        if not folder_path:
            logger.warning(f"[DELETE_FOLDER] FAIL | user={user_id} | reason=empty_path")
            return jsonify({"success": False, "error": "folder_path is required"}), 400
        
        result = get_storage().delete(user_id, folder_path, is_folder=True)
        
        if result['success']:
            logger.info(f"[DELETE_FOLDER] SUCCESS | user={user_id} | path={folder_path}")
        else:
            logger.warning(f"[DELETE_FOLDER] FAIL | user={user_id} | path={folder_path} | error={result.get('error')}")
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"[DELETE_FOLDER] EXCEPTION | user={user_id} | path={folder_path} | error={str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/delete-file', methods=['POST'])
def delete_file():
    """Delete a file"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}
        file_path = data.get('file_path', '').strip()
        
        logger.info(f"[DELETE_FILE] START | user={user_id} | path={file_path}")

        if not file_path:
            logger.warning(f"[DELETE_FILE] FAIL | user={user_id} | reason=empty_path")
            return jsonify({"success": False, "error": "file_path is required"}), 400

        result = get_storage().delete(user_id, file_path)
        
        if result['success']:
            logger.info(f"[DELETE_FILE] SUCCESS | user={user_id} | path={file_path}")
        else:
            logger.warning(f"[DELETE_FILE] FAIL | user={user_id} | path={file_path} | error={result.get('error')}")
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"[DELETE_FILE] EXCEPTION | user={user_id} | path={file_path} | error={str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/upload-file', methods=['POST'])
def upload_file():
    """Upload a file to a folder"""
    try:
        user_id = get_user_id_from_request()
        folder_path = request.form.get('folder_path', '').strip()
        
        if 'file' not in request.files:
            logger.warning(f"[UPLOAD_FILE] FAIL | user={user_id} | reason=no_file")
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning(f"[UPLOAD_FILE] FAIL | user={user_id} | reason=empty_filename")
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"[UPLOAD_FILE] FAIL | user={user_id} | file={file.filename} | reason=unsupported_extension")
            return jsonify({
                "success": False,
                "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        logger.info(f"[UPLOAD_FILE] START | user={user_id} | file={file.filename} | folder={folder_path} | size={file.content_length or 0}")
        
        filename = secure_filename(file.filename)
        if not PathValidator.is_valid_filename(filename):
            logger.warning(f"[UPLOAD_FILE] FAIL | user={user_id} | file={filename} | reason=invalid_name")
            return jsonify({
                "success": False,
                "error": "Invalid filename. Names must be 1-250 characters and avoid special characters."
            }), 400

        result = get_storage().upload(user_id, folder_path, filename, file)
        
        if result['success']:
            logger.info(f"[UPLOAD_FILE] SUCCESS | user={user_id} | file={filename} | folder={folder_path}")
        else:
            logger.warning(f"[UPLOAD_FILE] FAIL | user={user_id} | file={filename} | error={result.get('error')}")
        
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        logger.error(f"[UPLOAD_FILE] EXCEPTION | user={user_id} | error={str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/list', methods=['GET'])
def list_contents():
    """List files and folders in a directory"""
    try:
        user_id = get_user_id_from_request()
        folder_path = request.args.get('folder_path', request.args.get('path', '')).strip()
        
        logger.debug(f"[LIST] START | user={user_id} | path={folder_path or 'root'}")
        
        result = get_storage().list(user_id, folder_path)
        
        if result['success']:
            file_count = len(result.get('files', []))
            folder_count = len(result.get('folders', []))
            logger.debug(f"[LIST] SUCCESS | user={user_id} | path={folder_path or 'root'} | files={file_count} | folders={folder_count}")
        else:
            logger.warning(f"[LIST] FAIL | user={user_id} | path={folder_path} | error={result.get('error')}")
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"[LIST] EXCEPTION | user={user_id} | path={folder_path} | error={str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/rename', methods=['POST'])
def rename_item():
    """Rename a file or folder"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}
        item_path = data.get('item_path', '').strip()
        new_name = data.get('new_name', '').strip()
        
        logger.info(f"[RENAME] START | user={user_id} | path={item_path} | new_name={new_name}")
        
        if not item_path or not new_name:
            logger.warning(f"[RENAME] FAIL | user={user_id} | reason=missing_params")
            return jsonify({"success": False, "error": "item_path and new_name are required"}), 400
        
        result = get_storage().rename(user_id, item_path, new_name)
        
        if result['success']:
            logger.info(f"[RENAME] SUCCESS | user={user_id} | old_path={item_path} | new_name={new_name}")
        else:
            logger.warning(f"[RENAME] FAIL | user={user_id} | path={item_path} | error={result.get('error')}")
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"[RENAME] EXCEPTION | user={user_id} | path={item_path} | error={str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/storage-stats', methods=['GET'])
def storage_stats():
    """Get storage statistics"""
    try:
        user_id = get_user_id_from_request()
        result = get_storage().get_stats(user_id)
        
        if not result.get('success'):
            return jsonify(result), 400
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error in storage_stats: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/download/<path:file_path>', methods=['GET'])
def download_file(file_path):
    """Download or preview a file (proxy content through backend)"""
    try:
        import mimetypes
        import requests as req_lib

        user_id = get_user_id_from_request()
        result = get_storage().download(user_id, file_path)

        if isinstance(result, str) and result.startswith('http'):
            # Stream the content from HF instead of redirecting.
            # This ensures PDFs/images render in the browser preview
            # (HF raw URLs serve Content-Disposition: attachment).
            try:
                headers = {}
                if HF_TOKEN:
                    headers['Authorization'] = f'Bearer {HF_TOKEN}'
                
                hf_resp = req_lib.get(result, stream=True, timeout=30, headers=headers)
                hf_resp.raise_for_status()

                content_type = hf_resp.headers.get('Content-Type', 'application/octet-stream')

                # Override content-disposition so browser renders inline
                guessed_type, _ = mimetypes.guess_type(file_path)
                if guessed_type:
                    content_type = guessed_type
                else:
                    # Manual fallbacks for common types often missing in basic mimetypes
                    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
                    if ext == 'md': content_type = 'text/markdown'
                    elif ext == 'txt': content_type = 'text/plain'
                    elif ext == 'json': content_type = 'application/json'
                    elif ext == 'csv': content_type = 'text/csv'

                as_download = request.args.get('download', 'false').lower() == 'true'
                disposition = 'attachment' if as_download else 'inline'
                filename = file_path.split('/')[-1]

                response = Response(
                    stream_with_context(hf_resp.iter_content(chunk_size=8192)),
                    content_type=content_type,
                    headers={
                        'Content-Disposition': f'{disposition}; filename="{filename}"',
                        'Cache-Control': 'public, max-age=3600',
                    }
                )
                return response
            except Exception as proxy_err:
                logger.warning(f"Proxy stream failed, falling back to redirect: {str(proxy_err)}")
                from flask import redirect
                return redirect(result)

        guessed_type, _ = mimetypes.guess_type(file_path)
        as_download = request.args.get('download', 'false').lower() == 'true'
        filename = file_path.split('/')[-1]

        response = send_file(
            result,
            mimetype=guessed_type or 'application/octet-stream',
            as_attachment=as_download,
            download_name=filename
        )
        response.headers['Content-Disposition'] = f'{"attachment" if as_download else "inline"}; filename="{filename}"'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    except Exception as e:
        logger.error(f"Error in download_file: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/history', methods=['GET'])
def get_history():
    """Get version history for a file"""
    try:
        user_id = get_user_id_from_request()
        path = request.args.get('path', '').strip()
        
        if not path:
            return jsonify({"success": False, "error": "path is required"}), 400
            
        history = get_storage().get_history(user_id, path)
        return jsonify({"success": True, "history": history}), 200
    except Exception as e:
        logger.error(f"Error in get_history: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/restore', methods=['POST'])
def restore_version():
    """Restore a file to a specific revision"""
    try:
        user_id = get_user_id_from_request()
        data = request.get_json() or {}
        path = data.get('path', '').strip()
        revision = data.get('revision', '').strip()
        as_copy = data.get('as_copy', False)
        
        if not path or not revision:
            return jsonify({"success": False, "error": "path and revision are required"}), 400
            
        result = get_storage().restore(user_id, path, revision, as_copy=as_copy)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error in restore_version: {str(e)}")
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
