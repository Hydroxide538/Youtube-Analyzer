# Docker Troubleshooting Guide

## Quick Resolution Summary

### ✅ Web Interface Issue - RESOLVED
- **Problem**: Container running but web interface not accessible
- **Root Cause**: Container started without proper port mapping
- **Solution**: Use `docker-compose up -d` from the `docker/` directory

### ✅ GPU Detection Issue - RESOLVED  
- **Problem**: CUDA not detected after code changes
- **Root Cause**: Container needs to be restarted with proper nvidia runtime
- **Solution**: Restart container using correct docker-compose configuration

---

## 1. Web Interface Not Displaying

### Symptoms
- Docker container is running and healthy
- Health endpoint returns 200 OK
- But main web interface at `http://localhost:8000` is not accessible
- `curl` commands fail with "Unable to connect"

### Diagnosis Steps

1. **Check Container Status**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```
   
   **Expected Output:**
   ```
   NAMES                STATUS                   PORTS
   youtube-summarizer   Up X minutes (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
   ```

2. **If Port Mapping is Missing**
   The container is running but without port mapping (no ports shown in output above).

### Resolution

1. **Stop the incorrectly started container:**
   ```bash
   docker stop youtube-summarizer
   ```

2. **Start with correct Docker Compose configuration:**
   ```bash
   cd docker
   docker-compose up -d
   ```

3. **Verify port mapping:**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```

4. **Wait for services to fully initialize:**
   ```bash
   docker logs youtube-summarizer --follow
   ```
   
   **Look for:**
   - "Uvicorn running on http://0.0.0.0:8000"
   - "Application startup complete"

5. **Test the interface:**
   ```bash
   curl http://localhost:8000/health
   ```

### Prevention
- Always use `docker-compose up -d` from the `docker/` directory (works with external Ollama)
- Never start containers manually with `docker run`
- The main docker-compose.yml handles both GPU support and external Ollama automatically

---

## 2. CUDA/GPU Detection Issues

### Symptoms
- Container shows "No GPU acceleration available, using CPU"
- Previous runs detected GPU correctly
- Performance is slower than expected

### Diagnosis Steps

1. **Check GPU Detection in Container:**
   ```bash
   docker exec -it youtube-summarizer python /app/gpu_detect.py
   ```

2. **Check Container Logs:**
   ```bash
   docker logs youtube-summarizer | grep -i "gpu\|cuda"
   ```

3. **Verify nvidia-docker Runtime:**
   ```bash
   docker info | grep -i nvidia
   ```

### Resolution

1. **Restart Container with Proper Configuration:**
   ```bash
   cd docker
   docker-compose down
   docker-compose up -d
   ```

2. **Verify GPU Detection:**
   ```bash
   docker logs youtube-summarizer | grep -E "(GPU|CUDA)"
   ```

   **Expected Output:**
   ```
   GPU acceleration available: NVIDIA GeForce RTX 3050 Ti Laptop GPU (1 device(s))
   GPU_AVAILABLE=True
   CUDA GPU available: NVIDIA GeForce RTX 3050 Ti Laptop GPU (Total devices: 1, Memory: 4.0GB)
   ✅ GPU test successful - CUDA is working properly
   Using device: cuda
   Model loaded on device: cuda:0
   ```

3. **Test GPU Functionality:**
   ```bash
   docker exec -it youtube-summarizer python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"
   ```

### Prevention
- Always restart containers after major code changes
- Use the nvidia runtime configuration in docker-compose.yml
- Monitor startup logs for GPU detection messages

---

## 3. Common Startup Issues

### Issue: Container Takes Long Time to Start

**Symptoms:**
- Container status shows "health: starting" for extended period
- Application seems to hang during startup

**Cause:**
- Whisper model loading on GPU takes significant time (5-10 minutes)
- NLTK data downloading

**Resolution:**
- Wait for model loading to complete
- Monitor progress: `docker logs youtube-summarizer --follow`
- Look for "Application startup complete" message

### Issue: Model Loading Failures

**Symptoms:**
- Startup fails with model loading errors
- Out of memory errors

**Resolution:**
1. **Check available GPU memory:**
   ```bash
   nvidia-smi
   ```

2. **Reduce model size in configuration if needed**
3. **Restart with more memory allocation:**
   ```bash
   cd docker
   docker-compose down
   docker-compose up -d
   ```

---

## 4. Automated Validation Scripts

### Complete System Validation

Create this script as `scripts/validate_system.py`:

```python
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

def main():
    """Main validation function"""
    print("🚀 Starting YouTube Analyzer System Validation")
    print("=" * 50)
    
    checks = [
        (check_container_status, "Container Status"),
        (check_web_interface, "Web Interface"),
        (check_gpu_detection, "GPU Detection")
    ]
    
    passed = 0
    total = len(checks)
    
    for check_func, check_name in checks:
        if check_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Validation Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️  Some checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Run Validation
```bash
python scripts/validate_system.py
```

---

## 5. Startup Checklist

### Before Starting the Application:

1. **✅ Verify Docker is Running**
   ```bash
   docker --version
   ```

2. **✅ Check Ollama Service**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **✅ Start from Correct Directory**
   ```bash
   cd docker
   docker-compose up -d
   ```

4. **✅ Monitor Startup**
   ```bash
   docker logs youtube-summarizer --follow
   ```

5. **✅ Verify Services**
   ```bash
   python scripts/validate_system.py
   ```

### Expected Startup Sequence:

1. **GPU Detection** (30 seconds)
2. **Model Loading** (5-10 minutes)
3. **Service Initialization** (30 seconds)
4. **Web Interface Ready** (Total: 6-11 minutes)

---

## 6. Emergency Recovery

### If Everything Fails:

1. **Complete Reset:**
   ```bash
   cd docker
   docker-compose down
   docker system prune -f
   docker-compose up --build -d
   ```

2. **Check System Resources:**
   ```bash
   nvidia-smi
   docker system df
   ```

3. **Fallback to CPU Mode:**
   ```bash
   cd docker
   docker-compose -f docker-compose.cpu.yml up -d
   ```

---

## 7. Monitoring and Maintenance

### Regular Health Checks:

1. **Container Health:**
   ```bash
   docker ps
   curl http://localhost:8000/health
   ```

2. **GPU Status:**
   ```bash
   nvidia-smi
   docker exec -it youtube-summarizer python /app/gpu_detect.py
   ```

3. **Log Analysis:**
   ```bash
   docker logs youtube-summarizer --tail 50
   ```

### Performance Monitoring:

1. **GPU Utilization:**
   ```bash
   watch -n 1 nvidia-smi
   ```

2. **Container Resources:**
   ```bash
   docker stats youtube-summarizer
   ```

---

## 8. Prevention Best Practices

### Development Workflow:

1. **Always use Docker Compose** from the `docker/` directory
2. **Wait for complete startup** before testing
3. **Monitor logs** during development
4. **Run validation** after major changes
5. **Document** any new issues and solutions

### Code Changes:

1. **Test GPU detection** after model service changes
2. **Verify port mapping** after Docker configuration changes
3. **Check static files** after frontend changes
4. **Validate health endpoints** after API changes

### Deployment:

1. **Use provided scripts** in `scripts/` directory
2. **Follow startup checklist** systematically
3. **Monitor logs** for the first few minutes
4. **Run validation** to confirm everything works

---

## Contact and Support

For persistent issues:
1. Check the logs: `docker logs youtube-summarizer`
2. Run validation: `python scripts/validate_system.py`
3. Review this troubleshooting guide
4. Check GPU drivers and Docker nvidia runtime
5. Consider system resources and memory availability

**Last Updated:** July 16, 2025
**System Tested:** Windows 11 + Docker Desktop + WSL2 + NVIDIA RTX 3050 Ti
