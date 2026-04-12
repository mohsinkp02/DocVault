---
title: DocVault App
emoji: 📁
colorFrom: blue
colorTo: purple
sdk: static
app_file: index.html
---

# DocVault - Offline-First Document Storage System

Complete offline-first document storage system built with **Python Flask** and local filesystem storage. No cloud dependencies, fully self-contained, and ready for future Hugging Face integration.

## 🎯 Features

### Core Features
- ✅ **Create Files and Folders** - Including nested directory structures
- ✅ **Delete Items** - Individual files/folders or bulk deletion
- ✅ **Upload Files** - Support for 50+ file types
- ✅ **List Contents** - Browse file/folder hierarchy with metadata
- ✅ **Rename Items** - Rename files and folders
- ✅ **Security** - Path traversal prevention, input validation
- ✅ **Logging** - Comprehensive logging with rotation
- ✅ **File Metadata** - Size, creation time, modification time
- ✅ **Multi-User** - Support for multiple users via user IDs

### Storage
- Local filesystem storage in `data/{user_id}/` structure
- Automatic marker files (`.gitkeep`) for HF integration compatibility
- Prevents duplicate filenames with auto-numbering
- Maintains clean directory structure

## 📁 Project Structure

```
.
├── server/
│   ├── app.py              # Flask application
│   ├── config.py           # Configuration settings
│   ├── requirements.txt    # Python dependencies
│   ├── routes/
│   │   └── api.py          # API endpoints
│   ├── storage/
│   │   └── manager.py      # Storage operations
│   └── utils/
│       ├── logger.py       # Logging setup
│       └── validators.py   # Path validation & security
├── data/                   # Storage directory (auto-created)
├── logs/                   # Log files (auto-created)
├── tests/
│   ├── test_docvault.py   # Unit tests
│   └── test_api.sh        # API test script
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Flask 2.3+
- pip (Python package manager)

### Installation

1. **Clone or download the project**
```bash
cd path/to/DocVault
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r server/requirements.txt
```

### Running the Server

```bash
python server/app.py
```

Server will start at `http://localhost:5000`

View API docs: `http://localhost:5000/docs`

## 📚 API Endpoints

### 1. Health Check
```
GET /api/health
```
Check if server is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "DocVault"
}
```

---

### 2. Create Folder
```
POST /api/create-folder
```
Create a new folder (including nested folders).

**Request:**
```bash
curl -X POST http://localhost:5000/api/create-folder \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "folder_path": "Documents/Projects/MyProject"
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Folder created: Documents/Projects/MyProject",
  "folder": {
    "name": "MyProject",
    "path": "Documents/Projects/MyProject",
    "created_at": "2026-04-09T10:30:00.000000",
    "type": "folder"
  }
}
```

---

### 3. Delete Folder
```
POST /api/delete-folder
```
Delete a folder. Use `force: true` to delete non-empty folders.

**Request:**
```bash
curl -X POST http://localhost:5000/api/delete-folder \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "folder_path": "Documents/Projects/MyProject",
    "force": true
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Folder deleted: Documents/Projects/MyProject"
}
```

---

### 4. Upload File
```
POST /api/upload-file
```
Upload a file to a specific folder.

**Request:**
```bash
curl -X POST http://localhost:5000/api/upload-file \
  -H "X-User-ID: user123" \
  -F "folder_path=Documents" \
  -F "file=@/path/to/file.pdf"
```

**Response:**
```json
{
  "success": true,
  "message": "File uploaded: report.pdf",
  "file": {
    "name": "report.pdf",
    "path": "Documents/report.pdf",
    "size": 102400,
    "size_formatted": "100.00 KB",
    "uploaded_at": "2026-04-09T10:35:00.000000",
    "type": "file"
  }
}
```

---

### 5. List Contents
```
GET /api/list
```
List all files and folders in a directory.

**Request:**
```bash
# List root
curl -X GET "http://localhost:5000/api/list" \
  -H "X-User-ID: user123"

