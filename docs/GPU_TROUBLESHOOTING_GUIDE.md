# GPU Troubleshooting Guide for YouTube Analyzer

## Overview

This guide provides comprehensive troubleshooting steps for GPU-related issues in the YouTube Analyzer application. The most common issue is CUDA detection failures after code changes or container restarts.

## ✅ Current Status: GPU Detection Working

**Last Verified:** July 16, 2025  
**System:** Windows 11 + Docker Desktop + WSL2 + NVIDIA RTX 3050 Ti  
**Status:** ✅ GPU Detection Working Properly

### Current Working Configuration
- **GPU:** NVIDIA GeForce RTX 3050 Ti Laptop GPU (4GB VRAM)
- **CUDA Version:** 11.8 (via PyTorch)
- **Docker Runtime:** nvidia
- **Container Status:** Running with GPU acceleration
- **Model Loading:** Whisper 'small' model on GPU

---

## 1. Quick Diagnosis Commands

### Check GPU Status
```bash
# Check if GPU is detected in container
docker exec -it youtube-summarizer python /app/gpu_detect.py

# Check container logs for GPU messages
docker logs youtube-summarizer | grep -E "(GPU|CUDA)" | tail -10

# Check NVIDIA driver on host
nvidia-smi
```

### Expected Output (Working)
```
GPU acceleration available: NVIDIA GeForce RTX 3050 Ti Laptop GPU (1 device(s))
GPU_AVAILABLE=True
CUDA GPU available: NVIDIA GeForce RTX 3050 Ti Laptop GPU (Total devices: 1, Memory: 4.0GB)
✅ GPU test successful - CUDA is working properly
Using device: cuda
Model loaded on device: cuda:0
```

### Expected Output (Not Working)
```
No GPU acceleration available, using CPU
GPU_AVAILABLE=False
Using device: cpu
Model loaded on device: cpu
```

---

## 2. Common GPU Issues and Solutions

### Issue 1: GPU Not Detected After Code Changes

**Symptoms:**
- Previous run detected GPU correctly
- After code changes, showing "No GPU acceleration available"
- Container logs show "Using device: cpu"

**Root Cause:**
Container needs to be restarted to properly initialize GPU detection

**Solution:**
```bash
cd docker
docker-compose down
docker-compose up -d
```

**Wait for complete startup:**
```bash
docker logs youtube-summarizer --follow
```

### Issue 2: GPU Detection Inconsistent

**Symptoms:**
- Sometimes detects GPU, sometimes doesn't
- Intermittent CUDA failures

**Root Cause:**
- Docker nvidia runtime not properly configured
- Container started without GPU access

**Solution:**
```bash
# Verify nvidia runtime is available
docker info | grep -i nvidia

# Stop and restart with explicit GPU access
docker stop youtube-summarizer
cd docker
docker-compose up -d

# Verify GPU access
docker exec -it youtube-summarizer nvidia-smi
```

### Issue 3: CUDA Out of Memory

**Symptoms:**
- GPU detected but fails during model loading
- "CUDA out of memory" errors

**Root Cause:**
- 4GB VRAM limit on RTX 3050 Ti
- Other applications using GPU memory

**Solution:**
```bash
# Check GPU memory usage
nvidia-smi

# Close other GPU applications
# Restart container to clear GPU memory
cd docker
docker-compose down
docker-compose up -d
```

### Issue 4: Docker GPU Runtime Issues

**Symptoms:**
- "nvidia runtime not found" errors
- GPU not available in container

**Root Cause:**
- Docker Desktop GPU support not enabled
- NVIDIA Docker runtime not installed

**Solution for Windows/Docker Desktop:**
1. Open Docker Desktop Settings
2. Go to "Resources" → "WSL Integration"
3. Enable GPU support
4. Restart Docker Desktop

**Verification:**
```bash
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

---

## 3. Advanced Troubleshooting

### GPU Detection Script Analysis

The application uses a comprehensive GPU detection script:

```python
# Location: /app/gpu_detect.py
import torch
import sys
import os

def detect_gpu():
    try:
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            print(f"GPU acceleration available: {device_name} ({device_count} device(s))")
            return True
        else:
            print("No GPU acceleration available, using CPU")
            return False
    except Exception as e:
        print(f"Error detecting GPU: {e}, falling back to CPU")
        return False
```

### Manual GPU Testing

```bash
# Test PyTorch CUDA availability
docker exec -it youtube-summarizer python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
if torch.cuda.is_available():
    print(f'GPU count: {torch.cuda.device_count()}')
    print(f'GPU name: {torch.cuda.get_device_name(0)}')
    print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB')
"
```

### Whisper Model Selection Logic

The application automatically selects Whisper models based on GPU availability:

```python
# GPU Available: Uses 'small' model for better accuracy
# CPU Only: Uses 'base' model for faster processing
if torch.cuda.is_available():
    model_name = "small"  # Better accuracy, requires GPU
else:
    model_name = "base"   # Faster processing, CPU-friendly
