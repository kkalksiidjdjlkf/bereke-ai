# Docker Quick Commands

## 📦 Installation

```bash
# Check Docker is installed
docker --version
docker-compose --version

# If not installed, download from:
# https://www.docker.com/products/docker-desktop
```

## 🏗️ Building

```bash
# Build the Docker image
docker-compose build

# Build without cache (fresh installation)
docker-compose build --no-cache

# Build with custom tag
docker build -t wellbeing-monitor:custom .
```

## 🚀 Running

### Start Monitoring
```bash
# Interactive monitoring session
docker-compose run --rm wellbeing-monitor monitor

# Background monitoring
docker-compose up -d wellbeing-monitor
```

### Query & Analysis
```bash
# Run query tool interactively
docker-compose run --rm wellbeing-monitor query

# List all sessions
docker-compose run --rm wellbeing-monitor \
  python query_database.py --sessions

# View session 1
docker-compose run --rm wellbeing-monitor \
  python query_database.py --session 1

# Generate report
docker-compose run --rm wellbeing-monitor \
  python query_database.py --report 1
```

### Demo & Testing
```bash
# Run demo with sample data
docker-compose run --rm wellbeing-monitor demo

# Interactive shell
docker-compose run --rm wellbeing-monitor shell

# Python shell with system available
docker-compose run --rm wellbeing-monitor app-shell
```

## 📁 Data Management

```bash
# View database
ls -la data/

# Access data from host
cat data/wellbeing_monitor.db

# List reports
ls -la reports/

# List exports
ls -la exports/

# Copy file from container to host
docker cp wellbeing-monitor:/app/data/wellbeing_monitor.db ./

# Copy file from host to container
docker cp ./file.txt wellbeing-monitor:/app/data/
```

## 🔧 Container Management

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d wellbeing-monitor

# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop wellbeing-monitor

# Restart services
docker-compose restart

# Remove containers (keeps volumes)
docker-compose down

# Remove everything including volumes
docker-compose down -v

# Remove without stopping
docker-compose kill

# View running containers
docker-compose ps

# View all containers (including stopped)
docker-compose ps -a
```

## 📊 Logging & Monitoring

```bash
# View logs
docker-compose logs wellbeing-monitor

# Follow logs (realtime)
docker-compose logs -f wellbeing-monitor

# Last 100 lines
docker-compose logs --tail=100 wellbeing-monitor

# Logs from last 10 minutes
docker-compose logs --since 10m wellbeing-monitor

# View all service logs
docker-compose logs

# Container stats (CPU, memory)
docker stats wellbeing-monitor

# View health status
docker-compose exec wellbeing-monitor healthcheck
```

## 🐚 Interactive Access

```bash
# Bash shell in running container
docker-compose exec wellbeing-monitor /bin/bash

# Python interactive shell
docker-compose exec wellbeing-monitor python

# Run single command
docker-compose exec wellbeing-monitor ls -la /app/data

# Check processes
docker-compose exec wellbeing-monitor ps aux

# Check installed packages
docker-compose exec wellbeing-monitor pip list

# Check Python version
docker-compose exec wellbeing-monitor python --version
```

## 🔍 Debugging

```bash
# Inspect image details
docker inspect wellbeing-monitor

# View image layers
docker history wellbeing-monitor:latest

# Validate compose file
docker-compose config

# Dry-run (don't actually execute)
docker-compose up --dry-run

# Shell without running app
docker-compose run --rm --entrypoint=/bin/bash wellbeing-monitor

# Check network connectivity
docker-compose exec wellbeing-monitor ping postgres

# Test database connection
docker-compose exec wellbeing-monitor \
  python -c "from database import WellbeingDatabase; print('OK')"
```

## 🗄️ Database Management

```bash
# Connect to PostgreSQL
docker-compose exec postgres \
  psql -U wellbeing -d wellbeing_monitor

