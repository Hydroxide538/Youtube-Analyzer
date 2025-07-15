# External Ollama Setup Guide

This guide explains how to use the YouTube Video Summarizer with your existing Ollama Docker container.

## Prerequisites

- Your existing Ollama Docker container is running
- Ollama is accessible on port 11434
- You have models installed in your Ollama container

## Setup Options

### Option 1: Using Host Networking (Recommended)

Use the provided `docker-compose.external-ollama.yml` file:

```bash
# Build and run the application
docker-compose -f docker-compose.external-ollama.yml up --build
```

**Configuration:**
- Uses host networking to access your Ollama container
- Set `OLLAMA_HOST=host.docker.internal:11434` in the environment
- No additional network configuration needed

### Option 2: Custom Network Configuration

If your Ollama container is on a specific Docker network:

1. **Find your Ollama container network:**
   ```bash
   docker inspect your-ollama-container | grep NetworkMode
   ```

2. **Update the docker-compose.external-ollama.yml:**
   ```yaml
   services:
     youtube-summarizer:
       environment:
         - OLLAMA_HOST=your-ollama-container-name:11434
       networks:
         - your-existing-network
   
   networks:
     your-existing-network:
       external: true
   ```

3. **Run the application:**
   ```bash
   docker-compose -f docker-compose.external-ollama.yml up --build
   ```

### Option 3: Direct IP Address

If you know your Ollama container's IP address:

```yaml
environment:
  - OLLAMA_HOST=192.168.1.100:11434  # Replace with actual IP
```

## Verification

1. **Check Ollama connectivity:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Start the application:**
   ```bash
   docker-compose -f docker-compose.external-ollama.yml up --build
   ```

3. **Access the web interface:**
   Open http://localhost:8000

4. **Test model selection:**
   - Click "Advanced Options"
   - Verify that your installed models appear in the dropdown
   - Select your preferred model

## Troubleshooting

### Connection Issues

**Problem:** "Failed to fetch models from Ollama"
**Solutions:**
- Verify Ollama is running: `docker ps | grep ollama`
- Check Ollama API: `curl http://localhost:11434/api/tags`
- Update OLLAMA_HOST environment variable
- Ensure firewall allows port 11434

### Network Issues

**Problem:** "Ollama service is not responding"
**Solutions:**
- Check Docker network connectivity
- Try host networking mode
- Verify container can reach Ollama host
- Check Docker logs: `docker logs youtube-summarizer`

### Model Issues

**Problem:** "Selected model not available"
**Solutions:**
- List available models: `curl http://localhost:11434/api/tags`
- Pull missing models: `docker exec ollama-container ollama pull model-name`
- Refresh the web interface

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `localhost:11434` | Ollama server host and port |
| `PYTHONPATH` | `/app` | Python module path |

## Network Configurations

### Common Ollama Container Setups

**1. Ollama with host networking:**
```yaml
environment:
  - OLLAMA_HOST=localhost:11434
network_mode: host
```

**2. Ollama on custom bridge network:**
```yaml
environment:
  - OLLAMA_HOST=ollama:11434
networks:
  - ollama-network
```

**3. Ollama on Docker default bridge:**
```yaml
environment:
  - OLLAMA_HOST=host.docker.internal:11434
```

## Performance Tips

- **Model Selection:** Choose smaller models for faster processing
- **Memory:** Allocate at least 4GB to the application container
- **Network:** Use local Docker networks for better performance
- **Storage:** Ensure sufficient disk space for temporary files

## Security Considerations

- Ollama API has no authentication by default
- Use Docker networks to isolate containers
- Consider firewall rules for production deployments
- Monitor container resource usage

## Example Complete Setup

```bash
# 1. Verify existing Ollama container
docker ps | grep ollama

# 2. Test Ollama connectivity
curl http://localhost:11434/api/tags

# 3. Clone the YouTube Summarizer
git clone <repository-url>
cd youtube-analyzer

# 4. Run with external Ollama
docker-compose -f docker-compose.external-ollama.yml up --build

# 5. Access the application
open http://localhost:8000
```

## Support

If you encounter issues:
1. Check the build notes in `build_notes/change_log.md`
2. Review Docker logs: `docker logs youtube-summarizer`
3. Verify Ollama functionality independently
4. Check network connectivity between containers
