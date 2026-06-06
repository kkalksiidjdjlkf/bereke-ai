# Docker Setup & Deployment Guide

## 🐳 Docker Overview

The Wellbeing Monitoring System is fully containerized for:
- ✅ Easy deployment across systems
- ✅ Guaranteed environment consistency
- ✅ Isolated dependencies
- ✅ Simple scaling
- ✅ Microservices support

## 📋 Prerequisites

### Required
- Docker (v20.10+): https://docs.docker.com/get-docker/
- Docker Compose (v1.29+): https://docs.docker.com/compose/install/
- At least 2GB disk space

### Optional
- Docker Desktop (includes Docker and Compose)
- GPU support (for accelerated processing)

## 🚀 Quick Start

### 1. Verify Docker Installation

```bash
docker --version
docker-compose --version
docker ps
```

Expected output:
```
Docker version 20.10.0+
Docker Compose version 1.29.0+
CONTAINER ID        IMAGE        ...
```

### 2. Build Docker Image

```bash
# Navigate to project directory
cd /Users/maks/Desktop/стартап

# Build the image
docker-compose build

# Or build without cache for fresh installation
docker-compose build --no-cache
```

### 3. Start the System

#### Option A: Interactive Monitoring
```bash
# Start monitoring with accessible camera/microphone
docker-compose run --rm wellbeing-monitor monitor
```

#### Option B: Query Tool
```bash
# Run query and analysis tool
docker-compose run --rm wellbeing-monitor query
```

#### Option C: Demo
```bash
# Run demonstration with sample data
docker-compose run --rm wellbeing-monitor demo
```

#### Option D: Background Services
```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f wellbeing-monitor

# Stop services
docker-compose down
```

## 📊 Service Architecture

### Main Services

**wellbeing-monitor** (Main Application)
- Real-time monitoring system
- Face, voice, breathing analysis
- Database storage
- Report generation

**postgres** (Database)
- Advanced data storage
- Multi-session support
- Analytics queries
- Backup support

**pgAdmin** (Database UI)
- Visual database management
- Query builder
- Data export
- Available at: http://localhost:5050

**redis** (Cache)
- Fast data caching
- Session management
- Performance optimization

## 🎯 Usage Examples

### Running Monitoring with Hardware Access

```bash
# Linux with X11 display
docker-compose run \
  -e DISPLAY=$DISPLAY \
  --volume=$HOME/.Xauthority:/root/.Xauthority:rw \
  --rm wellbeing-monitor monitor

# macOS (requires XQuartz)
docker-compose run \
  -e DISPLAY=host.docker.internal:0 \
  --rm wellbeing-monitor monitor

# Windows (use Docker Desktop)
docker-compose run --rm wellbeing-monitor monitor
```

### Running in Background

```bash
# Start all services
docker-compose up -d

# Start just the monitoring service
docker-compose up -d wellbeing-monitor

# View live logs
docker-compose logs -f wellbeing-monitor

# View logs from past hour
docker-compose logs --since 1h wellbeing-monitor
```

### Interactive Shell Access

```bash
# Bash shell
docker-compose run --rm wellbeing-monitor shell

# Python interactive shell
docker-compose run --rm wellbeing-monitor app-shell

# Run custom command
docker-compose run --rm wellbeing-monitor python query_database.py --sessions
```

## 📁 Volume Management

### Persistent Data Locations

**Inside Container** → **Host Machine**

```
/app/data/          → ./data/
/app/reports/       → ./reports/
/app/exports/       → ./exports/
```

### Accessing Data

```bash
# View database
ls -la data/wellbeing_monitor.db

# View reports
ls -la reports/

# View exports
ls -la exports/

# Copy from container
docker cp wellbeing-monitor:/app/data/wellbeing_monitor.db ./

# Copy to container
docker cp ./myfile.txt wellbeing-monitor:/app/data/
```

## 🔧 Configuration

### Environment Variables

Create `.env` file in project directory:

```env
# Database
POSTGRES_USER=wellbeing
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=wellbeing_monitor

# Monitoring
MONITORING_DURATION=60
CHECK_INTERVAL=5
CAMERA_ID=0

# Logging
LOG_LEVEL=INFO

# Timezone
TZ=UTC
```

### Using Environment File

```bash
docker-compose --env-file .env up -d
```

### Runtime Configuration

Edit `config.py` before building:

```python
# Open config.py and modify:
MONITORING_DURATION_SECONDS = 60
CHECK_INTERVAL_SECONDS = 5
CAMERA_ID = 0
```

Then rebuild:
```bash
docker-compose build --no-cache
```

## 🖥️ Hardware Access

### Camera Access

```yaml
# In docker-compose.yml
devices:
  - /dev/video0:/dev/video0  # First camera
  - /dev/video1:/dev/video1  # Second camera
```

### Microphone/Audio Access

```yaml
devices:
  - /dev/snd:/dev/snd        # Sound devices
```

### GPU Access (Optional)

```yaml
services:
  wellbeing-monitor:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Requires nvidia-docker: https://github.com/NVIDIA/nvidia-docker

## 📊 Database Access

### Connect from Host

```bash
# Using sqlite3
sqlite3 data/wellbeing_monitor.db

# Using command-line tools
docker-compose exec postgres psql -U wellbeing -d wellbeing_monitor