# Connect to SQLite
docker-compose exec wellbeing-monitor \
  sqlite3 /app/data/wellbeing_monitor.db

# pgAdmin web interface (optional)
# http://localhost:5050
# Login: admin@wellbeing.local / admin

# Backup database
docker-compose exec wellbeing-monitor \
  cp /app/data/wellbeing_monitor.db /app/exports/backup.db

# Restore database
docker-compose exec wellbeing-monitor \
  cp /app/exports/backup.db /app/data/wellbeing_monitor.db
```

## 🌐 Network & Ports

```bash
# View network info
docker-compose exec wellbeing-monitor ifconfig

# Check port bindings
docker-compose port wellbeing-monitor 8000

# Test port connectivity
docker-compose exec wellbeing-monitor curl localhost:8000

# View all networks
docker network ls

# Inspect network
docker network inspect wellbeing_wellbeing-network
```

## 📤 Publishing & Registry

```bash
# Tag image
docker tag wellbeing-monitor:latest \
  yourusername/wellbeing-monitor:1.0

# Push to Docker Hub
docker push yourusername/wellbeing-monitor:1.0

# Pull from Docker Hub
docker pull yourusername/wellbeing-monitor:1.0

# Save image to file
docker save wellbeing-monitor:latest | gzip > image.tar.gz

# Load image from file
docker load < image.tar.gz
```

## 🧹 Cleanup

```bash
# Remove unused images
docker image prune

# Remove unused containers
docker container prune

# Remove unused networks
docker network prune

# Remove unused volumes
docker volume prune

# Clean everything (careful!)
docker system prune -a

# View disk usage
docker system df
```

## 🔐 Security

```bash
# Run container as non-root
docker-compose run --rm --user 1000:1000 wellbeing-monitor shell

# Run read-only filesystem
docker-compose run --rm --read-only wellbeing-monitor query

# Limit resources
docker-compose run \
  --rm \
  --memory=512m \
  --cpus=1 \
  wellbeing-monitor monitor

# View seccomp profile
docker inspect wellbeing-monitor --format="{{.ProcessLabel}}"
```

## 📋 Common Workflows

### First-time setup
```bash
docker-compose build
docker-compose up -d
docker-compose logs -f
```

### Monitor once and view results
```bash
docker-compose run --rm wellbeing-monitor monitor
docker-compose run --rm wellbeing-monitor query
```

### Daily monitoring
```bash
# Morning
docker-compose run --rm wellbeing-monitor monitor

# Evening
docker-compose run --rm wellbeing-monitor monitor

# View comparison
docker-compose run --rm wellbeing-monitor \
  python query_database.py --compare 1,2
```

### Backup workflow
```bash
docker-compose exec wellbeing-monitor \
  cp /app/data/wellbeing_monitor.db /app/exports/backup_$(date +%Y%m%d).db
```

## 🚨 Troubleshooting Commands

```bash
# What went wrong?
docker-compose logs --tail=50

# Too much output?
docker-compose logs 2>&1 | grep ERROR

# Docker daemon not running?
docker ps  # Will show error if daemon stopped

# Out of disk space?
docker system df  # Check usage

# Can't build?
docker-compose build --progress=plain  # See detailed output

# Port already in use?
docker ps -a  # Find container using port
docker stop <container_id>

# Database locked?
docker-compose down -v  # Remove everything and start fresh
```

## 📚 Documentation

- Full guide: `DOCKER_GUIDE.md`
- Docker docs: `https://docs.docker.com`
- Compose reference: `https://docs.docker.com/compose/compose-file/`

---

**Pro Tips:**
1. Use `docker-compose` instead of `docker` for this project
2. Add `--rm` flag to automatically remove containers
3. Use `-f` flag to follow logs in realtime
4. Set up `.env` file for configuration
5. Backup your database regularly!

**Quick Start:**
```bash
docker-compose build
docker-compose up -d
docker-compose logs -f wellbeing-monitor
```
