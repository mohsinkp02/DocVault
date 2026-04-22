#!/usr/bin/env python3
"""
DocVault Stress Test Suite
Automated testing for production readiness
Run: python stress_test.py http://localhost:5000
"""

import requests
import time
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ──────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
USER_ID = "stress_test_user"
NUM_FILES_BULK = 50
NUM_FILES_FOLDER = 30
RAPID_OPS_COUNT = 20
TIMEOUT = 30

HEADERS = {
    "X-User-ID": USER_ID,
    "Content-Type": "application/json"
}

# ──────────────────────────────────────────────────────
# RESULTS TRACKING
# ──────────────────────────────────────────────────────

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.timings = {}
        self.race_conditions = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"  ✓ {test_name}")
    
    def add_fail(self, test_name, reason):
        self.failed += 1
        self.errors.append(f"{test_name}: {reason}")
        print(f"  ✗ {test_name} - {reason}")
    
    def add_timing(self, operation, duration):
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(duration)
    
    def report(self):
        print("\n" + "="*60)
        print("STRESS TEST RESULTS")
        print("="*60)
        print(f"✓ Passed: {self.passed}")
        print(f"✗ Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}\n")
        
        if self.timings:
            print("PERFORMANCE METRICS:")
            for op, times in self.timings.items():
                avg = sum(times) / len(times)
                max_t = max(times)
                print(f"  {op}: avg={avg:.2f}s, max={max_t:.2f}s, count={len(times)}")
        
        if self.errors:
            print("\nERRORS:")
            for error in self.errors[:10]:  # Show first 10
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
        
        if self.race_conditions:
            print("\nPOTENTIAL RACE CONDITIONS:")
            for rc in self.race_conditions:
                print(f"  ⚠️  {rc}")
        
        print("\n" + "="*60)
        return self.passed, self.failed

results = TestResults()

# ──────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────

def health_check():
    """Verify server is running"""
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
        return resp.status_code == 200
    except:
        return False

def upload_file(filename, folder="", size_kb=10):
    """Upload a test file"""
    url = f"{BASE_URL}/api/upload-file"
    
    # Create test file content
    content = b"x" * (size_kb * 1024)
    
    files = {"file": (filename, content)}
    data = {"folder_path": folder}
    
    try:
        resp = requests.post(url, headers=HEADERS, files=files, data=data, timeout=TIMEOUT)
        return resp.status_code == 201 and resp.json().get("success")
    except Exception as e:
        results.add_fail(f"upload({filename})", str(e))
        return False

def delete_file(path):
    """Delete a file"""
    url = f"{BASE_URL}/api/delete-file"
    try:
        resp = requests.post(url, headers=HEADERS, json={"file_path": path}, timeout=TIMEOUT)
        return resp.status_code == 200 and resp.json().get("success")
    except Exception as e:
        results.add_fail(f"delete({path})", str(e))
        return False

def delete_folder(path):
    """Delete a folder"""
    url = f"{BASE_URL}/api/delete-folder"
    try:
        resp = requests.post(url, headers=HEADERS, json={"folder_path": path}, timeout=TIMEOUT)
        return resp.status_code == 200 and resp.json().get("success")
    except Exception as e:
        results.add_fail(f"delete_folder({path})", str(e))
        return False

def list_files(path=""):
    """List files in path"""
    url = f"{BASE_URL}/api/list"
    try:
        resp = requests.get(url, headers=HEADERS, params={"folder_path": path}, timeout=TIMEOUT)
        return resp.status_code == 200 and resp.json().get("success")
    except Exception as e:
        results.add_fail(f"list({path})", str(e))
        return False

def rename_item(old_path, new_name):
    """Rename a file or folder"""
    url = f"{BASE_URL}/api/rename"
    try:
        resp = requests.post(
            url, 
            headers=HEADERS, 
            json={"item_path": old_path, "new_name": new_name},
            timeout=TIMEOUT
        )
        return resp.status_code == 200 and resp.json().get("success")
    except Exception as e:
        results.add_fail(f"rename({old_path})", str(e))
        return False