```

---

## 4. Performance Optimization

### GPU Memory Management

1. **Monitor GPU Memory:**
   ```bash
   watch -n 1 nvidia-smi
   ```

2. **Optimize Model Loading:**
   - Use fp16 precision on GPU (automatically enabled)
   - Reduce batch size if memory issues occur
   - Close other GPU applications

3. **Container Resource Limits:**
   ```yaml
   # docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 4G
       reservations:
         devices:
           - driver: nvidia
             count: all
             capabilities: [gpu]
   ```

### Performance Expectations

| Hardware | Model | Processing Speed | Memory Usage |
|----------|-------|------------------|--------------|
| RTX 3050 Ti | small | 2-3x faster | 2-3GB VRAM |
| RTX 3050 Ti | base | 1.5-2x faster | 1-2GB VRAM |
| CPU Only | base | Baseline | 1-2GB RAM |

---

## 5. Automated Monitoring

### GPU Health Check Script

```bash
#!/bin/bash
# scripts/check_gpu_health.sh

echo "🔍 GPU Health Check"
echo "==================="

# Check host GPU
echo "Host GPU Status:"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader

# Check container GPU
echo -e "\nContainer GPU Status:"
docker exec -it youtube-summarizer nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader

# Check GPU detection
echo -e "\nGPU Detection Test:"
docker exec -it youtube-summarizer python /app/gpu_detect.py

# Check model loading
echo -e "\nModel Device Check:"
docker logs youtube-summarizer | grep -E "(Model loaded on device|Using device)" | tail -2
```

### Continuous Monitoring

```bash
# Monitor GPU utilization during video processing
watch -n 1 'nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader'
```

---

## 6. Emergency Procedures

### Complete GPU Reset

```bash
# Stop all containers
docker stop youtube-summarizer

# Reset Docker
docker system prune -f

# Restart Docker Desktop (Windows)
# Or restart Docker daemon (Linux)

# Rebuild and restart
cd docker
docker-compose up --build -d

# Verify GPU detection
docker logs youtube-summarizer --follow
```

### Fallback to CPU Mode

If GPU continues to fail:

```bash
# Use CPU-only configuration
cd docker
docker-compose -f docker-compose.cpu.yml up -d
```

---

## 7. Prevention Best Practices

### Development Workflow

1. **Always test GPU detection after code changes:**
   ```bash
   python scripts/validate_system.py
   ```

2. **Monitor startup logs:**
   ```bash
   docker logs youtube-summarizer --follow
   ```

3. **Use validation script before deployment:**
   ```bash
   python scripts/validate_system.py
   ```

### Code Change Checklist

After making changes to:
- `app/services/transcription_service.py`
- `app/services/model_manager.py`
- `docker/Dockerfile`
- `docker-compose.yml`

Always run:
```bash
cd docker
docker-compose down
docker-compose up --build -d
docker logs youtube-summarizer --follow
python scripts/validate_system.py
```

---

## 8. Troubleshooting Decision Tree

```
GPU Not Detected?
├── Check container logs for GPU messages
├── Is nvidia-smi working on host?
│   ├── No: Fix NVIDIA drivers
│   └── Yes: Continue
├── Is Docker GPU runtime available?
│   ├── No: Install nvidia-docker runtime
│   └── Yes: Continue
├── Is container running with GPU access?
│   ├── No: Restart with docker-compose
│   └── Yes: Continue
├── Is PyTorch CUDA available in container?
│   ├── No: Rebuild container
│   └── Yes: Check application logs
└── Test with manual GPU detection script
```

---

## 9. Common Error Messages

### "No GPU acceleration available, using CPU"
**Cause:** Container started without GPU access  
**Solution:** Restart with `docker-compose up -d`

### "CUDA out of memory"
**Cause:** GPU memory exhausted  
**Solution:** Close other GPU apps, restart container

### "nvidia runtime not found"
**Cause:** Docker GPU support not enabled  
**Solution:** Enable in Docker Desktop settings

### "Failed to extract any player response"
**Cause:** yt-dlp issue (not GPU related)  
**Solution:** Update yt-dlp or use different video

---

## 10. Support and Resources

### Documentation References
- [DOCKER_GPU_SETUP.md](DOCKER_GPU_SETUP.md) - Initial setup guide
- [DOCKER_TROUBLESHOOTING.md](DOCKER_TROUBLESHOOTING.md) - General troubleshooting
- [scripts/validate_system.py](../scripts/validate_system.py) - System validation

### Testing Commands
```bash
# Run complete system validation
python scripts/validate_system.py

# Test GPU detection only
docker exec -it youtube-summarizer python /app/gpu_detect.py

# Monitor GPU during processing
watch -n 1 nvidia-smi
```

### Emergency Contacts
- Check GitHub issues for similar problems
- Review Docker and NVIDIA documentation
- Test on different hardware if available

---

**Last Updated:** July 16, 2025  
**Tested Configuration:** Windows 11 + Docker Desktop + WSL2 + NVIDIA RTX 3050 Ti  
**Status:** ✅ Working - GPU Detection Reliable
