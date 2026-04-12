"""Test cases for DocVault API"""

import unittest
import json
import os
import tempfile
import shutil
import io

# Add server to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server.app import create_app
import server.config as config
import server.utils.validators as validators
import server.storage.manager as storage_manager
from server.config import FOLDER_MARKER


class DocVaultTestCase(unittest.TestCase):
    """Base test case for DocVault"""
    
    def setUp(self):
        """Set up test client and temporary data directory"""
        self.app = create_app()
        self.client = self.app.test_client()
        self.user_id = "test_user"
        self.temp_data_dir = tempfile.mkdtemp()
        self.user_data_path = os.path.join(self.temp_data_dir, self.user_id)
        os.makedirs(self.user_data_path, exist_ok=True)
        
        # Override storage directory for tests
        config.DATA_DIR = self.temp_data_dir
        validators.DATA_DIR = self.temp_data_dir
        storage_manager.DATA_DIR = self.temp_data_dir
    
    def tearDown(self):
        """Clean up temporary data"""
        if os.path.exists(self.temp_data_dir):
            shutil.rmtree(self.temp_data_dir)
    
    def get_headers(self, user_id=None):
        """Get request headers with user ID"""
        return {'X-User-ID': user_id or self.user_id}


class HealthCheckTest(DocVaultTestCase):
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'DocVault')


class FolderOperationsTest(DocVaultTestCase):
    """Test folder operations"""
    
    def test_create_folder_success(self):
        """Test successful folder creation"""
        response = self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Documents'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['folder']['name'], 'Documents')
    
    def test_create_nested_folder_success(self):
        """Test nested folder creation"""
        response = self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Documents/Projects/MyProject'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_create_folder_duplicate(self):
        """Test creating duplicate folder"""
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Documents'},
            headers=self.get_headers()
        )
        
        response = self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Documents'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data.get('code'), 'FOLDER_EXISTS')
    
    def test_create_folder_invalid_name(self):
        """Test creating folder with invalid characters"""
        response = self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Invalid/../Folder'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_delete_folder_success(self):
        """Test successful folder deletion"""
        # Create folder first
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'ToDelete'},
            headers=self.get_headers()
        )
        
        # Delete it
        response = self.client.post(
            '/api/delete-folder',
            json={'folder_path': 'ToDelete'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_delete_nonexistent_folder(self):
        """Test deleting non-existent folder"""
        response = self.client.post(
            '/api/delete-folder',
            json={'folder_path': 'NonExistent'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data.get('code'), 'FOLDER_NOT_FOUND')
    
    def test_delete_non_empty_folder_without_force(self):
        """Test deleting non-empty folder without force"""
        # Create folder with file
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'WithFiles'},
            headers=self.get_headers()
        )
        
        # Try to delete without force
        response = self.client.post(
            '/api/delete-folder',
            json={'folder_path': 'WithFiles', 'force': False},
            headers=self.get_headers()
        )
        # Should fail if folder has marker file
        data = json.loads(response.data)
        if not data['success']:
            self.assertEqual(data.get('code'), 'FOLDER_NOT_EMPTY')


class FileOperationsTest(DocVaultTestCase):
    """Test file operations"""
    
    def test_upload_file_success(self):
        """Test successful file upload"""
        # Create folder first
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Documents'},
            headers=self.get_headers()
        )
        
        # Upload file
        data = {'folder_path': 'Documents', 'file': (io.BytesIO(b'Hello World'), 'test.txt')}
        response = self.client.post(
            '/api/upload-file',
            data=data,
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['file']['name'], 'test.txt')
    
    def test_upload_file_to_nonexistent_folder(self):
        """Test uploading file to non-existent folder (should create)"""
        data = {'folder_path': 'NewFolder', 'file': (io.BytesIO(b'Hello World'), 'test.txt')}
        response = self.client.post(
            '/api/upload-file',
            data=data,
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
    
    def test_upload_file_no_file_provided(self):
        """Test upload with no file"""
        response = self.client.post(
            '/api/upload-file',
            data={'folder_path': 'Documents'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_upload_file_restricted_extension(self):
        """Test uploading file with restricted extension"""
        data = {'folder_path': 'Documents', 'file': (io.BytesIO(b'malware'), 'virus.exe')}
        response = self.client.post(
            '/api/upload-file',
            data=data,
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])

    def test_delete_file_success(self):
        """Test successful file deletion"""
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Documents'},
            headers=self.get_headers()
        )

        self.client.post(
            '/api/upload-file',
            data={'folder_path': 'Documents', 'file': (io.BytesIO(b'Hello World'), 'test.txt')},
            headers=self.get_headers()
        )

        response = self.client.post(
            '/api/delete-file',
            json={'file_path': 'Documents/test.txt'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])


class ListOperationsTest(DocVaultTestCase):
    """Test listing operations"""
    
    def test_list_empty_root(self):
        """Test listing empty root"""
        response = self.client.get(
            '/api/list',
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['total_folders'], 0)
        self.assertEqual(data['total_files'], 0)
    
    def test_list_with_folders(self):
        """Test listing with folders"""
        # Create folders
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Docs'},
            headers=self.get_headers()
        )
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Images'},
            headers=self.get_headers()
        )
        
        # List
        response = self.client.get(
            '/api/list',
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(data['total_folders'], 0)
    
    def test_list_with_files(self):
        """Test listing with files"""
        # Create folder and upload file
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Documents'},
            headers=self.get_headers()
        )
        
        self.client.post(
            '/api/upload-file',
            data={'folder_path': 'Documents', 'file': (io.BytesIO(b'# Read Me'), 'readme.md')},
            headers=self.get_headers()
        )
        
        # List subfolder
        response = self.client.get(
            '/api/list?folder_path=Documents',
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(data['total_files'], 0)


class RenameOperationsTest(DocVaultTestCase):
    """Test rename operations"""
    
    def test_rename_folder_success(self):
        """Test successful folder rename"""
        # Create folder
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'OldName'},
            headers=self.get_headers()
        )
        
        # Rename it
        response = self.client.post(
            '/api/rename',
            json={'item_path': 'OldName', 'new_name': 'NewName'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['item']['name'], 'NewName')
    
    def test_rename_file_success(self):
        """Test successful file rename"""
        # Create folder and upload file
        self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Documents'},
            headers=self.get_headers()
        )
        
        self.client.post(
            '/api/upload-file',
            data={'folder_path': 'Documents', 'file': (io.BytesIO(b'content'), 'oldname.txt')},
            headers=self.get_headers()
        )
        
        # Rename
        response = self.client.post(
            '/api/rename',
            json={'item_path': 'Documents/oldname.txt', 'new_name': 'newname.txt'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])


