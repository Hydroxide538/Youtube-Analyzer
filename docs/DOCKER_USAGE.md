# Docker Usage Guide

## 🐳 Docker Overview

The YouTube & Conference Video Analyzer supports multiple Docker deployment configurations to accommodate different use cases and infrastructure setups. This guide covers all Docker-related aspects of the application.

## 📦 Available Docker Configurations

### 1. Standard Configuration (`docker-compose.yml`)
**Best for**: Most users, includes all services
```yaml
# Includes:
# - YouTube Analyzer application
# - Internal Ollama service
# - Proper networking and volume management
```

### 2. External Ollama Configuration (`docker-compose.external-ollama.yml`)
**Best for**: Users with existing Ollama installations
```yaml
# Includes:
# - YouTube Analyzer application only
# - Connects to external Ollama service
# - Reduced resource usage
```

### 3. Bridge Networking Configuration (`docker-compose.bridge.yml`)
**Best for**: Complex network setups, multiple services
```yaml
# Features:
# - Standard Docker bridge networking
# - Explicit network configuration
# - Better for multi-container environments
```

### 4. Development Configuration (`docker-compose.dev.yml`)
**Best for**: Development and testing
```yaml
# Features:
# - Live code reloading
# - Development environment variables
# - Volume mounts for code changes
```

### 5. GPU Configuration (`docker-compose.gpu.yml`)
**Best for**: GPU-accelerated processing
```yaml
# Features:
# - NVIDIA GPU support
# - CUDA acceleration for AI models
# - Enhanced performance for large models
```

## 🚀 Quick Start

### Standard Deployment
```bash
# Clone repository
git clone https://github.com/Hydroxide538/Youtube-Analyzer.git
cd Youtube-Analyzer

# Start all services
docker-compose up --build

# Access application
open http://localhost:8000
```

### External Ollama Deployment
```bash
# If you have Ollama running separately
docker-compose -f docker-compose.external-ollama.yml up --build

# Or with custom Ollama host
OLLAMA_HOST=your-ollama-host:11434 docker-compose -f docker-compose.external-ollama.yml up --build
```

## 🔧 Configuration Details

### Environment Variables

#### Application Configuration
```bash
# Core application settings
HOST=0.0.0.0                    # Server host
PORT=8000                       # Server port
PYTHONPATH=/app                 # Python path for imports
LOG_LEVEL=INFO                  # Logging level (DEBUG, INFO, WARNING, ERROR)
ENVIRONMENT=production          # Environment (development, production)

# AI Provider Configuration
OLLAMA_HOST=localhost:11434     # Ollama server host
OPENAI_API_KEY=sk-your-key      # OpenAI API key (optional)
ANTHROPIC_API_KEY=sk-ant-key    # Anthropic API key (optional)

# Conference Video Configuration
CHROME_BINARY_PATH=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

#### Docker-Specific Variables
```bash
# Container configuration
CONTAINER_NAME=youtube-analyzer
RESTART_POLICY=unless-stopped

# Resource limits
MEMORY_LIMIT=4g
MEMORY_RESERVATION=2g
CPU_LIMIT=2.0

# Network configuration
NETWORK_NAME=youtube-analyzer-network
BRIDGE_NETWORK=bridge
```

### Volume Management

#### Application Volumes
```yaml
volumes:
  # Application data (temporary files)
  - app_data:/app/data
  
  # Ollama models (if using internal Ollama)
  - ollama_models:/root/.ollama
  
  # Chrome user data (for conference videos)
  - chrome_data:/home/chromeuser/.config/google-chrome
  
  # Temporary processing files
  - temp_data:/tmp
```

#### Volume Cleanup
```bash
# Remove all application volumes
docker-compose down -v

# Remove specific volumes
docker volume rm youtube-analyzer_app_data
docker volume rm youtube-analyzer_ollama_models

# Clean up unused volumes
docker volume prune
```

## 🛠️ Advanced Configuration

### Custom Docker Compose Override

#### Create Override File
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  youtube-summarizer:
    environment:
      - CUSTOM_SETTING=value
    ports:
      - "8001:8000"  # Use different port
    volumes:
      - ./custom_config:/app/config
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'
```

#### Usage
```bash
# Override file is automatically loaded
docker-compose up --build
```

### GPU Support Configuration

#### Prerequisites
```bash
# Install NVIDIA Docker support
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

#### GPU Docker Compose
```yaml
# docker-compose.gpu.yml
version: '3.8'
services:
  youtube-summarizer:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### Usage
```bash
# Run with GPU support
docker-compose -f docker-compose.gpu.yml up --build

# Verify GPU access
docker exec -it youtube-analyzer nvidia-smi
```

### Multi-Stage Build Configuration

#### Optimized Dockerfile
```dockerfile
# docker/Dockerfile.optimized
FROM python:3.11-slim as base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base as development
ENV ENVIRONMENT=development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base as production
ENV ENVIRONMENT=production
COPY . .
RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### Build Commands
```bash
# Build development image
docker build --target development -t youtube-analyzer:dev .

# Build production image
docker build --target production -t youtube-analyzer:prod .
```

## 🔍 Monitoring and Debugging

### Container Health Checks

#### Health Check Configuration
```yaml
# docker-compose.yml
services:
  youtube-summarizer:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

#### Health Check Commands
```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect youtube-analyzer --format='{{json .State.Health}}'

# Manual health check
docker exec youtube-analyzer curl -f http://localhost:8000/health
```

### Resource Monitoring

#### Container Stats
```bash
# Real-time resource usage
docker stats youtube-analyzer

# Detailed container information
docker inspect youtube-analyzer

# Container logs
docker logs youtube-analyzer -f
```

