# DocVault HuggingFace Spaces - Deployment & Testing Guide

**Application URL**: https://huggingface.co/spaces/mohsin-devs/DocVault-app  
**Repository**: mohsin-devs/DocVault-Storage (dataset)  
**Status**: Ready for production validation

---

## 🔧 Current Configuration

```
STORAGE_MODE: HF (Hugging Face Mode)
HF_REPO_ID: mohsin-devs/DocVault-Storage
HF_REPO_TYPE: dataset
Cache TTL: 60 seconds
Max File Size: 50MB
USER_ID: default_user
```

---

## ✅ Pre-Deployment Checklist

### Environment Variables (Verify in HF Spaces Settings)
```bash
STORAGE_MODE=HF                          # ✅ Set
HF_TOKEN=hf_MXrmgjFFRaqYUltCaf...      # ✅ Set (current token in codebase)
HF_REPO_ID=mohsin-devs/DocVault-Storage # ✅ Set
HF_REPO_TYPE=dataset                    # ✅ Set
DEBUG=False                              # ⏳ Verify for production
SECRET_KEY=<random-value>               # ✅ Should be changed in production
```

### Backend Requirements
```python
# server/requirements.txt contains:
Flask
flask-cors
huggingface_hub
Werkzeug
```

### Frontend Configuration
```javascript
// js/api/hfService.js
apiBase = '/api'
User ID = 'default_user'
Cache TTL = 60 seconds
Retry Limit = 3
Retry Delay = 1 second (exponential backoff)
```

---

## 🧪 Post-Deployment Testing Procedure

### Step 1: Verify Application is Accessible
```
1. Open: https://huggingface.co/spaces/mohsin-devs/DocVault-app
2. Should see:
   - Logo and "DocVault" title
   - Sidebar with "New" button
   - File browser area (empty or with existing files)
   - Upload progress area
   - Storage stats at bottom
3. Check browser console: No errors
```

### Step 2: Test Basic Upload (5 minutes)
```
1. Click "New" → "Upload File"
2. Select a test file (small .txt file recommended)
3. Wait for upload to complete
4. Verify:
   ✓ File appears in main area
   ✓ File size displays correctly
   ✓ Toast shows "Uploaded <filename>" success
   ✓ Storage stats update
```

### Step 3: Test Download
```
1. Click on uploaded file (or download icon)
2. If preview modal opens:
   - Click download button
   - Or: right-click → Save as
3. Verify: File downloads with original name
4. Verify: Content is correct
```

### Step 4: Test NEW Rename Feature ⭐ (PRIORITY)
```
1. Click file's dropdown menu (three-dot icon)
2. Should see two options:
   - Rename
   - Delete
3. Click "Rename"
4. Modal appears with filename pre-filled and selected
5. Type new name: "test_renamed.txt"
6. Press Enter or click "Rename" button
7. Verify:
   ✓ Modal closes
   ✓ File list updates
   ✓ New name appears
   ✓ Toast shows success
   ✓ In HF repo: file renamed
```

### Step 5: Test Delete
```
1. Upload another test file
2. Click file menu → Delete
3. Delete confirmation modal appears
4. Click "Confirm Delete"
5. Verify:
   ✓ File removed from list
   ✓ Storage stats decrease
   ✓ Toast shows "Deleted successfully"
```

### Step 6: Test Folder Operations (5 minutes)
```
1. Click "New" → "Create Folder"
2. Type: "TestFolder"
3. Click "Create" or press Enter
4. Verify:
   ✓ Folder appears in list
   ✓ Folder icon displays
   ✓ Toast shows "Folder created"

5. Double-click folder to enter
6. Verify:
   ✓ Path updates in breadcrumbs
   ✓ Says "Nothing here yet"
   
7. Upload file into folder
8. Verify: File appears in folder

9. Click three-dot menu on folder
10. Click "Rename" → "Renamed_Folder"
11. Verify: Folder name updated

12. Delete folder
13. Verify: Removed with all contents
```

### Step 7: Test Version History (HF Mode) ⏸️ - Requires Pre-existing Versions
```
IF previous versions of files exist in HF repo:
1. Click file's history icon (clock icon)
2. History modal opens
3. Verify:
   ✓ Multiple versions listed
   ✓ Current version marked
   ✓ Commit messages visible
   ✓ Timestamps correct

4. Test "Restore as Copy":
   - Click on old version
   - Click "Restore as Copy"
   - Modal closes WITHOUT warning
   - New file appears with timestamp suffix

5. Test "Restore (Overwrite)":
   - Click on old version
   - Click "Overwrite"
   - Confirmation dialog appears
   - Click "Confirm"
   - File reverted to old version
```

### Step 8: Test Cache Behavior (10 minutes)
```
1. Upload file1.txt
2. Note the time
3. Reload page within 10 seconds
4. Verify:
   ✓ List loads instantly (uses cache)
   ✓ file1.txt visible

5. Upload file2.txt
6. List should update immediately
7. Wait 65 seconds
8. Upload file3.txt again
9. Verify: List updates immediately (cache was cleared)

DevTools Network check:
- Upload: Should clear cache (no /api/list call immediately after)
- Delete: Should clear cache
- Rename: Should clear cache
```

