"""Utility functions for path validation and security"""

import os
import re

try:
    from .. import config
except ImportError:
    import server.config as config

class PathValidator:
    """Validates and sanitizes file paths to prevent vulnerabilities"""

    @staticmethod
    def _normalize_relative_path(path: str) -> str:
        """Normalize relative path separators and remove duplicate separators"""
        if not isinstance(path, str):
            return ''
        return re.sub(r'[\\/]+', '/', path).strip('/ ')

    @staticmethod
    def is_valid_filename(filename: str) -> bool:
        """
        Check if filename contains only allowed characters.
        Prevents path traversal attacks and follows cross-platform naming rules.
        """
        if not filename or not isinstance(filename, str):
            return False
            
        filename = filename.strip()
        if not filename or len(filename) > 250: # Slightly under 255 for buffer
            return False
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
            
        # Reserved characters for Windows/Linux/Cloud safety
        # < > : " / \ | ? * and control chars
        invalid_chars = set('<>:"/\\|?*')
        if any((c in invalid_chars or ord(c) < 32) for c in filename):
            return False
        
        # Check for reserved names (Windows)
        reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                    'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                    'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        
        # Handle extensions in reserved check (e.g., CON.txt is invalid)
        base_name = filename.split('.')[0].upper()
        if base_name in reserved:
            return False
            
        return True

    @staticmethod
    def is_valid_path(user_id: str, path: str) -> bool:
        """
        Validate that path is safe and within user directory.
        Prevents accessing files outside user's data directory.
        """
        if not user_id or not isinstance(user_id, str):
            return False
        
        normalized_path = PathValidator._normalize_relative_path(path or '')
        
        user_dir = os.path.normpath(os.path.join(config.DATA_DIR, user_id))
        requested_path = os.path.normpath(os.path.join(user_dir, normalized_path))
        
        try:
            return os.path.commonpath([requested_path, user_dir]) == user_dir
        except ValueError:
            return False

    @staticmethod
    def get_safe_path(user_id: str, relative_path: str = "") -> str:
        """Get a validated absolute path within user's directory"""
        normalized_path = PathValidator._normalize_relative_path(relative_path)
        if not PathValidator.is_valid_path(user_id, normalized_path):
            raise ValueError(f"Invalid path: {relative_path}")
        
        user_dir = os.path.join(config.DATA_DIR, user_id)
        if normalized_path:
            return os.path.normpath(os.path.join(user_dir, normalized_path))
        return os.path.normpath(user_dir)

    @staticmethod
    def validate_folder_structure(path_parts: list) -> bool:
        """Validate each part of a folder path"""
        return all(PathValidator.is_valid_filename(part) for part in path_parts if part)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing or replacing invalid characters"""
    if not filename: return "file"
    # Replace characters that are invalid on Windows/Linux or could be used for traversal
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    return sanitized if sanitized else "file"


def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except (OSError, IOError):
        return 0


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable size"""
    if size_bytes == 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1].lstrip('.').lower()
