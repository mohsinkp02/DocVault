"""Storage management module for DocVault"""

import os
import shutil
from datetime import datetime

try:
    from ..utils.validators import PathValidator, sanitize_filename, get_file_size, format_file_size
    from ..utils.logger import setup_logger
    from .. import config
except ImportError:
    from utils.validators import PathValidator, sanitize_filename, get_file_size, format_file_size
    from utils.logger import setup_logger
    import config

logger = setup_logger(__name__)


class StorageManager:
    """Manages file and folder operations in local storage"""

    @staticmethod
    def delete_file(user_id: str, file_path: str) -> dict:
        """Delete a file from local storage."""
        try:
            file_path = PathValidator._normalize_relative_path(file_path)
            if not PathValidator.is_valid_path(user_id, file_path):
                return {"success": False, "error": "Invalid file path"}

            safe_path = PathValidator.get_safe_path(user_id, file_path)

            if not os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "code": "FILE_NOT_FOUND"
                }

            if not os.path.isfile(safe_path):
                return {"success": False, "error": "Path is not a file"}

            os.remove(safe_path)
            logger.info(f"Deleted file: {user_id}/{file_path}")
            return {
                "success": True,
                "message": f"File deleted: {file_path}"
            }

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_folder(user_id: str, folder_path: str) -> dict:
        """
        Create a folder (including nested folders).
        
        Args:
            user_id: User identifier
            folder_path: Folder path (can be nested like "Documents/Projects")
        
        Returns:
            dict with status and folder info
        """
        try:
            folder_path = PathValidator._normalize_relative_path(folder_path)
            # Validate path
            if not PathValidator.is_valid_path(user_id, folder_path):
                return {"success": False, "error": "Invalid folder path"}
            
            # Validate each part of the path
            parts = [p for p in folder_path.split('/') if p]
            if not PathValidator.validate_folder_structure(parts):
                return {"success": False, "error": "Invalid folder name characters"}
            
            # Get safe absolute path
            safe_path = PathValidator.get_safe_path(user_id, folder_path)
            
            # Check if already exists
            if os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": f"Folder already exists: {folder_path}",
                    "code": "FOLDER_EXISTS"
                }
            
            # Create folder
            os.makedirs(safe_path, exist_ok=True)
            
            # Create marker file for HF integration compatibility
            marker_path = os.path.join(safe_path, config.FOLDER_MARKER)
            if not os.path.exists(marker_path):
                with open(marker_path, 'a', encoding='utf-8'):
                    pass
            
            logger.info(f"Created folder: {user_id}/{folder_path}")
            
            return {
                "success": True,
                "message": f"Folder created: {folder_path}",
                "folder": {
                    "name": os.path.basename(safe_path),
                    "path": folder_path,
                    "created_at": datetime.now().isoformat(),
                    "type": "folder"
                }
            }
        
        except Exception as e:
            logger.error(f"Error creating folder {folder_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_folder(user_id: str, folder_path: str, force: bool = False) -> dict:
        """
        Delete a folder (including non-empty folders if force=True).
        
        Args:
            user_id: User identifier
            folder_path: Folder path to delete
            force: If True, delete non-empty folders
        
        Returns:
            dict with status
        """
        try:
            folder_path = PathValidator._normalize_relative_path(folder_path)
            # Validate path
            if not PathValidator.is_valid_path(user_id, folder_path):
                return {"success": False, "error": "Invalid folder path"}
            
            safe_path = PathValidator.get_safe_path(user_id, folder_path)
            
            # Check if exists
            if not os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": f"Folder not found: {folder_path}",
                    "code": "FOLDER_NOT_FOUND"
                }
            
            # Check if it's a folder
            if not os.path.isdir(safe_path):
                return {"success": False, "error": "Path is not a folder"}
            
            # Check if empty
            contents = os.listdir(safe_path)
            # Filter out marker file
            contents = [f for f in contents if f != config.FOLDER_MARKER]
            
            if contents and not force:
                return {
                    "success": False,
                    "error": "Folder is not empty. Use force=true to delete",
                    "code": "FOLDER_NOT_EMPTY",
                    "item_count": len(contents)
                }
            
            # Delete folder
            if force or not contents:
                shutil.rmtree(safe_path)
                logger.info(f"Deleted folder: {user_id}/{folder_path}")
                return {
                    "success": True,
                    "message": f"Folder deleted: {folder_path}"
                }
        
        except Exception as e:
            logger.error(f"Error deleting folder {folder_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def upload_file(user_id: str, folder_path: str, filename: str, file_obj) -> dict:
        """
        Upload and save file to specific folder.
        
        Args:
            user_id: User identifier
            folder_path: Destination folder path
            filename: Original filename
            file_obj: File object to save
        
        Returns:
            dict with status and file info
        """
        try:
            folder_path = PathValidator._normalize_relative_path(folder_path)
            # Sanitize filename
            safe_filename = sanitize_filename(filename)
            if not PathValidator.is_valid_filename(safe_filename):
                return {"success": False, "error": "Invalid filename"}
            
            # Validate folder path
            if not PathValidator.is_valid_path(user_id, folder_path):
                return {"success": False, "error": "Invalid folder path"}
            
            safe_folder_path = PathValidator.get_safe_path(user_id, folder_path)
            
            # Create folder if it doesn't exist
            if not os.path.exists(safe_folder_path):
                os.makedirs(safe_folder_path, exist_ok=True)
                # Create marker file
                marker_path = os.path.join(safe_folder_path, config.FOLDER_MARKER)
                with open(marker_path, 'a', encoding='utf-8'):
                    pass
            
            # Full file path
            file_path = os.path.join(safe_folder_path, safe_filename)
            
            # Handle duplicate filenames
            if os.path.exists(file_path):
                name, ext = os.path.splitext(safe_filename)
                counter = 1
                while os.path.exists(file_path):
                    safe_filename = f"{name}_{counter}{ext}"
                    file_path = os.path.join(safe_folder_path, safe_filename)
                    counter += 1
            
            # Save file
            file_obj.seek(0)
            file_obj.save(file_path)
            
            file_size = get_file_size(file_path)
            logger.info(f"Uploaded file: {user_id}/{folder_path}/{safe_filename} ({format_file_size(file_size)})")
            
            return {
                "success": True,
                "message": f"File uploaded: {safe_filename}",
                "file": {
                    "name": safe_filename,
                    "path": f"{folder_path}/{safe_filename}",
                    "size": file_size,
                    "size_formatted": format_file_size(file_size),
                    "uploaded_at": datetime.now().isoformat(),
                    "type": "file"
                }
            }
        
        except Exception as e:
            logger.error(f"Error uploading file to {folder_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_contents(user_id: str, folder_path: str = "") -> dict:
        """
        List all files and folders in a directory.
        
        Args:
            user_id: User identifier
            folder_path: Folder to list (empty for root)
        
        Returns:
            dict with files and folders
        """
        try:
            folder_path = PathValidator._normalize_relative_path(folder_path)
            # Validate path
            if not PathValidator.is_valid_path(user_id, folder_path):
                return {"success": False, "error": "Invalid folder path"}
            
            safe_path = PathValidator.get_safe_path(user_id, folder_path)
            
            # Check if exists
            if not os.path.exists(safe_path):
                logger.warning(f"Attempted to list non-existent path: {user_id}/{folder_path}")
                return {
                    "success": True,
                    "path": folder_path or "/",
                    "folders": [],
                    "files": [],
                    "total_folders": 0,
                    "total_files": 0,
                    "summary": {
                        "total_folders": 0,
                        "total_files": 0
                    }
                }
            
            folders = []
            files = []
            
            # List contents
            for item in os.listdir(safe_path):
                # Skip marker files
                if item == config.FOLDER_MARKER:
                    continue
                
                item_path = os.path.join(safe_path, item)
                item_stat = os.stat(item_path)
                
                if os.path.isdir(item_path):
                    folders.append({
                        "name": item,
                        "type": "folder",
                        "path": f"{folder_path}/{item}" if folder_path else item,
                        "created_at": datetime.fromtimestamp(item_stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(item_stat.st_mtime).isoformat()
                    })
                else:
                    files.append({
                        "name": item,
                        "type": "file",
                        "path": f"{folder_path}/{item}" if folder_path else item,
                        "size": item_stat.st_size,
                        "size_formatted": format_file_size(item_stat.st_size),
                        "created_at": datetime.fromtimestamp(item_stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(item_stat.st_mtime).isoformat()
                    })
            
            # Sort by name
            folders.sort(key=lambda x: x['name'].lower())
            files.sort(key=lambda x: x['name'].lower())
            
            logger.info(f"Listed contents: {user_id}/{folder_path} ({len(folders)} folders, {len(files)} files)")
            
            return {
                "success": True,
                "path": folder_path or "/",
                "folders": folders,
                "files": files,
                "total_folders": len(folders),
                "total_files": len(files),
                "summary": {
                    "total_folders": len(folders),
                    "total_files": len(files)
                }
            }
        
        except Exception as e:
            logger.error(f"Error listing contents of {folder_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def rename_item(user_id: str, item_path: str, new_name: str) -> dict:
        """
        Rename a file or folder.
        
        Args:
            user_id: User identifier
            item_path: Current path to file/folder
            new_name: New name
        
        Returns:
            dict with status
        """
        try:
            item_path = PathValidator._normalize_relative_path(item_path)
            # Validate paths
            if not PathValidator.is_valid_path(user_id, item_path):
                return {"success": False, "error": "Invalid item path"}
            
            if not PathValidator.is_valid_filename(new_name):
                return {"success": False, "error": "Invalid new name"}
            
            # Get parent directory
            parent_path = os.path.dirname(item_path) if item_path else ""
            old_full_path = PathValidator.get_safe_path(user_id, item_path)
            new_full_path = os.path.join(
                PathValidator.get_safe_path(user_id, parent_path),
                new_name
            )
            
            # Check if exists
            if not os.path.exists(old_full_path):
                return {"success": False, "error": "Item not found"}
            
            # Check if new name already exists
            if os.path.exists(new_full_path):
                return {"success": False, "error": "Name already exists"}
            
            # Rename
            os.rename(old_full_path, new_full_path)
            
            item_type = "folder" if os.path.isdir(new_full_path) else "file"
            logger.info(f"Renamed {item_type}: {user_id}/{item_path} -> {new_name}")
            
            return {
                "success": True,
                "message": f"{item_type.capitalize()} renamed to: {new_name}",
                "item": {
                    "name": new_name,
                    "type": item_type,
                    "path": f"{parent_path}/{new_name}" if parent_path else new_name
                }
            }
        
        except Exception as e:
            logger.error(f"Error renaming item {item_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_storage_stats(user_id: str) -> dict:
        """Get storage statistics for a user"""
        try:
            user_dir = PathValidator.get_safe_path(user_id, "")
            
            if not os.path.exists(user_dir):
                return {
                    "success": True,
                    "total_size": 0,
                    "total_files": 0,
                    "total_folders": 0
                }
            
            total_size = 0
            total_files = 0
            total_folders = 0
            
            for dirpath, dirnames, filenames in os.walk(user_dir):
                total_folders += len(dirnames)
                for filename in filenames:
                    if filename != config.FOLDER_MARKER:
                        file_path = os.path.join(dirpath, filename)
                        total_size += get_file_size(file_path)
                        total_files += 1
            
            return {
                "success": True,
                "total_size": total_size,
                "total_size_formatted": format_file_size(total_size),
                "total_files": total_files,
                "total_folders": total_folders
            }
        
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {"success": False, "error": str(e)}
