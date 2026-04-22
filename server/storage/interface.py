"""Storage Interface for DocVault"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class StorageInterface(ABC):
    """
    Standard interface for all storage backends (Local, Hugging Face, etc.)
    Ensures identical behavior and standardized return structures.
    """

    @abstractmethod
    def create_folder(self, user_id: str, folder_path: str) -> Dict[str, Any]:
        """
        Create a folder path, including nested folders if needed.
        """
        pass

    @abstractmethod
    def upload(self, user_id: str, folder_path: str, filename: str, file_obj: Any) -> Dict[str, Any]:
        """
        Upload a file to storage.
        Returns a standardized file object.
        """
        pass

    @abstractmethod
    def download(self, user_id: str, file_path: str) -> Any:
        """
        Download a file from storage.
        Returns bytes or a file-like object.
        """
        pass

    @abstractmethod
    def delete(self, user_id: str, path: str, is_folder: bool = False) -> Dict[str, Any]:
        """
        Delete a file or folder.
        """
        pass

    @abstractmethod
    def list(self, user_id: str, prefix: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """
        List files and folders at the given prefix.
        Returns a dictionary with 'files' and 'folders' lists of standardized objects.
        """
        pass

    @abstractmethod
    def rename(self, user_id: str, old_path: str, new_name: str) -> Dict[str, Any]:
        """
        Rename a file or folder.
        """
        pass

    @abstractmethod
    def exists(self, user_id: str, path: str) -> bool:
        """
        Check if a path exists.
        """
        pass

    @abstractmethod
    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get storage statistics.
        """
        pass

    @abstractmethod
    def get_history(self, user_id: str, path: str) -> List[Dict[str, Any]]:
        """
        Get version history for a file.
        """
        pass

    @abstractmethod
    def restore(self, user_id: str, path: str, revision: str) -> Dict[str, Any]:
        """
        Restore a file to a specific revision.
        """
        pass

    def standardize_file(self, name: str, path: str, size: int, created_at: str, storage_type: str, modified_at: Optional[str] = None) -> Dict[str, Any]:
        """Helper to create a standardized file object"""
        return {
            "name": name,
            "path": path,
            "size": size,
            "type": "file",
            "created_at": created_at,
            "modified_at": modified_at or created_at,
            "storage": storage_type
        }

    def standardize_folder(self, name: str, path: str, created_at: str, storage_type: str) -> Dict[str, Any]:
        """Helper to create a standardized folder object"""
        return {
            "name": name,
            "path": path,
            "type": "folder",
            "created_at": created_at,
            "storage": storage_type
        }