#### Resource Limits
```yaml
# Set resource limits
services:
  youtube-summarizer:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

### Log Management

#### Log Configuration
```yaml
# docker-compose.yml
services:
  youtube-summarizer:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
```

#### Log Commands
```bash
# View logs
docker-compose logs youtube-summarizer

# Follow logs
docker-compose logs -f youtube-summarizer

# View logs with timestamps
docker-compose logs -t youtube-summarizer

# Filter logs by time
docker-compose logs --since="2024-01-01T00:00:00" youtube-summarizer
```

## 🚨 Troubleshooting

### Common Docker Issues

#### Container Won't Start
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs youtube-summarizer

# Check configuration
docker-compose config

# Restart specific service
docker-compose restart youtube-summarizer
```

#### Port Conflicts
```bash
# Find process using port
sudo lsof -i :8000
sudo netstat -tulpn | grep :8000

# Kill conflicting process
sudo kill -9 $(sudo lsof -t -i:8000)

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

#### Network Issues
```bash
# Check network configuration
docker network ls
docker network inspect youtube-analyzer_default

# Test network connectivity
docker exec -it youtube-analyzer ping ollama
docker exec -it youtube-analyzer curl http://ollama:11434/api/tags

# Recreate network
docker-compose down
docker network prune
docker-compose up --build
```

#### Volume Issues
```bash
# Check volumes
docker volume ls
docker volume inspect youtube-analyzer_app_data

# Clean up volumes
docker-compose down -v
docker volume prune

# Backup volumes
docker run --rm -v youtube-analyzer_app_data:/data -v $(pwd):/backup ubuntu tar czf /backup/backup.tar.gz /data
```

### Performance Issues

#### Memory Problems
```bash
# Monitor memory usage
docker stats youtube-analyzer

# Increase memory limit
# In docker-compose.yml
mem_limit: 8g
memswap_limit: 8g

# Or set in override file
services:
  youtube-summarizer:
    deploy:
      resources:
        limits:
          memory: 8G
```

#### CPU Issues
```bash
# Monitor CPU usage
docker stats youtube-analyzer

# Limit CPU usage
# In docker-compose.yml
cpus: '2.0'

# Or set CPU shares
cpu_shares: 1024
```

#### Disk Space Issues
```bash
# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a

# Remove unused volumes
docker volume prune

# Remove unused images
docker image prune -a
```

## 🔄 Updates and Maintenance

### Updating the Application

#### Standard Update
```bash
# Stop services
docker-compose down

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up --build
```

#### Zero-Downtime Update
```bash
# Build new image
docker-compose build youtube-summarizer

# Rolling update
docker-compose up --no-deps -d youtube-summarizer

# Verify update
docker-compose ps
```

### Backup and Restore

#### Backup Configuration
```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup docker-compose files
cp docker-compose*.yml backups/$(date +%Y%m%d)/

# Backup environment files
cp .env backups/$(date +%Y%m%d)/

# Backup volumes
docker run --rm -v youtube-analyzer_app_data:/data -v $(pwd)/backups:/backup ubuntu tar czf /backup/app_data_$(date +%Y%m%d).tar.gz /data
```

#### Restore Configuration
```bash
# Restore from backup
cd backups/20240101
cp docker-compose*.yml ../../
cp .env ../../

# Restore volumes
docker run --rm -v youtube-analyzer_app_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/app_data_20240101.tar.gz -C /
```

### Maintenance Tasks

#### Regular Maintenance
```bash
# Clean up unused resources (weekly)
docker system prune -f

# Update base images (monthly)
docker-compose pull
docker-compose up --build

# Check for security updates
docker scan youtube-analyzer:latest

# Backup volumes (daily)
./scripts/backup_volumes.sh
```

#### Health Monitoring
```bash
# Check container health
docker-compose ps

# Monitor resource usage
docker stats --no-stream

# Check logs for errors
docker-compose logs --tail=100 | grep -i error

# Test application endpoints
curl -f http://localhost:8000/health
curl -f http://localhost:8000/api/models
```

## 📈 Production Deployment

### Production Configuration

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  youtube-summarizer:
    image: youtube-analyzer:latest
    container_name: youtube-analyzer-prod
    restart: always
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    ports:
      - "80:8000"
    volumes:
      - prod_data:/app/data
    networks:
      - prod_network
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

volumes:
  prod_data:
    driver: local

networks:
  prod_network:
    driver: bridge
```

#### Production Deployment
```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Scaling Configuration

#### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  youtube-summarizer:
    image: youtube-analyzer:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    networks:
      - app_network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - youtube-summarizer
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
```

#### Load Balancer Configuration
```nginx
# nginx.conf
upstream app_servers {
    server youtube-summarizer:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws {
        proxy_pass http://app_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🛡️ Security Considerations

### Container Security

#### Security Best Practices
```dockerfile
# Use non-root user
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
USER appuser

# Minimal base image
FROM python:3.11-alpine

# Read-only filesystem
docker run --read-only --tmpfs /tmp youtube-analyzer:latest

# Drop capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE youtube-analyzer:latest
```

#### Security Scanning
```bash
# Scan for vulnerabilities
docker scan youtube-analyzer:latest

# Use security-focused base images
FROM python:3.11-slim-bullseye

# Keep images updated
docker-compose pull
docker-compose up --build
```

### Network Security

#### Network Isolation
```yaml
# Isolated networks
networks:
  frontend:
    driver: bridge
    internal: false
  backend:
    driver: bridge
    internal: true
```

#### Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 8000/tcp
ufw deny 11434/tcp  # Block direct Ollama access

# Use Docker networks instead of host networking
network_mode: bridge  # Instead of host
```

---

**Note**: This guide covers the main Docker usage patterns. For specific deployment scenarios or advanced configurations, refer to the main documentation or create custom Docker configurations based on these examples.
