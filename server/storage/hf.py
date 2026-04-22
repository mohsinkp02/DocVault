"""Hugging Face Hub Storage Manager for DocVault (Optimized)"""

import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from huggingface_hub import HfApi, CommitOperationAdd, CommitOperationDelete, CommitOperationCopy

from .interface import StorageInterface
try:
    from ..utils.validators import PathValidator, sanitize_filename, format_file_size
    from ..utils.logger import setup_logger
    from .. import config
except ImportError:
    from server.utils.validators import PathValidator, sanitize_filename, format_file_size
    from server.utils.logger import setup_logger
    import server.config as config

logger = setup_logger(__name__)

class HuggingFaceStorageManager(StorageInterface):
    """Manages file and folder operations in Hugging Face Hub (simulated folders)"""

    def __init__(self):
        self.api = HfApi(token=config.HF_TOKEN)
        self._ensure_repo_exists()
        
        # Caching layer
        self._cache = {} # Key: user_id:prefix, Value: {data, timestamp}
        self._cache_ttl = 60 # 60 seconds
        self._full_repo_files_cache = None # Optionally cache all files
        self._repo_files_ts = 0

    def _ensure_repo_exists(self):
        try:
            self.api.repo_info(repo_id=config.HF_REPO_ID, repo_type=config.HF_REPO_TYPE)
        except Exception:
            try:
                self.api.create_repo(
                    repo_id=config.HF_REPO_ID, 
                    repo_type=config.HF_REPO_TYPE,
                    private=True,
                    exist_ok=True
                )
            except Exception as e:
                logger.error(f"HF Repo Creation Error: {str(e)}")

    def _clear_cache(self):
        """Invalidate all caches on write"""
        self._cache = {}
        self._full_repo_files_cache = None
        self._repo_files_ts = 0
        logger.debug("HF Cache invalidated")

    def _repo_path(self, user_id: str, relative_path: str = "") -> str:
        relative_path = PathValidator._normalize_relative_path(relative_path)
        return f"{user_id}/{relative_path}".strip("/")

    def _folder_marker_path(self, user_id: str, folder_path: str) -> str:
        base = self._repo_path(user_id, folder_path)
        return f"{base}/{config.FOLDER_MARKER}".strip("/")

    def _list_repo_files(self) -> List[str]:
        if self._full_repo_files_cache and (time.time() - self._repo_files_ts < self._cache_ttl):
            return self._full_repo_files_cache

        files = self.api.list_repo_files(repo_id=config.HF_REPO_ID, repo_type=config.HF_REPO_TYPE)
        self._full_repo_files_cache = files
        self._repo_files_ts = time.time()
        return files

    def _resolve_duplicate_file_path(self, repo_files: List[str], desired_path: str) -> str:
        if desired_path not in repo_files:
            return desired_path

        stem, ext = os.path.splitext(desired_path)
        counter = 1
        candidate = f"{stem}_{counter}{ext}"
        while candidate in repo_files:
            counter += 1
            candidate = f"{stem}_{counter}{ext}"
        return candidate

    def create_folder(self, user_id: str, folder_path: str) -> Dict[str, Any]:
        try:
            self._clear_cache()
            folder_path = PathValidator._normalize_relative_path(folder_path)
            if not folder_path:
                return {"success": False, "error": "folder_path is required", "code": "INVALID_PATH"}

            path_parts = folder_path.split('/')
            if not PathValidator.validate_folder_structure(path_parts):
                return {"success": False, "error": "Invalid folder name", "code": "INVALID_NAME"}

            repo_files = self._list_repo_files()
            repo_folder_path = self._repo_path(user_id, folder_path)
            marker_path = self._folder_marker_path(user_id, folder_path)

            if marker_path in repo_files or any(f.startswith(repo_folder_path + "/") for f in repo_files):
                return {"success": False, "error": "Folder already exists", "code": "FOLDER_EXISTS"}

            self.api.upload_file(
                path_or_fileobj=b"",
                path_in_repo=marker_path,
                repo_id=config.HF_REPO_ID,
                repo_type=config.HF_REPO_TYPE,
                commit_message=f"Create folder: {folder_path}"
            )

            return {
                "success": True,
                "message": f"Folder created: {folder_path}",
                "folder": self.standardize_folder(
                    name=path_parts[-1],
                    path=folder_path,
                    created_at=datetime.now().isoformat(),
                    storage_type="hf"
                )
            }
        except Exception as e:
            logger.error(f"HF Create Folder Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def upload(self, user_id: str, folder_path: str, filename: str, file_obj: Any) -> Dict[str, Any]:
        try:
            self._clear_cache()
            folder_path = PathValidator._normalize_relative_path(folder_path)
            safe_filename = sanitize_filename(filename)
            hf_path = self._repo_path(user_id, f"{folder_path}/{safe_filename}" if folder_path else safe_filename)
            hf_path = self._resolve_duplicate_file_path(self._list_repo_files(), hf_path)
            
            if hasattr(file_obj, 'read'):
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
                file_data = file_obj.read()
            else:
                file_data = file_obj
            
            # Validate file_data is bytes
            if not isinstance(file_data, (bytes, bytearray)):
                raise TypeError(f"Expected bytes, got {type(file_data).__name__}")

            self.api.upload_file(
                path_or_fileobj=file_data,
                path_in_repo=hf_path,
                repo_id=config.HF_REPO_ID,
                repo_type=config.HF_REPO_TYPE,
                commit_message=f"Upload {safe_filename} to {folder_path or 'root'}"
            )
            
            file_size = len(file_data)
            final_name = hf_path.split('/')[-1]
            rel_path = hf_path[len(user_id) + 1:] if hf_path.startswith(user_id + "/") else hf_path
            return {
                "success": True,
                "message": f"Uploaded to HF: {final_name}",
                "file": self.standardize_file(
                    name=final_name,
                    path=rel_path,
                    size=file_size,
                    created_at=datetime.now().isoformat(),
                    storage_type="hf"
                )
            }
        except Exception as e:
            logger.error(f"HF Upload Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def download(self, user_id: str, file_path: str) -> Any:
        from urllib.parse import quote
        hf_path = self._repo_path(user_id, file_path)
        encoded_path = quote(hf_path)
        repo_type_prefix = "datasets/" if config.HF_REPO_TYPE == "dataset" else ""
        return f"https://huggingface.co/{repo_type_prefix}{config.HF_REPO_ID}/resolve/main/{encoded_path}"

    def delete(self, user_id: str, path: str, is_folder: bool = False) -> Dict[str, Any]:
        try:
            self._clear_cache()
            prefix = self._repo_path(user_id, path)
            repo_files = self._list_repo_files()
            
            if is_folder:
                folder_prefix = prefix + "/"
                operations = []
                for f in repo_files:
                    if f.startswith(folder_prefix):
                        operations.append(CommitOperationDelete(path_in_repo=f))
                
                if not operations:
                    return {"success": False, "error": "Folder not found", "code": "FOLDER_NOT_FOUND"}

                self.api.create_commit(
                    repo_id=config.HF_REPO_ID,
                    repo_type=config.HF_REPO_TYPE,
                    operations=operations,
                    commit_message=f"Delete folder: {path}"
                )
                return {"success": True, "message": f"Deleted folder and its contents from HF"}
            else:
                if prefix not in repo_files:
                    return {"success": False, "error": "File not found", "code": "FILE_NOT_FOUND"}
                self.api.delete_file(
                    path_in_repo=prefix,
                    repo_id=config.HF_REPO_ID,
                    repo_type=config.HF_REPO_TYPE,
                    commit_message=f"Delete file: {path}"
                )
                return {"success": True, "message": f"Deleted file from HF: {path}"}
        except Exception as e:
            logger.error(f"HF Delete Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def list(self, user_id: str, prefix: str = "") -> Dict[str, List[Dict[str, Any]]]:
        try:
            prefix = PathValidator._normalize_relative_path(prefix)
            cache_key = f"{user_id}:{prefix}"
            
            # Check cache
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if time.time() - entry['timestamp'] < self._cache_ttl:
                    logger.debug(f"Serving from HF cache: {cache_key}")
                    return entry['data']
            
            repo_prefix = f"{user_id}/{prefix}".strip("/")
            search_prefix = repo_prefix + "/" if repo_prefix else f"{user_id}/"
            
            files_info = self._list_repo_files()
            
            folders_set = set()
            files = []
            
            for f in files_info:
                if not f.startswith(f"{user_id}/"): continue
                
                if f.startswith(search_prefix):
                    rel_part = f[len(search_prefix):]
                    if not rel_part: continue
                    
                    parts = rel_part.split('/')
                    if len(parts) > 1:
                        folders_set.add(parts[0])
                    else:
                        if parts[0] == config.FOLDER_MARKER:
                            continue
                        
                        files.append(self.standardize_file(
                            name=parts[0],
                            path=f"{prefix}/{parts[0]}" if prefix else parts[0],
                            size=0, # Placeholder (list_repo_files doesn't give stats)
                            created_at=datetime.now().isoformat(),
                            storage_type="hf"
                        ))
            
            folders = [self.standardize_folder(
                name=name,
                path=f"{prefix}/{name}" if prefix else name,
                created_at=datetime.now().isoformat(),
                storage_type="hf"
            ) for name in folders_set]
            
            folders.sort(key=lambda x: x['name'].lower())
            files.sort(key=lambda x: x['name'].lower())
            
            result = {"success": True, "folders": folders, "files": files}
            
            # Store in cache
            self._cache[cache_key] = {"data": result, "timestamp": time.time()}
            
            return result
        except Exception as e:
            logger.error(f"HF List Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def rename(self, user_id: str, old_path: str, new_name: str) -> Dict[str, Any]:
        """Atomic rename using create_commit with batch operations"""
        try:
            self._clear_cache()
            old_path = PathValidator._normalize_relative_path(old_path)
            hf_old_path = self._repo_path(user_id, old_path)
            
            if not PathValidator.is_valid_filename(new_name):
                return {"success": False, "error": "Invalid characters in name", "code": "INVALID_NAME"}

            parent = os.path.dirname(old_path)
            new_item_path = f"{parent}/{new_name}" if parent else new_name
            hf_new_path = self._repo_path(user_id, new_item_path)
            
            all_files = self._list_repo_files()
            
            # Check if destination already exists
            if hf_new_path in all_files or any(f.startswith(hf_new_path + "/") for f in all_files):
                return {"success": False, "error": "An item with this name already exists", "code": "CONFLICT"}

            operations = []
            if hf_old_path in all_files:
                # rename single file
                operations.append(CommitOperationCopy(src_path=hf_old_path, path_in_repo=hf_new_path))
                operations.append(CommitOperationDelete(path_in_repo=hf_old_path))
            else:
                # rename folder (move all prefixes)
                folder_old_prefix = hf_old_path + "/"
                folder_new_prefix = hf_new_path + "/"
                found = False
                for f in all_files:
                    if f.startswith(folder_old_prefix):
                        found = True
                        rel = f[len(folder_old_prefix):]
                        operations.append(CommitOperationCopy(src_path=f, path_in_repo=folder_new_prefix + rel))
                        operations.append(CommitOperationDelete(path_in_repo=f))
                
                if not found:
                    return {"success": False, "error": "Item not found", "code": "NOT_FOUND"}
            
            if operations:
                self.api.create_commit(
                    repo_id=config.HF_REPO_ID,
                    repo_type=config.HF_REPO_TYPE,
                    operations=operations,
                    commit_message=f"Atomic Move: {old_path} -> {new_item_path}"
                )
                return {
                    "success": True, 
                    "message": f"Renamed to {new_name}",
                    "item": {
                        "name": new_name,
                        "path": new_item_path.replace('\\', '/')
                    }
                }
                
            return {"success": False, "error": "Item not found", "code": "NOT_FOUND"}
        except Exception as e:
            logger.error(f"HF Rename Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def exists(self, user_id: str, path: str) -> bool:
        try:
            hf_path = self._repo_path(user_id, path)
            files = self._list_repo_files()
            return hf_path in files or any(f.startswith(hf_path + "/") for f in files)
        except:
            return False

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        try:
            files = [f for f in self._list_repo_files() if f.startswith(f"{user_id}/")]
            return {
                "success": True,
                "total_files": len(files),
                "storage_type": "hf",
                "repo_id": config.HF_REPO_ID
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_history(self, user_id: str, path: str) -> List[Dict[str, Any]]:
        try:
            hf_path = self._repo_path(user_id, path)
            # Use list_repo_commits with path filtering
            commits = self.api.list_repo_commits(repo_id=config.HF_REPO_ID, repo_type=config.HF_REPO_TYPE, path=hf_path)
            
            history = []
            for c in commits:
                history.append({
                    "id": c.commit_id,
                    "message": c.message,
                    "timestamp": c.created_at.isoformat(),
                    "author": c.authors[0] if c.authors else "unknown"
                })
            return history
        except Exception as e:
            logger.error(f"HF History Error: {str(e)}")
            return []

    def restore(self, user_id: str, path: str, revision: str, as_copy: bool = False) -> Dict[str, Any]:
        """Restore file, either overwriting or creating a timestamped copy"""
        try:
            self._clear_cache()
            hf_path = self._repo_path(user_id, path)
            
            dest_path = hf_path
            if as_copy:
                name, ext = os.path.splitext(path)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                new_path = f"{name}_{timestamp}{ext}"
                dest_path = self._repo_path(user_id, new_path)
            
            # Using create_commit with CommitOperationCopy to restore without download/upload
            op = CommitOperationCopy(
                src_path=hf_path,
                path_in_repo=dest_path,
                src_revision=revision
            )
            
            self.api.create_commit(
                repo_id=config.HF_REPO_ID,
                repo_type=config.HF_REPO_TYPE,
                operations=[op],
                commit_message=f"Restored {path} from {revision[:7]}" + (f" as {os.path.basename(dest_path)}" if as_copy else ""),
            )
            
            return {
                "success": True, 
                "message": f"Restored {path} successfully",
                "item": {
                    "name": os.path.basename(dest_path),
                    "path": dest_path[len(user_id)+1:] if dest_path.startswith(user_id + "/") else dest_path
                }
            }
        except Exception as e:
            logger.error(f"HF Restore Error: {str(e)}")
            return {"success": False, "error": str(e)}
