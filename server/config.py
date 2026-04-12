"""Configuration settings for DocVault"""

import os
from datetime import timedelta

# Base configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Storage configuration
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Flask configuration
DEBUG = True
SECRET_KEY = os.getenv('SECRET_KEY', 'default-insecure-key-change-in-production')
JSONIFY_PRETTYPRINT_REGULAR = True

# API configuration
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'json', 'xml', 
    'csv', 'md', 'py', 'js', 'html', 'css', 'yml', 'yaml'
}

# Security
# - Only alphanumeric, hyphens, underscores for folder/file names
VALID_FILENAME_CHARS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.')

# Default user ID for offline use
DEFAULT_USER_ID = "default_user"

# Marker file for identifying folders in HF integration
FOLDER_MARKER = ".gitkeep"

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