def create_folder(path):
    """Create a folder"""
    url = f"{BASE_URL}/api/create-folder"
    try:
        resp = requests.post(url, headers=HEADERS, json={"folder_path": path}, timeout=TIMEOUT)
        return resp.status_code == 201 and resp.json().get("success")
    except Exception as e:
        results.add_fail(f"create_folder({path})", str(e))
        return False

# ──────────────────────────────────────────────────────
# TEST 1: BULK UPLOAD
# ──────────────────────────────────────────────────────

def test_bulk_upload():
    """Upload 50+ files and check for speed/failures"""
    print("\n🔥 TEST 1: BULK UPLOAD (50 files)")
    print("-" * 40)
    
    start_time = time.time()
    success_count = 0
    failed_uploads = []
    
    for i in range(NUM_FILES_BULK):
        filename = f"bulk_test_{i:03d}.txt"
        op_start = time.time()
        
        if upload_file(filename, size_kb=5):
            success_count += 1
        else:
            failed_uploads.append(filename)
        
        op_duration = time.time() - op_start
        results.add_timing("bulk_upload", op_duration)
    
    total_duration = time.time() - start_time
    
    print(f"  Uploaded: {success_count}/{NUM_FILES_BULK}")
    print(f"  Total time: {total_duration:.2f}s")
    print(f"  Avg per file: {total_duration/NUM_FILES_BULK:.2f}s")
    
    if success_count == NUM_FILES_BULK:
        results.add_pass("bulk_upload_all_succeed")
    else:
        results.add_fail("bulk_upload", f"Only {success_count}/{NUM_FILES_BULK} succeeded")
    
    if total_duration > NUM_FILES_BULK * 5:  # Should be faster than 5s per file
        results.add_fail("bulk_upload_speed", f"Too slow: {total_duration:.2f}s total")
    else:
        results.add_pass("bulk_upload_speed")
    
    # Cleanup
    for i in range(success_count):
        delete_file(f"bulk_test_{i:03d}.txt")

# ──────────────────────────────────────────────────────
# TEST 2: FOLDER RENAME STRESS
# ──────────────────────────────────────────────────────

def test_folder_rename_stress():
    """Create folder with many files, then rename it"""
    print("\n🔥 TEST 2: FOLDER RENAME STRESS (30 files in folder)")
    print("-" * 40)
    
    folder_name = "stress_folder_rename"
    
    # Create folder
    if not create_folder(folder_name):
        results.add_fail("create_test_folder", "Failed to create folder")
        return
    
    # Upload 30 files into it
    print("  Uploading 30 files into folder...")
    for i in range(NUM_FILES_FOLDER):
        filepath = f"{folder_name}/file_{i:02d}.txt"
        if not upload_file(f"file_{i:02d}.txt", folder=folder_name):
            results.add_fail(f"upload_to_folder", f"File {i} failed")
            break
    
    # List before rename
    list_before = list_files(folder_name)
    if not list_before:
        results.add_fail("list_before_rename", "List failed")
    
    # Rename folder
    print("  Renaming folder...")
    op_start = time.time()
    rename_success = rename_item(folder_name, "stress_folder_renamed")
    rename_duration = time.time() - op_start
    results.add_timing("folder_rename", rename_duration)
    
    if rename_success:
        results.add_pass("folder_rename")
    else:
        results.add_fail("folder_rename", "Rename failed")
    
    if rename_duration > 10:
        results.add_fail("folder_rename_speed", f"Too slow: {rename_duration:.2f}s")
    else:
        results.add_pass("folder_rename_speed")
    
    # List after rename
    list_after = list_files("stress_folder_renamed")
    if not list_after:
        results.add_fail("list_after_rename", "List failed after rename - data may be lost!")
    else:
        results.add_pass("folder_rename_data_preserved")
    
    # Cleanup
    delete_folder("stress_folder_renamed")

# ──────────────────────────────────────────────────────
# TEST 3: RAPID OPERATIONS (Race Conditions)
# ──────────────────────────────────────────────────────

