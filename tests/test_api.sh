#!/bin/bash

# DocVault API Test Script
# Uses curl to test all API endpoints

BASE_URL="http://localhost:5000/api"
USER_ID="test_user_$(date +%s)"

echo "========================================="
echo "DocVault API Test Script"
echo "========================================="
echo "Base URL: $BASE_URL"
echo "User ID: $USER_ID"
echo ""

# Health Check
echo "1. Testing Health Check..."
curl -X GET "$BASE_URL/health" \
  -H "Content-Type: application/json"
echo ""
echo ""

# Create Folders
echo "2. Creating Folders..."
curl -X POST "$BASE_URL/create-folder" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d '{"folder_path": "Documents"}'
echo ""

echo "3. Creating Nested Folders..."
curl -X POST "$BASE_URL/create-folder" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d '{"folder_path": "Documents/Projects/MyProject"}'
echo ""

echo "4. Creating More Folders..."
curl -X POST "$BASE_URL/create-folder" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d '{"folder_path": "Images"}'
echo ""
echo ""

# List Contents
echo "5. Listing Root Contents..."
curl -X GET "$BASE_URL/list" \
  -H "X-User-ID: $USER_ID"
echo ""
echo ""

# Upload Files
echo "6. Uploading Test File to Documents..."
curl -X POST "$BASE_URL/upload-file" \
  -H "X-User-ID: $USER_ID" \
  -F "folder_path=Documents" \
  -F "file=@test_file.txt"
echo ""

echo "7. Uploading Another File to Documents/Projects..."
curl -X POST "$BASE_URL/upload-file" \
  -H "X-User-ID: $USER_ID" \
  -F "folder_path=Documents/Projects" \
  -F "file=@test_document.md"
echo ""
echo ""

# List Folder Contents
echo "8. Listing Documents Folder..."
curl -X GET "$BASE_URL/list?folder_path=Documents" \
  -H "X-User-ID: $USER_ID"
echo ""
echo ""

echo "9. Listing Documents/Projects Folder..."
curl -X GET "$BASE_URL/list?folder_path=Documents/Projects" \
  -H "X-User-ID: $USER_ID"
echo ""
echo ""

# Rename
echo "10. Renaming Folder..."
curl -X POST "$BASE_URL/rename" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d '{"item_path": "Images", "new_name": "Pictures"}'
echo ""
echo ""

# Storage Stats
echo "11. Getting Storage Statistics..."
curl -X GET "$BASE_URL/storage-stats" \
  -H "X-User-ID: $USER_ID"
echo ""
echo ""

# Delete File (by renaming and deleting the test)
echo "12. Listing all contents before deletion..."
curl -X GET "$BASE_URL/list?folder_path=Documents/Projects/MyProject" \
  -H "X-User-ID: $USER_ID"
echo ""
echo ""

# Delete Folder (empty)
echo "13. Deleting Empty Folder..."
curl -X POST "$BASE_URL/delete-folder" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d '{"folder_path": "Documents/Projects/MyProject"}'
echo ""
echo ""

# Delete Folder (non-empty, with force)
echo "14. Deleting Non-Empty Folder with Force..."
curl -X POST "$BASE_URL/delete-folder" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d '{"folder_path": "Documents/Projects", "force": true}'
echo ""
echo ""

# Final List
echo "15. Final Directory Listing..."
curl -X GET "$BASE_URL/list" \
  -H "X-User-ID: $USER_ID"
echo ""
echo ""

echo "========================================="
echo "Test Complete!"
echo "========================================="
