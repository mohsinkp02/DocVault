"""Configuration settings for DocVault."""

import os

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
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'default-insecure-key-change-in-production')
JSONIFY_PRETTYPRINT_REGULAR = True

# API configuration
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'json', 'xml', 
    'csv', 'md', 'py', 'js', 'html', 'css', 'yml', 'yaml', 'gitkeep'
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

# Hugging Face Storage Configuration
STORAGE_MODE = os.getenv('STORAGE_MODE', 'HF').upper()
HF_TOKEN = os.getenv('HF_TOKEN', '')
HF_REPO_ID = os.getenv('HF_REPO_ID', 'mohsin-devs/DocVault-Storage')
HF_REPO_TYPE = os.getenv('HF_REPO_TYPE', 'dataset').lower()


def validate_runtime_configuration() -> None:
    """Fail fast unless the app is configured for permanent HF-backed storage."""
    if STORAGE_MODE != 'HF':
        raise RuntimeError(
            "DocVault requires permanent Hugging Face storage. "
            "Set STORAGE_MODE=HF and configure the HF_* environment variables."
        )

    missing = []
    if not HF_TOKEN:
        missing.append('HF_TOKEN')
    if not HF_REPO_ID:
        missing.append('HF_REPO_ID')
    if not HF_REPO_TYPE:
        missing.append('HF_REPO_TYPE')

    if missing:
        raise RuntimeError(
            "Missing required Hugging Face configuration: " + ", ".join(missing)
        )

    if HF_REPO_TYPE not in {'dataset', 'model'}:
        raise RuntimeError("HF_REPO_TYPE must be either 'dataset' or 'model'.")
