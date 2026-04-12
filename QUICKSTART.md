# DocVault Quick Start Guide

Get up and running with DocVault in 5 minutes!

## Step 1: Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

## Step 2: Start the Server

```bash
python app.py
```

You should see:
```
Starting DocVault on http://localhost:5000 (DEBUG: True)
```

## Step 3: Test the API

Open a new terminal and run these curl commands:

### Create a folder
```bash
curl -X POST http://localhost:5000/api/create-folder \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d '{"folder_path": "MyDocuments"}'
```

### Upload a file
```bash
curl -X POST http://localhost:5000/api/upload-file \
  -H "X-User-ID: test_user" \
  -F "folder_path=MyDocuments" \
  -F "file=@tests/test_file.txt"
```

### List contents
```bash
curl -X GET http://localhost:5000/api/list \
  -H "X-User-ID: test_user"
```

### Check storage stats
```bash
curl -X GET http://localhost:5000/api/storage-stats \
  -H "X-User-ID: test_user"
```

## Step 4: Using Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:5000/api"
HEADERS = {"X-User-ID": "test_user"}

# Create folder
response = requests.post(
    f"{BASE_URL}/create-folder",
    json={"folder_path": "Projects"},
    headers=HEADERS
)
print(response.json())

# Upload file
with open("tests/test_document.md", "rb") as f:
    files = {"file": f}
    data = {"folder_path": "Projects"}
    response = requests.post(
        f"{BASE_URL}/upload-file",
        files=files,
        data=data,
        headers=HEADERS
    )
    print(response.json())

# List contents
response = requests.get(
    f"{BASE_URL}/list?folder_path=Projects",
    headers=HEADERS
)
print(json.dumps(response.json(), indent=2))

# Storage stats
response = requests.get(
    f"{BASE_URL}/storage-stats",
    headers=HEADERS
)
print(response.json())
```

## Step 5: Using Postman

1. Import `tests/DocVault.postman_collection.json` into Postman
2. Set the `X-User-ID` header for each request
3. Test all endpoints

## File Structure

After running some operations, your file structure will look like:

```
data/
└── test_user/
    ├── MyDocuments/
    │   ├── test_file.txt
    │   └── .gitkeep
    ├── Projects/
    │   ├── test_document.md
    │   └── .gitkeep
    └── .gitkeep
```

## Directory Size

Check storage usage:
```bash
# Windows
dir /s /b data\

# Linux/Mac
du -sh data/
```

## Troubleshooting

### Port 5000 Already in Use
```bash
# Find process using port 5000
netstat -ano | findstr :5000  # Windows
lsof -i :5000                  # Mac/Linux

# Kill process
taskkill /PID <PID> /F  # Windows
kill -9 <PID>           # Mac/Linux

# Or use different port (modify app.py)
```

### Module Import Errors
Ensure you're in the correct directory:
```bash
cd /path/to/DocVault
python server/app.py
```

### Permission Denied
Ensure write permissions:
```bash
chmod 755 data logs  # Mac/Linux
# Windows should work automatically
```

## Next Steps

1. **Explore the API** - Try all endpoints with different user IDs
2. **Test with files** - Upload various file types
3. **Integrate** - Embed DocVault into your application
4. **Scale** - Plan for database backend or cloud storage

## API Reference

See [README.md](../README.md) for complete API documentation.

## Support

For issues:
1. Check logs in `logs/` directory
2. Review error messages in response
3. Verify file/folder names are valid
4. Ensure user ID is consistent across requests

---

**Happy documenting with DocVault!** 📂✨
