#!/usr/bin/env python3
"""
Complete system validation script for YouTube Analyzer
"""
import subprocess
import requests
import time
import json
import sys

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_container_status():
    """Check if container is running with correct port mapping"""
    print("🔍 Checking container status...")
    try:
        result = subprocess.run(
            'docker ps --format "{{.Names}}\t{{.Status}}\t{{.Ports}}" | grep youtube-summarizer',
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "8000->8000" in output:
                print("✅ Container running with correct port mapping")
                return True
            else:
                print("❌ Container running but missing port mapping")
                return False
        else:
            print("❌ Container not running")
            return False
    except Exception as e:
        print(f"❌ Error checking container: {e}")
        return False

def check_web_interface():
    """Check if web interface is accessible"""
    print("🔍 Checking web interface...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Web interface accessible")
            return True
        else:
            print(f"❌ Web interface returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web interface not accessible: {e}")
        return False

def check_gpu_detection():
    """Check GPU detection in container"""
    print("🔍 Checking GPU detection...")
    try:
        result = subprocess.run(
            'docker logs youtube-summarizer | grep -E "(GPU|CUDA)" | tail -5',
            shell=True, capture_output=True, text=True
        )
        
        if "GPU acceleration available" in result.stdout:
            print("✅ GPU detection working")
            return True
        else:
            print("⚠️  GPU not detected, using CPU")
            return True  # Not a failure, just informational
    except Exception as e:
        print(f"❌ Error checking GPU: {e}")
        return False

def check_models_loaded():
    """Check if models are loaded successfully"""
    print("🔍 Checking model loading...")
    try:
        response = requests.get("http://localhost:8000/api/models", timeout=30)
        if response.status_code == 200:
            models_data = response.json()
            if models_data.get("models") and len(models_data["models"]) > 0:
                print(f"✅ Models loaded successfully ({len(models_data['models'])} models)")
                return True
            else:
                print("❌ No models loaded")
                return False
        else:
            print(f"❌ Models API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def check_ollama_connection():
    """Check Ollama connection"""
    print("🔍 Checking Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama service accessible")
            return True
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama not accessible: {e}")
        return False

def check_static_files():
    """Check if static files are being served"""
    print("🔍 Checking static files...")
    try:
        # Check CSS file
        css_response = requests.get("http://localhost:8000/static/css/style.css", timeout=10)
        # Check JS file
        js_response = requests.get("http://localhost:8000/static/js/app.js", timeout=10)
        
        if css_response.status_code == 200 and js_response.status_code == 200:
            print("✅ Static files accessible")
            return True
        else:
            print(f"❌ Static files not accessible (CSS: {css_response.status_code}, JS: {js_response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Error checking static files: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Starting YouTube Analyzer System Validation")
    print("=" * 50)
    
    checks = [
        (check_container_status, "Container Status"),
        (check_ollama_connection, "Ollama Connection"),
        (check_web_interface, "Web Interface"),
        (check_static_files, "Static Files"),
        (check_models_loaded, "Model Loading"),
        (check_gpu_detection, "GPU Detection")
    ]
    
    passed = 0
    total = len(checks)
    
    for check_func, check_name in checks:
        if check_func():
            passed += 1
        print()
        time.sleep(1)  # Small delay between checks
    
    print("=" * 50)
    print(f"📊 Validation Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems operational!")
        print("\n💡 System Information:")
        try:
            # Get container info
            container_result = subprocess.run(
                'docker ps --format "{{.Status}}" | grep youtube-summarizer',
                shell=True, capture_output=True, text=True
            )
            if container_result.returncode == 0:
                print(f"   Container Status: {container_result.stdout.strip()}")
            
            # Get GPU info if available
            gpu_result = subprocess.run(
                'docker logs youtube-summarizer | grep "GPU acceleration available" | tail -1',
                shell=True, capture_output=True, text=True
            )
            if gpu_result.returncode == 0 and gpu_result.stdout.strip():
                print(f"   GPU: {gpu_result.stdout.strip()}")
            
            # Get model count
            response = requests.get("http://localhost:8000/api/models", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                print(f"   Available Models: {len(models_data.get('models', []))}")
        except:
            pass
        
        return 0
    else:
        print("⚠️  Some checks failed. Please review the output above.")
        print("\n🔧 Troubleshooting suggestions:")
        print("   1. Check the Docker troubleshooting guide: docs/DOCKER_TROUBLESHOOTING.md")
        print("   2. Restart the container: cd docker && docker-compose down && docker-compose up -d")
        print("   3. Check container logs: docker logs youtube-summarizer")
        print("   4. Verify Ollama is running: curl http://localhost:11434/api/tags")
        return 1

if __name__ == "__main__":
    sys.exit(main())
