"""Storage Factory for DocVault."""

import server.config as config
from server.storage.hf import HuggingFaceStorageManager

_storage_instance = None

def get_storage():
    """Return the singleton HF storage backend or fail loudly."""
    global _storage_instance
    config.validate_runtime_configuration()
    if _storage_instance is None:
        _storage_instance = HuggingFaceStorageManager()
    return _storage_instance
