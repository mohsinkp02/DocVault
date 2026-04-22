"""Storage Factory for DocVault"""

from .local import LocalStorageManager
from .hf import HuggingFaceStorageManager
try:
    from .. import config
except ImportError:
    import server.config as config

_storage_instance = None

def get_storage():
    """
    Factory function to get the configured storage manager instance.
    Implements a singleton pattern for the manager.
    """
    global _storage_instance
    if _storage_instance is None:
        if config.STORAGE_MODE == 'HF':
            _storage_instance = HuggingFaceStorageManager()
        else:
            _storage_instance = LocalStorageManager()
    return _storage_instance
