# Simplified Docker Guide

## ✅ One Simple Rule

**Always use the main Docker Compose configuration:**

```bash
cd docker
docker-compose up -d
```

That's it! This single command handles everything:
- ✅ Works with external Ollama (your current setup)
- ✅ Includes GPU support automatically
- ✅ Proper port mapping (8000:8000)
- ✅ Health checks and monitoring
- ✅ Automatic restart policies

## Why This Works

The main `docker-compose.yml` is configured to:
- Connect to external Ollama via `OLLAMA_HOST=host.docker.internal:11434`
- Detect and use GPU when available
- Fall back to CPU gracefully if GPU isn't available
- Handle all the networking and volume mounting automatically

## No Need for Other Configurations

You can **ignore** these other docker-compose files:
- `docker-compose.external-ollama.yml` - Redundant, main config already works with external Ollama
- `docker-compose.cpu.yml` - Only needed if you want to force CPU mode
- `docker-compose.dev.yml` - Only for development
- Others - Special use cases

## Quick Reference

```bash
# Start the service
cd docker
docker-compose up -d

# Check status
docker ps

# View logs
docker logs youtube-summarizer --follow

# Stop the service
docker-compose down

# Restart after changes
docker-compose down && docker-compose up -d
```

## Validation

After starting, run:
```bash
python scripts/validate_system.py
```

This will confirm:
- Container is running with correct ports
- Web interface is accessible
- GPU detection status
- Ollama connection working

## That's All You Need!

No more confusion about which configuration to use. The main `docker-compose.yml` handles everything for your setup.
