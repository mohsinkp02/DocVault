"""HF-backed storage tests using mocks only, with no filesystem persistence dependency."""

import io
import unittest
from unittest.mock import MagicMock, patch

import server.config as config
import server.storage.factory as storage_factory
from server.storage.hf import HuggingFaceStorageManager


class HuggingFaceStorageManagerTest(unittest.TestCase):
    def setUp(self):
        self.original_mode = config.STORAGE_MODE
        self.original_token = config.HF_TOKEN
        self.original_repo = config.HF_REPO_ID
        self.original_repo_type = config.HF_REPO_TYPE
        storage_factory._storage_instance = None

        config.STORAGE_MODE = "HF"
        config.HF_TOKEN = "hf_test_token"
        config.HF_REPO_ID = "user/docvault-storage"
        config.HF_REPO_TYPE = "dataset"

    def tearDown(self):
        config.STORAGE_MODE = self.original_mode
        config.HF_TOKEN = self.original_token
        config.HF_REPO_ID = self.original_repo
        config.HF_REPO_TYPE = self.original_repo_type
        storage_factory._storage_instance = None

    @patch("server.storage.hf.HfApi")
    def test_create_folder_uploads_marker(self, mock_hf_api_cls):
        mock_api = MagicMock()
        mock_api.list_repo_files.return_value = []
        mock_hf_api_cls.return_value = mock_api

        storage = HuggingFaceStorageManager()
        result = storage.create_folder("u1", "docs/contracts")

        self.assertTrue(result["success"])
        mock_api.upload_file.assert_called_once()
        self.assertIn("docs/contracts/.gitkeep", mock_api.upload_file.call_args.kwargs["path_in_repo"])

    @patch("server.storage.hf.HfApi")
    def test_upload_duplicate_auto_renames(self, mock_hf_api_cls):
        mock_api = MagicMock()
        mock_api.list_repo_files.return_value = ["u1/docs/file.pdf"]
        mock_hf_api_cls.return_value = mock_api

        storage = HuggingFaceStorageManager()
        result = storage.upload("u1", "docs", "file.pdf", io.BytesIO(b"pdf-data"))

        self.assertTrue(result["success"])
        self.assertEqual(result["file"]["name"], "file_1.pdf")

    @patch("server.storage.hf.HfApi")
    def test_rename_folder_uses_commit_operations(self, mock_hf_api_cls):
        mock_api = MagicMock()
        mock_api.list_repo_files.return_value = [
            "u1/docs/.gitkeep",
            "u1/docs/report.txt",
        ]
        mock_hf_api_cls.return_value = mock_api

        storage = HuggingFaceStorageManager()
        result = storage.rename("u1", "docs", "archive")

        self.assertTrue(result["success"])
        mock_api.create_commit.assert_called_once()

    @patch("server.storage.hf.HfApi")
    def test_delete_folder_deletes_all_children(self, mock_hf_api_cls):
        mock_api = MagicMock()
        mock_api.list_repo_files.return_value = [
            "u1/docs/.gitkeep",
            "u1/docs/report.txt",
        ]
        mock_hf_api_cls.return_value = mock_api

        storage = HuggingFaceStorageManager()
        result = storage.delete("u1", "docs", is_folder=True)

        self.assertTrue(result["success"])
        mock_api.create_commit.assert_called_once()


class StorageFactoryGuardTest(unittest.TestCase):
    def test_local_mode_raises_explicit_error(self):
        original_mode = config.STORAGE_MODE
        try:
            config.STORAGE_MODE = "LOCAL"
            storage_factory._storage_instance = None
            with self.assertRaises(RuntimeError):
                storage_factory.get_storage()
        finally:
            config.STORAGE_MODE = original_mode
            storage_factory._storage_instance = None


if __name__ == "__main__":
    unittest.main()
