# Sample Markdown Document

This is a sample markdown document for testing DocVault file upload functionality.

## Features
- File upload
- Folder creation
- File management
- Storage tracking

## Code Example

```python
# DocVault API Usage
import requests

response = requests.post(
    'http://localhost:5000/api/create-folder',
    json={'folder_path': 'Documents/Projects'},
    headers={'X-User-ID': 'user123'}
)

print(response.json())
```

---

**Created for DocVault Testing**