# Using pgAdmin (web UI)
# Open: http://localhost:5050
# Login: admin@wellbeing.local / admin
```

### Query from Python

```python
from database import WellbeingDatabase
db = WellbeingDatabase("data/wellbeing_monitor.db")
sessions = db.get_user_history()
```

## 🔐 Security

### Docker Security Best Practices

```bash
# Run with read-only filesystem
docker-compose run --rm --read-only wellbeing-monitor query

# Run with reduced privileges
docker-compose run --rm --user 1000:1000 wellbeing-monitor query

# Limit resources
docker-compose run \
  --rm \
  --memory=512m \
  --cpus=1 \
  wellbeing-monitor monitor
```

### Network Security

```yaml
# Isolated network
networks:
  wellbeing-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

### Secret Management

```bash
# Create secret file
echo "your-password" | docker secret create db_password -

# Use in compose
docker secret ls
```

## 🔍 Monitoring & Debugging

### View Container Status

```bash
# List running containers
docker-compose ps

# View container logs
docker-compose logs wellbeing-monitor

# Follow logs in real-time
docker-compose logs -f wellbeing-monitor

# View last 100 lines
docker-compose logs --tail=100 wellbeing-monitor

# View logs from specific time
docker-compose logs --since 10m wellbeing-monitor
```

### System Health

```bash
# Check health status
docker-compose exec wellbeing-monitor healthcheck || echo "Unhealthy"

# View container stats
docker stats wellbeing-monitor

# View detailed container info
docker inspect wellbeing-monitor
```

### Debugging

```bash
# Connect to running container
docker-compose exec wellbeing-monitor bash

# View container processes
docker-compose exec wellbeing-monitor ps aux

# Check Python packages
docker-compose exec wellbeing-monitor pip freeze

# Test imports
docker-compose exec wellbeing-monitor python -c "import cv2; print('OK')"
```

## 🛠️ Troubleshooting

### Build Issues

```bash
# Clear build cache
docker-compose build --no-cache

# Remove old images
docker image prune -a

# Check build output
docker-compose build --verbose
```

### Runtime Issues

```bash
# No input device error
# → Add to docker-compose.yml:
devices:
  - /dev/video0:/dev/video0
  - /dev/snd:/dev/snd

# Permission denied
# → Run with elevated privileges:
docker-compose run --rm --privileged wellbeing-monitor monitor

# Out of memory
# → Increase Docker memory allocation
# Desktop: Settings → Resources → Memory
```

### Database Issues

```bash
# Reset database
docker-compose run --rm wellbeing-monitor shell
rm /app/data/wellbeing_monitor.db
exit

# Check database integrity
docker-compose run --rm wellbeing-monitor \
  sqlite3 /app/data/wellbeing_monitor.db ".integrity_check"
```

## 📦 Docker Commands Reference

### Build & Push

```bash
# Build image
docker-compose build

# Tag image
docker tag wellbeing-monitor:latest myregistry/wellbeing-monitor:1.0

# Push to registry
docker push myregistry/wellbeing-monitor:1.0

# Pull from registry
docker pull myregistry/wellbeing-monitor:1.0
```

### Container Management

```bash
# Start in background
docker-compose up -d

# Start specific service
docker-compose up -d wellbeing-monitor

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Remove containers
docker-compose down

# Full cleanup (including volumes)
docker-compose down -v
```

### Scaling

```bash
# Scale monitoring service to 3 instances
docker-compose up -d --scale wellbeing-monitor=3

# View running instances
docker-compose ps
```

## 🚀 Production Deployment

### Docker Hub

```bash
# Build for hub
docker build -t yourusername/wellbeing-monitor:1.0 .

# Push to Docker Hub
docker push yourusername/wellbeing-monitor:1.0

# Pull from Docker Hub
docker pull yourusername/wellbeing-monitor:1.0
```

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml wellbeing

# View services
docker service ls

# Scale service
docker service scale wellbeing_wellbeing-monitor=3
```

### Kubernetes

```bash
# Generate Kubernetes manifests
docker-compose convert > kubernetes.yml

# Deploy to Kubernetes
kubectl apply -f kubernetes.yml

# View deployment
kubectl get pods
```

## 📈 Performance Optimization

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Multi-Stage Build

```dockerfile
FROM python:3.11-slim as builder
# ... build dependencies ...

FROM python:3.11-slim
COPY --from=builder /app /app
# ... minimal runtime ...
```

### Caching

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker-compose build

# Cache mount for pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements_new.txt
```

## 🎓 Learning Resources

- Docker Documentation: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Best Practices: https://docs.docker.com/develop/dev-best-practices/
- Container Security: https://docs.docker.com/engine/security/

## 📞 Support & Help

```bash
# Get Docker help
docker --help
docker-compose --help

# Check Docker logs
docker system events

# Resource usage
docker system df

# Run diagnostics
docker system info
```

## 🎉 Success Checklist

- ✅ Docker installed and running
- ✅ docker-compose.yml configured
- ✅ Image built successfully
- ✅ Containers start without errors
- ✅ Database initializes
- ✅ Monitoring runs
- ✅ Data persists across restarts

---

**Docker Setup Status**: ✅ COMPLETE AND READY FOR DEPLOYMENT!

The Wellbeing Monitoring System is fully containerized and ready for production use!