# List specific folder
curl -X GET "http://localhost:5000/api/list?folder_path=Documents" \
  -H "X-User-ID: user123"
```

**Response:**
```json
{
  "success": true,
  "path": "Documents",
  "folders": [
    {
      "name": "Projects",
      "type": "folder",
      "path": "Documents/Projects",
      "created_at": "2026-04-09T10:30:00.000000",
      "modified_at": "2026-04-09T10:30:00.000000"
    }
  ],
  "files": [
    {
      "name": "notes.txt",
      "type": "file",
      "path": "Documents/notes.txt",
      "size": 1024,
      "size_formatted": "1.00 KB",
      "created_at": "2026-04-09T10:35:00.000000",
      "modified_at": "2026-04-09T10:35:00.000000"
    }
  ],
  "summary": {
    "total_folders": 1,
    "total_files": 1
  }
}
```

---

### 6. Rename File/Folder
```
POST /api/rename
```
Rename a file or folder.

**Request:**
```bash
curl -X POST http://localhost:5000/api/rename \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "item_path": "Documents/OldName",
    "new_name": "NewName"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Folder renamed to: NewName",
  "item": {
    "name": "NewName",
    "type": "folder",
    "path": "Documents/NewName"
  }
}
```

---

### 7. Storage Statistics
```
GET /api/storage-stats
```
Get storage usage statistics.

**Request:**
```bash
curl -X GET "http://localhost:5000/api/storage-stats" \
  -H "X-User-ID: user123"
```

**Response:**
```json
{
  "success": true,
  "total_size": 5242880,
  "total_size_formatted": "5.00 MB",
  "total_files": 42,
  "total_folders": 8
}
```

---

### 8. Download File
```
GET /api/download/<file_path>
```
Download a file.

**Request:**
```bash
curl -X GET "http://localhost:5000/api/download/Documents/report.pdf" \
  -H "X-User-ID: user123" \
  -o report.pdf
```

---

## 🔐 Security Features

### Path Traversal Prevention
- Validates all paths are within user's directory
- Prevents `../` and similar attacks
- Normalizes paths before operations

### Input Validation
- Filename restrictions: alphanumeric, hyphens, underscores, dots
- Maximum filename length: 255 characters
- Blocks Windows reserved names (CON, PRN, AUX, etc.)

### File Type Restrictions
Allowed extensions: `txt`, `pdf`, `png`, `jpg`, `jpeg`, `gif`, `doc`, `docx`, `xls`, `xlsx`, `ppt`, `pptx`, `zip`, `rar`, `json`, `xml`, `csv`, `md`, `py`, `js`, `html`, `css`, `yml`, `yaml`

Maximum file size: 50 MB (configurable)

---

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/test_docvault.py -v
```

Or using unittest:
```bash
python -m unittest tests.test_docvault -v
```

### Manual API Testing

#### Using curl (Linux/Mac/WSL)
```bash
bash tests/test_api.sh
```

#### Using Postman
1. Import the endpoints from the documentation above
2. Set header: `X-User-ID: test_user`
3. Test each endpoint

#### Using PowerShell (Windows)
```powershell
# Create folder
$headers = @{"X-User-ID" = "test_user"; "Content-Type" = "application/json"}
$body = '{"folder_path": "Documents"}'
Invoke-RestMethod -Uri "http://localhost:5000/api/create-folder" `
  -Method POST -Headers $headers -Body $body

# Upload file
$headers = @{"X-User-ID" = "test_user"}
$form = @{"folder_path" = "Documents"; "file" = Get-Item "path/to/file.txt"}
Invoke-RestMethod -Uri "http://localhost:5000/api/upload-file" `
  -Method POST -Headers $headers -Form $form

# List contents
$headers = @{"X-User-ID" = "test_user"}
Invoke-RestMethod -Uri "http://localhost:5000/api/list" `
  -Method GET -Headers $headers