### Step 9: Test Error Handling (5 minutes)
```
1. Note current network activity
2. Simulate offline: DevTools → Network → Offline
3. Try to upload: Should show "offline" warning
4. Go back online: DevTools → Network → Online
5. Try operation again: Should work

Alternative error tests:
- Try renaming to extremely long name (>255 chars)
- Try special characters: file[2024].txt
- Try path traversal: ../../../admin
- All should be rejected gracefully with error toast
```

### Step 10: View Mode Toggle (2 minutes)
```
1. Files should display in "Grid" view by default
2. Click grid/list toggle buttons (top right)
3. Verify:
   ✓ View changes between grid and list
   ✓ All files still visible
   ✓ File actions still work in both views
   ✓ Preference persists on reload
```

---

## 🔍 Verification Checklist

### Frontend Functionality
- [ ] Upload file works
- [ ] Download file works
- [ ] Delete file shows warning, works correctly
- [ ] **Rename file works (NEW FEATURE)**
- [ ] Create folder works
- [ ] Delete folder works
- [ ] **Rename folder works (NEW FEATURE)**
- [ ] Browse folders with breadcrumbs works
- [ ] Grid/List view toggle works
- [ ] View preference persists (localStorage)

### API Responsiveness
- [ ] All requests complete within 5 seconds
- [ ] Cache works (repeated list calls are instant)
- [ ] Cache invalidation works (changes appear immediately)
- [ ] Error responses show helpful messages

### HF Integration
- [ ] Files appear in https://huggingface.co/datasets/mohsin-devs/DocVault-Storage
- [ ] Deletions remove files from HF repo
- [ ] Renames work correctly in HF repo
- [ ] File structure preserved with user_id prefix

### UX/Polish
- [ ] Toast notifications appear and fade
- [ ] Progress indicator shows during operations
- [ ] Modals open/close smoothly
- [ ] No console errors
- [ ] Mobile responsive (test on small screen)
- [ ] Keyboard shortcuts work (Enter to confirm, Escape to cancel)

---

## 📊 Performance Benchmarks

| Operation | Expected Time | Current | Pass/Fail |
|-----------|---------------|---------|-----------|
| List files (cached) | <100ms | ? | ? |
| List files (fresh) | <2s | ? | ? |
| Upload small file (<5MB) | <5s | ? | ? |
| Upload large file (45MB) | <30s | ? | ? |
| Download file | <5s | ? | ? |
| Delete file | <2s | ? | ? |
| Rename operation | <2s | ? | ? |
| Cache hit rate | >80% | ? | ? |

---

## 🐛 Known Issues & Workarounds

| Issue | Workaround |
|-------|-----------|
| HF file sizes show as 0 | HF API limitation—consider querying file API separately if size needed |
| Search is client-side | Works for <10K files; disable for massive lists or implement backend search |
| Version history not synced | Refresh page/reopen modal to see latest history |
| Large batch operations slow | Reduce batch size or implement progressive loading |

---

## 🚨 Troubleshooting

### Files not appearing after upload
```
1. Check network tab: Upload request should return 201
2. Wait 3 seconds for cache to clear
3. Refresh page manually
4. Check HF repo: Files should be at /default_user/filename
5. If still missing: Check browser console for errors
```

### Rename shows but doesn't work
```
1. Verify backend /api/rename endpoint exists
2. Check response: Should return {"success": true, "message": "..."}
3. Clear browser cache and hard refresh (Ctrl+F5)
4. Check console for JavaScript errors
5. Verify HuggingFace API token is valid
```

### Cache not clearing
```
1. Manual refresh: Ctrl+F5 (hard refresh)
2. Clear browser cache: DevTools → Application → Clear storage
3. Check network: Recent upload should trigger cache clear
4. Verify: TTL is 60 seconds (not 5 minutes)
```

### Slow performance
```
1. Check: File count (if >1000, might need pagination)
2. Check: File sizes (very large files slow down listing)
3. Check: Network speed (throttle in DevTools)
4. Consider: Reducing cache data logged to console
```

---

## 🚀 Production Deployment Readiness

### Deployment Checklist
- [x] Code fixes applied and verified
- [x] Cache TTL aligned (60 seconds)
- [x] Error handling comprehensive
- [x] Security validation in place
- [ ] HF token configured in Space settings
- [ ] DEBUG=False set for production
- [ ] Monitoring/alerting configured
- [ ] Backup strategy documented
- [ ] User documentation ready
- [ ] Team trained on deployment

### Go/No-Go Decision
After completing all test steps above:
- [ ] Go: All tests passed, ready for production
- [ ] No-Go: Issues found, needs fixes before deployment

---

## 📞 Support
For issues or questions:
1. Check this guide
2. Review `/memories/repo/docvault-comprehensive-audit-report.md` for detailed testing
3. Check browser console (F12 → Console tab) for error messages
4. Review HF Space logs for backend errors

---

**Test Date**: ___________  
**Tested By**: ___________  
**Result**: ☐ PASS ☐ FAIL  
**Comments**: ____________________________

**Sign Off**: _________________ Date: _______