def test_rapid_operations():
    """Upload → Delete → Rename rapidly"""
    print("\n🔥 TEST 3: RAPID OPERATIONS (Race Conditions)")
    print("-" * 40)
    
    start_time = time.time()
    failed_ops = []
    
    # Scenario 1: Upload then immediately delete
    for i in range(RAPID_OPS_COUNT):
        filename = f"rapid_test_{i}.txt"
        
        # Upload
        if not upload_file(filename):
            failed_ops.append(f"upload({filename})")
            continue
        
        # Delete immediately
        if not delete_file(filename):
            failed_ops.append(f"delete({filename})")
            # Could indicate race condition
            results.race_conditions.append(
                f"Delete failed right after upload for {filename}"
            )
    
    duration = time.time() - start_time
    
    if not failed_ops:
        results.add_pass(f"rapid_ops_{RAPID_OPS_COUNT}_cycles")
    else:
        results.add_fail(f"rapid_ops", f"{len(failed_ops)} operations failed")
    
    print(f"  {RAPID_OPS_COUNT} cycles in {duration:.2f}s")
    
    # Scenario 2: Sequential upload → rename → delete
    for i in range(10):
        filename = f"rapid_seq_{i}.txt"
        if upload_file(filename):
            if rename_item(filename, f"rapid_seq_{i}_renamed.txt"):
                delete_file(f"rapid_seq_{i}_renamed.txt")
    
    results.add_pass("rapid_seq_operations")

# ──────────────────────────────────────────────────────
# TEST 4: CACHE VALIDATION
# ──────────────────────────────────────────────────────

def test_cache_behavior():
    """Verify cache is updated correctly"""
    print("\n🧪 TEST 4: CACHE VALIDATION (60s TTL)")
    print("-" * 40)
    
    # Upload file
    if not upload_file("cache_test.txt"):
        results.add_fail("cache_upload", "Failed to upload")
        return
    
    # List immediately (should be fresh)
    op_start = time.time()
    if list_files():
        duration1 = time.time() - op_start
        results.add_timing("list_fresh", duration1)
        results.add_pass("cache_first_list")
    else:
        results.add_fail("cache_first_list", "List failed")
    
    # List again (should use cache, be faster)
    op_start = time.time()
    if list_files():
        duration2 = time.time() - op_start
        results.add_timing("list_cached", duration2)
        results.add_pass("cache_second_list")
    else:
        results.add_fail("cache_second_list", "List failed")
    
    # Cleanup
    delete_file("cache_test.txt")

# ──────────────────────────────────────────────────────
# TEST 5: ERROR HANDLING
# ──────────────────────────────────────────────────────

def test_error_handling():
    """Test error cases and recovery"""
    print("\n🧪 TEST 5: ERROR HANDLING")
    print("-" * 40)
    
    # Try invalid operations
    invalid_tests = [
        ("delete_nonexistent", lambda: delete_file("does_not_exist.txt")),
        ("rename_nonexistent", lambda: rename_item("nonexistent", "newname")),
        ("list_nonexistent", lambda: list_files("nonexistent/path")),
    ]
    
    for test_name, operation in invalid_tests:
        try:
            result = operation()
            if not result:  # Should fail
                results.add_pass(f"error_handling_{test_name}")
            else:
                results.add_fail(f"error_handling_{test_name}", "Should have failed")
        except Exception as e:
            results.add_fail(f"error_handling_{test_name}", str(e))

# ──────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("DOCVAULT STRESS TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"User: {USER_ID}")
    print(f"Timeout: {TIMEOUT}s\n")
    
    # Check server
    print("Checking server connectivity...")
    if not health_check():
        print("❌ Server is not running or not responding!")
        print(f"Make sure your app is running at {BASE_URL}")
        sys.exit(1)
    
    print("✓ Server is healthy\n")
    
    # Run tests
    try:
        test_bulk_upload()
        test_folder_rename_stress()
        test_rapid_operations()
        test_cache_behavior()
        test_error_handling()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Report results
    passed, failed = results.report()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