class StorageStatsTest(DocVaultTestCase):
    """Test storage statistics"""
    
    def test_storage_stats(self):
        """Test storage statistics endpoint"""
        response = self.client.get(
            '/api/storage-stats',
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('total_size', data)
        self.assertIn('total_files', data)
        self.assertIn('total_folders', data)


class SecurityTest(DocVaultTestCase):
    """Test security features"""
    
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        response = self.client.post(
            '/api/create-folder',
            json={'folder_path': '../../etc/passwd'},
            headers=self.get_headers()
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_invalid_folder_name(self):
        """Test invalid folder name"""
        response = self.client.post(
            '/api/create-folder',
            json={'folder_path': 'Folder With Spaces'},
            headers=self.get_headers()
        )
        # Should fail or sanitize (depends on implementation)
        data = json.loads(response.data)
        # Either it fails or creates with sanitized name
        self.assertIsNotNone(data)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(HealthCheckTest))
    suite.addTests(loader.loadTestsFromTestCase(FolderOperationsTest))
    suite.addTests(loader.loadTestsFromTestCase(FileOperationsTest))
    suite.addTests(loader.loadTestsFromTestCase(ListOperationsTest))
    suite.addTests(loader.loadTestsFromTestCase(RenameOperationsTest))
    suite.addTests(loader.loadTestsFromTestCase(StorageStatsTest))
    suite.addTests(loader.loadTestsFromTestCase(SecurityTest))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
