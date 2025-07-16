#!/usr/bin/env python3
"""
Test script to validate static file serving in the container
"""

import os
import sys
import requests
import time
from pathlib import Path

def test_static_file_paths():
    """Test that static files exist at expected paths"""
    print("🔍 Testing static file paths...")
    
    # Expected file paths in container
    expected_files = [
        "/app/static/css/style.css",
        "/app/static/js/app.js", 
        "/app/templates/index.html"
    ]
    
    all_exist = True
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_web_server_health():
    """Test that the web server is running"""
    print("\n🌐 Testing web server health...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint accessible")
            return True
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health endpoint not accessible: {e}")
        return False

def test_static_file_serving():
    """Test that static files are served correctly"""
    print("\n📁 Testing static file serving...")
    
    static_urls = [
        "http://localhost:8000/static/css/style.css",
        "http://localhost:8000/static/js/app.js"
    ]
    
    all_served = True
    for url in static_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} served successfully")
            else:
                print(f"❌ {url} returned {response.status_code}")
                all_served = False
        except requests.exceptions.RequestException as e:
            print(f"❌ {url} not accessible: {e}")
            all_served = False
    
    return all_served

def test_main_page():
    """Test that the main page loads"""
    print("\n🏠 Testing main page...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            if "YouTube Video Summarizer" in response.text:
                print("✅ Main page loads with correct title")
                return True
            else:
                print("❌ Main page loads but missing expected content")
                return False
        else:
            print(f"❌ Main page returned {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Main page not accessible: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 YouTube Analyzer Frontend Test Suite")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(5)
    
    # Run tests
    tests = [
        ("File Paths", test_static_file_paths),
        ("Web Server Health", test_web_server_health),
        ("Static File Serving", test_static_file_serving),
        ("Main Page", test_main_page)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Frontend should be working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
