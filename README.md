---
title: DocVault App
emoji: 📁
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
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
├── index.html              # Frontend UI
├── app.js                  # Frontend app logic
├── styles.css              # Frontend styles
└── README.md               # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip or conda

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd DocVault
   ```

2. **Install dependencies**
   ```bash
   pip install -r server/requirements.txt
   ```

3. **Run the application**
   ```bash
   python server/app.py
   ```

4. **Access the app**
   - Open browser to `http://localhost:5000`

## 📝 API Endpoints

### File Operations
- `POST /api/create` - Create file or folder
- `DELETE /api/delete` - Delete file or folder
- `PUT /api/rename` - Rename item
- `POST /api/upload` - Upload file
- `GET /api/list/<path>` - List directory contents

### Request Examples

**Create File:**
```bash
curl -X POST http://localhost:5000/api/create \
  -H "Content-Type: application/json" \
  -d '{"user_id":"default_user","item_type":"file","name":"test.txt","path":"/"}'
```

**Upload File:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "user_id=default_user" \
  -F "file=@localfile.txt" \
  -F "path=/"
```

**List Contents:**
```bash
curl http://localhost:5000/api/list/default_user/
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/test_docvault.py -v
```

Or use the included API test script:
```bash
bash tests/test_api.sh
```

## 🔒 Security Features

- **Path Traversal Prevention** - Validates all paths to prevent directory escape attacks
- **Input Validation** - Sanitizes filenames and paths
- **User Isolation** - Each user has their own data directory
- **Error Handling** - Comprehensive error messages without exposing system details

## 📊 Logging

- Logs stored in `logs/` directory
- Automatic log rotation (10 MB per file, 10 files kept)
- Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🚢 Deployment

### Docker
```bash
docker build -t docvault .
docker run -p 5000:5000 docvault
```

### Hugging Face Spaces
This app is ready for deployment on Hugging Face Spaces as a static frontend application.

## 📦 Dependencies

- Flask 2.3.2
- Werkzeug 2.3.6
- Python 3.8+

See `server/requirements.txt` for full list.

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues or questions, please open an Issue on GitHub.