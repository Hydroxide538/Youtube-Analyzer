# GPU-Enabled Docker Setup for YouTube Analyzer

This document explains how to set up the YouTube Analyzer with GPU acceleration for NVIDIA systems, while maintaining compatibility with CPU-only systems.

## Prerequisites

### For NVIDIA GPU Systems

1. **NVIDIA GPU with CUDA support** (GTX 10 series or newer recommended)
2. **NVIDIA Docker Runtime** installed on your system
3. **Docker Desktop** with GPU support enabled

#### Installing NVIDIA Docker Runtime

**Windows (Docker Desktop):**
1. Install Docker Desktop
2. Enable GPU support in Docker Desktop settings
3. Ensure WSL2 backend is enabled with GPU support

**Linux:**
```bash
# Install NVIDIA Docker runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### For CPU-Only Systems

No additional setup required - the system will automatically fall back to CPU processing.

## Configuration Files

### 1. GPU-Enabled (Default)

The main `docker-compose.yml` file is configured for GPU acceleration:

```yaml
services:
  youtube-summarizer:
    deploy:
      resources:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

### 2. CPU-Only Fallback

For systems without GPU support, use `docker-compose.cpu.yml`:

```yaml
services:
  youtube-summarizer:
    build: .
    # GPU configuration removed for CPU-only systems
```

## Usage

### For NVIDIA GPU Systems

1. **Verify GPU support:**
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

2. **Run with GPU acceleration:**
   ```bash
   docker compose up --build
   ```

3. **Monitor GPU usage:**
   ```bash
   nvidia-smi
   ```

### For CPU-Only Systems

1. **Use CPU-only configuration:**
   ```bash
   docker compose -f docker-compose.cpu.yml up --build
   ```

2. **Or modify the main docker-compose.yml:**
   - Remove the `devices` section from `deploy`
   - Remove GPU-related environment variables

## Automatic Hardware Detection

The application includes automatic hardware detection:

1. **Build time:** The Dockerfile attempts to install GPU-enabled PyTorch first, falling back to CPU version if needed
2. **Runtime:** The application detects available hardware and configures itself accordingly
3. **Model selection:** Uses larger Whisper models on GPU for better accuracy, smaller models on CPU for speed

## Performance Comparison

### GPU vs CPU Processing Times (Approximate)

| Video Length | GPU (NVIDIA RTX 3080) | CPU (Intel i7-10700K) |
|--------------|----------------------|----------------------|
| 5 minutes    | 30 seconds           | 2 minutes            |
| 30 minutes   | 2 minutes            | 10 minutes           |
| 1 hour       | 4 minutes            | 20 minutes           |

### Model Selection

- **GPU:** Uses `small` Whisper model for better accuracy
- **CPU:** Uses `base` Whisper model for faster processing

## Troubleshooting

### Common Issues

1. **GPU not detected:**
   - Verify NVIDIA Docker runtime is installed
   - Check GPU availability: `nvidia-smi`
   - Ensure Docker has GPU access

2. **CUDA out of memory:**
   - Reduce batch size in processing
   - Use smaller Whisper model
   - Close other GPU-intensive applications

3. **Slow performance on GPU:**
   - Check GPU utilization with `nvidia-smi`
   - Verify CUDA version compatibility
   - Ensure adequate VRAM (4GB+ recommended)

4. **Build timeout issues:**
   - Increase Docker build timeout
   - Use local PyTorch index for faster downloads
   - Check internet connection stability

### Fallback Behavior

If GPU setup fails:
1. Application automatically falls back to CPU processing
2. Logs will indicate the fallback with device information
3. No functionality is lost, only processing speed is affected

## Environment Variables

### GPU-Related Variables

```bash
# Enable all GPUs
NVIDIA_VISIBLE_DEVICES=all

# Enable compute and utility capabilities
NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Force CPU mode (override GPU detection)
FORCE_CPU=true
```

### Application Variables

```bash
# Whisper model size (auto-selected based on hardware)
WHISPER_MODEL=auto  # or base, small, medium, large

# Maximum video length for processing
MAX_VIDEO_LENGTH=3600  # seconds

# Enable debug logging
DEBUG=true
```

## Monitoring

### GPU Usage

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Detailed GPU info
nvidia-smi -l 1

# GPU utilization logs
docker logs youtube-summarizer | grep -i gpu
```

### Application Logs

```bash
# View application logs
docker logs youtube-summarizer

# Follow logs in real-time
docker logs -f youtube-summarizer

# Filter GPU-related logs
docker logs youtube-summarizer | grep -i "device\|gpu\|cuda"
```

## Optimization Tips

### For GPU Systems

1. **Use larger models** for better accuracy when GPU memory allows
2. **Batch processing** for multiple videos
3. **Monitor GPU memory** usage during processing
4. **Close unnecessary applications** to free GPU memory

### For CPU Systems

1. **Use smaller models** for faster processing
2. **Limit concurrent processing** to avoid overloading CPU
3. **Consider video length limits** for reasonable processing times
4. **Optimize Docker resource limits**

## Security Considerations

1. **GPU access** requires privileged Docker containers
2. **Network exposure** should be limited to necessary ports
3. **Volume mounts** should be restricted to required directories
4. **Environment variables** should not contain sensitive data

## Future Enhancements

1. **Multi-GPU support** for parallel processing
2. **AMD GPU support** (ROCm integration)
3. **Apple Silicon** optimization (Metal Performance Shaders)
4. **Cloud GPU** integration (AWS, GCP, Azure)
5. **Dynamic model selection** based on available resources