```

---

## 📝 Configuration

Edit `server/config.py` to customize:

```python
# Storage location
DATA_DIR = "data"

# Maximum file size (bytes)
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', ...}

# Debug mode
DEBUG = True

# Logging level
LOG_LEVEL = "INFO"
```

---

## 🗂️ Storage Structure

Files are organized by user ID:

```
data/
├── default_user/
│   ├── Documents/
│   │   ├── report.pdf
│   │   ├── notes.txt
│   │   ├── Projects/
│   │   │   ├── ProjectA/
│   │   │   │   ├── .gitkeep
│   │   │   │   └── code.py
│   │   │   └── .gitkeep
│   │   └── .gitkeep
│   ├── Images/
│   └── .gitkeep
├── user123/
└── user456/
```

The `.gitkeep` marker file:
- Identifies folders in HF integration
- Allows tracking empty directories in git
- Automatically created with new folders

---

## 🔌 API Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response
```json
{
  "success": false,
  "error": "Description of error",
  "code": "ERROR_CODE"
}
```

### Common Status Codes
- `200`: OK
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `413`: Payload Too Large
- `500`: Internal Server Error

---

## 🔄 Future Integration: Hugging Face

The system is designed for easy HF integration:

### Mapping to HF Structure
```
Local: data/user/folder/file.txt
  ↓
HF Git: repo/user/folder/file.txt
```

### When integrating with HF:
1. Replace `StorageManager` with `HFStorageManager`
2. Use git operations instead of filesystem
3. Maintain same API interface
4. Folder marker files (`.gitkeep`) enable empty folder tracking

### Integration Points
- Folder creation → git mkdir + .gitkeep commit
- File upload → git commit with file
- Deletion → git remove file/folder
- Listing → git tree navigation
- Renaming → git move + commit

---

## 📊 Logging

Logs are automatically saved and rotated:

```
logs/
├── __main__.log
├── routes.api.log
├── storage.manager.log
└── utils.logger.log
```

- Max log file size: 10 MB
- Backup count: 5 files
- Format: `timestamp - logger - level - message`

---

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Change port in app.py or set environment variable
export FLASK_PORT=5001
python server/app.py
```

### Permission Denied Creating Files
- Ensure write permission to `data/` directory
- On Linux/Mac: `chmod 755 data/`

### CORS Issues
- CORS is enabled by default for local development
- Modify `server/app.py` for production settings

### 404 on API Endpoints
- Check your base URL is `http://localhost:5000/api`
- Verify endpoint path matches exactly

### Duplicate Files
- Files are automatically renamed with `_1`, `_2`, etc.
- Check `/api/list` to see actual filenames

---

## 📈 Performance

- Average folder creation: < 10ms
- File upload: Limited by disk I/O
- Large file handling: Optimized with streaming
- Concurrent requests: Thread-safe with Flask

For high-volume operations, consider:
- Database indexing (future upgrade)
- Caching layer (Redis)
- Background tasks (Celery)

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Database backend integration
- Advanced search functionality
- File versioning
- Collaborative features
- Mobile app support

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files in `logs/`
3. Test with sample curl commands
4. Check configuration in `config.py`

---

## 🎓 Example Workflow

```bash
# 1. Start server
python server/app.py

# 2. Create workspace
curl -X POST http://localhost:5000/api/create-folder \
  -H "X-User-ID: user1" \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "MyProject"}'

# 3. Upload files
curl -X POST http://localhost:5000/api/upload-file \
  -H "X-User-ID: user1" \
  -F "folder_path=MyProject" \
  -F "file=@document.pdf"

# 4. List contents
curl -X GET "http://localhost:5000/api/list?folder_path=MyProject" \
  -H "X-User-ID: user1"

# 5. Check storage
curl -X GET http://localhost:5000/api/storage-stats \
  -H "X-User-ID: user1"
```

---

**DocVault v1.0** - Your offline-first document storage solution ✨
