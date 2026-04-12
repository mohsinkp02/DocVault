"""Utility functions for path validation and security"""

import os
import re

try:
    from .. import config
except ImportError:
    import config

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
        Prevents path traversal attacks.
        """
        if not filename or len(filename) > 255:
            return False
        
        # Check for path traversal attempts
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            return False
        
        # Check for reserved names (Windows)
        reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'LPT1', 'LPT2'}
        if filename.upper() in reserved:
            return False
        
        # Check characters
        return all(c in config.VALID_FILENAME_CHARS for c in filename)

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
    # Remove invalid characters
    sanitized = ''.join(c if c in config.VALID_FILENAME_CHARS else '_' for c in filename)
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
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1].lstrip('.').lower()
