"""Local Storage Manager for DocVault"""

import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

from .interface import StorageInterface
try:
    from ..utils.validators import PathValidator, sanitize_filename, get_file_size, format_file_size
    from ..utils.logger import setup_logger
    from .. import config
except ImportError:
    from server.utils.validators import PathValidator, sanitize_filename, get_file_size, format_file_size
    from server.utils.logger import setup_logger
    import server.config as config

logger = setup_logger(__name__)

class LocalStorageManager(StorageInterface):
    """Manages file and folder operations on local disk"""

    def create_folder(self, user_id: str, folder_path: str) -> Dict[str, Any]:
        try:
            folder_path = PathValidator._normalize_relative_path(folder_path)
            if not folder_path:
                return {"success": False, "error": "folder_path is required", "code": "INVALID_PATH"}

            path_parts = folder_path.split('/')
            if not PathValidator.validate_folder_structure(path_parts):
                return {"success": False, "error": "Invalid folder name", "code": "INVALID_NAME"}

            safe_folder_path = PathValidator.get_safe_path(user_id, folder_path)
            if os.path.exists(safe_folder_path):
                return {"success": False, "error": "Folder already exists", "code": "FOLDER_EXISTS"}

            os.makedirs(safe_folder_path, exist_ok=False)
            marker_path = os.path.join(safe_folder_path, config.FOLDER_MARKER)
            with open(marker_path, 'wb') as marker:
                marker.write(b'')

            stat = os.stat(safe_folder_path)
            return {
                "success": True,
                "message": f"Folder created: {folder_path}",
                "folder": self.standardize_folder(
                    name=path_parts[-1],
                    path=folder_path,
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    storage_type="local"
                )
            }
        except Exception as e:
            logger.error(f"Local Create Folder Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def upload(self, user_id: str, folder_path: str, filename: str, file_obj: Any) -> Dict[str, Any]:
        try:
            folder_path = PathValidator._normalize_relative_path(folder_path)
            safe_filename = sanitize_filename(filename)
            safe_folder_path = PathValidator.get_safe_path(user_id, folder_path)
            
            os.makedirs(safe_folder_path, exist_ok=True)
            
            file_path = os.path.join(safe_folder_path, safe_filename)
            
            # Duplicate handling
            if os.path.exists(file_path):
                name, ext = os.path.splitext(safe_filename)
                counter = 1
                while os.path.exists(file_path):
                    safe_filename = f"{name}_{counter}{ext}"
                    file_path = os.path.join(safe_folder_path, safe_filename)
                    counter += 1

            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            if hasattr(file_obj, 'save'):
                file_obj.save(file_path)
            else:
                with open(file_path, 'wb') as f:
                    f.write(file_obj if isinstance(file_obj, bytes) else file_obj.read())
            
            file_size = get_file_size(file_path)
            stat = os.stat(file_path)
            
            return {
                "success": True,
                "message": f"File uploaded: {safe_filename}",
                "file": self.standardize_file(
                    name=safe_filename,
                    path=f"{folder_path}/{safe_filename}" if folder_path else safe_filename,
                    size=file_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    storage_type="local"
                )
            }
        except Exception as e:
            logger.error(f"Local Upload Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def download(self, user_id: str, file_path: str) -> Any:
        safe_path = PathValidator.get_safe_path(user_id, file_path)
        if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        return safe_path # Flask send_file handles the path

    def delete(self, user_id: str, path: str, is_folder: bool = False) -> Dict[str, Any]:
        try:
            safe_path = PathValidator.get_safe_path(user_id, path)
            if not os.path.exists(safe_path):
                return {"success": False, "error": "Path not found", "code": "FOLDER_NOT_FOUND" if is_folder else "FILE_NOT_FOUND"}
            
            if is_folder:
                if not os.path.isdir(safe_path):
                    return {"success": False, "error": "Not a folder"}
                shutil.rmtree(safe_path)
            else:
                if not os.path.isfile(safe_path):
                    return {"success": False, "error": "Not a file"}
                os.remove(safe_path)
                
            return {"success": True, "message": f"Deleted: {path}"}
        except Exception as e:
            logger.error(f"Local Delete Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def list(self, user_id: str, prefix: str = "") -> Dict[str, List[Dict[str, Any]]]:
        try:
            prefix = PathValidator._normalize_relative_path(prefix)
            safe_path = PathValidator.get_safe_path(user_id, prefix)
            
            if not os.path.exists(safe_path):
                return {"success": True, "folders": [], "files": []}
            
            folders = []
            files = []
            
            for item in os.listdir(safe_path):
                if item == config.FOLDER_MARKER: continue
                
                item_path = os.path.join(safe_path, item)
                rel_item_path = f"{prefix}/{item}" if prefix else item
                stat = os.stat(item_path)
                
                if os.path.isdir(item_path):
                    folders.append(self.standardize_folder(
                        name=item,
                        path=rel_item_path,
                        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        storage_type="local"
                    ))
                else:
                    files.append(self.standardize_file(
                        name=item,
                        path=rel_item_path,
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        storage_type="local",
                        modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
                    ))
            
            return {"success": True, "folders": folders, "files": files}
        except Exception as e:
            logger.error(f"Local List Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def rename(self, user_id: str, old_path: str, new_name: str) -> Dict[str, Any]:
        try:
            old_path = PathValidator._normalize_relative_path(old_path)
            safe_old_path = PathValidator.get_safe_path(user_id, old_path)
            
            if not os.path.exists(safe_old_path):
                return {"success": False, "error": "Item not found", "code": "NOT_FOUND"}
            
            if not PathValidator.is_valid_filename(new_name):
                return {"success": False, "error": "Invalid characters in new name", "code": "INVALID_NAME"}
            
            parent_dir = os.path.dirname(old_path)
            new_path_rel = os.path.join(parent_dir, new_name) if parent_dir else new_name
            safe_new_path = PathValidator.get_safe_path(user_id, new_path_rel)
            
            if os.path.exists(safe_new_path):
                return {"success": False, "error": "An item with this name already exists", "code": "CONFLICT"}
                
            os.rename(safe_old_path, safe_new_path)
            
            is_folder = os.path.isdir(safe_new_path)
            return {
                "success": True, 
                "message": f"Renamed to {new_name}",
                "item": {
                    "name": new_name,
                    "type": "folder" if is_folder else "file",
                    "path": new_path_rel.replace('\\', '/')
                }
            }
        except Exception as e:
            logger.error(f"Local Rename Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def exists(self, user_id: str, path: str) -> bool:
        try:
            safe_path = PathValidator.get_safe_path(user_id, path)
            return os.path.exists(safe_path)
        except:
            return False

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        try:
            user_dir = PathValidator.get_safe_path(user_id, "")
            total_size = 0
            total_files = 0
            total_folders = 0
            
            for dirpath, dirnames, filenames in os.walk(user_dir):
                total_folders += len(dirnames)
                for f in filenames:
                    if f != config.FOLDER_MARKER:
                        total_size += os.path.getsize(os.path.join(dirpath, f))
                        total_files += 1
            
            return {
                "success": True,
                "total_size": total_size,
                "total_size_formatted": format_file_size(total_size),
                "total_files": total_files,
                "total_folders": total_folders,
                "storage_type": "local"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_history(self, user_id: str, path: str) -> List[Dict[str, Any]]:
        # Local storage doesn't support versioning yet
        return []

    def restore(self, user_id: str, path: str, revision: str) -> Dict[str, Any]:
        return {"success": False, "error": "Versioning not supported on local storage"}
