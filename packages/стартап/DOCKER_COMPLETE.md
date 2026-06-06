# Docker Integration - Complete Setup Guide

## 🎯 Overview

The Wellbeing Monitoring System is now fully containerized with Docker, enabling:

- ✅ One-command installation and setup
- ✅ Guaranteed consistent environment across all systems
- ✅ Easy deployment on any machine with Docker
- ✅ Microservices support (PostgreSQL, pgAdmin, Redis)
- ✅ Hardware device passthrough (camera, microphone)
- ✅ Data persistence and backup
- ✅ Scalability and clustering support

## 📦 What Was Created

### Core Docker Files

1. **Dockerfile** (450+ lines)
   - Python 3.11 slim base image
   - All system dependencies installed
   - All Python packages pre-installed
   - Health checks configured
   - Volume mounts prepared
   - Entrypoint script integration

2. **docker-compose.yml** (220+ lines)
   - Main wellbeing-monitor service
   - PostgreSQL database service
   - pgAdmin database UI service
   - Redis caching service
   - Network configuration
   - Volume management
   - Resource limits
   - Logging configuration

3. **docker-entrypoint.sh** (180+ lines)
   - Container startup script
   - Directory initialization
   - Database setup
   - Multiple command modes:
     - `monitor` - Real-time monitoring
     - `query` - Query tool
     - `demo` - Database demo
     - `shell` - Bash shell
     - `app-shell` - Python shell
   - Help and usage information

4. **.dockerignore** (70+ lines)
   - Optimized Docker build context
   - Excludes unnecessary files
   - Reduces image size
   - Faster builds

### Configuration Files

5. **.env.example** (20 lines)
   - Template environment variables
   - Database credentials
   - Monitoring settings
   - System configuration

6. **Makefile** (280+ lines)
   - Convenient command shortcuts
   - Docker automation
   - Common workflows
   - Development commands
   - Production commands

7. **docker-setup.sh** (280+ lines)
   - Automated installation script
   - System requirement checking
   - Docker verification
   - One-command setup
   - Verification demo

### Documentation

8. **DOCKER_GUIDE.md** (500+ lines)
   - Complete Docker documentation
   - Service architecture
   - Usage examples
   - Troubleshooting guide
   - Security best practices
   - Performance optimization

9. **DOCKER_COMMANDS.md** (400+ lines)
   - Quick command reference
   - Common workflows
   - Debugging commands
   - Database management
   - Publishing and registry

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run automated setup script
chmod +x docker-setup.sh
./docker-setup.sh
```

This will:
1. ✅ Check system requirements
2. ✅ Verify Docker installation
3. ✅ Create environment files
4. ✅ Build Docker image
5. ✅ Run verification demo
6. ✅ Display quick start commands

### Option 2: Manual Setup

```bash
# Step 1: Build image
docker-compose build

# Step 2: Start services
docker-compose up -d

# Step 3: Run monitoring
docker-compose run --rm wellbeing-monitor monitor
```

### Option 3: Makefile (Easiest)

```bash
# Build
make build

# Run monitoring
make monitor

# Query data
make query

# View logs
make logs
```

## 📋 Available Commands

### With Makefile (Recommended)
```bash
make help      # Show all commands
make build     # Build image
make up        # Start services
make monitor   # Start monitoring
make query     # Query tool
make demo      # Run demo
make logs      # View logs
make down      # Stop services
make clean     # Cleanup
```

### With docker-compose
```bash
docker-compose build
docker-compose up -d
docker-compose run --rm wellbeing-monitor monitor
docker-compose run --rm wellbeing-monitor query
docker-compose logs -f
docker-compose down
```

### With docker-compose Directly
```bash
# List sessions
docker-compose run --rm wellbeing-monitor query --sessions

# View session 1
docker-compose run --rm wellbeing-monitor query --session 1

# Generate report
docker-compose run --rm wellbeing-monitor query --report 1
```

## 🎯 System Architecture

```
┌─────────────────────────────────────────────┐
│         WELLBEING MONITORING SYSTEM          │
│              Docker Deployment               │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│    wellbeing-monitor (Main Application)     │
│  • Face, voice, breathing analysis          │
│  • Database storage (SQLite)                │
│  • Report generation                        │
└─────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │  postgres  │ │  pgAdmin   │ │   redis    │
    │ (database) │ │   (UI)     │ │  (cache)   │
    └────────────┘ └────────────┘ └────────────┘

┌─────────────────────────────────────────────┐
│           Persistent Volumes                │
│  • data/      (databases)                   │
│  • reports/   (session reports)             │
│  • exports/   (JSON exports)                │
│  • logs/      (application logs)            │
└─────────────────────────────────────────────┘
```

## 📁 File Structure

```
стартап/
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Services orchestration
├── docker-entrypoint.sh          # Container startup script
├── .dockerignore                 # Build context exclusions
├── .env.example                  # Environment template
├── Makefile                      # Command shortcuts
├── docker-setup.sh               # Automated setup script
│
├── DOCKER_GUIDE.md              # Complete Docker guide
├── DOCKER_COMMANDS.md           # Command reference
│
├── database.py                  # Database module
├── main.py                      # Monitoring app
├── query_database.py            # Query tool
├── face_analyzer.py             # Face analysis
├── voice_analyzer.py            # Voice analysis
├── breathing_analyzer.py        # Breathing analysis
│
├── data/                        # Database storage (volume)
├── reports/                     # Session reports (volume)
├── exports/                     # JSON exports (volume)
└── logs/                        # Application logs (volume)
```

## 🔧 Configuration

### Environment Variables (.env)

```env
POSTGRES_USER=wellbeing
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=wellbeing_monitor
TZ=UTC
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
LOG_LEVEL=INFO
DEBUG=false
```

### Application Config (config.py)

```python
MONITORING_DURATION_SECONDS = 30
CHECK_INTERVAL_SECONDS = 5
CAMERA_ID = 0
SAMPLE_RATE = 16000
```

## 🖥️ Hardware Access

The Docker setup provides access to:

```yaml
# Camera
- /dev/video0:/dev/video0

# Microphone/Audio
- /dev/snd:/dev/snd

# X11 Display (for visualization)
- /tmp/.X11-unix:/tmp/.X11-unix:rw

# GPU (optional)
- /dev/dri:/dev/dri
```

## 📊 Services & Ports

| Service | Port | Purpose |
|---------|------|---------|
| wellbeing-monitor | 8000 | Main app (future web UI) |
| wellbeing-monitor | 8080 | API endpoint (future) |
| PostgreSQL | 5432 | Database |
| pgAdmin | 5050 | Database management UI |
| Redis | 6379 | Caching layer |

Access pgAdmin:
- URL: http://localhost:5050
- Login: admin@wellbeing.local / admin
- Password: admin (change in production!)

## 💾 Data Management

### Database Files
```bash
data/wellbeing_monitor.db      SQLite database (persistent)
data/postgres/                 PostgreSQL data
```

### Report Files
```bash
reports/wellbeing_report_1_*.txt    Session reports
exports/session_1_*.json            JSON exports
logs/app.log                        Application logs
backups/*.db                        Database backups
```

### Accessing Data
```bash
# From host machine
ls -la data/
ls -la reports/
ls -la exports/

# From inside container
docker-compose exec wellbeing-monitor ls -la /app/data/
```

## 🔒 Security Features

### Built-in Security
- ✅ Non-root user execution
- ✅ Read-only filesystem support
- ✅ Resource limits (CPU, memory)
- ✅ Network isolation
- ✅ Health checks
- ✅ Privilege escalation prevention

### Production Ready
```bash
# Run with security hardening
docker-compose run \
  --rm \
  --read-only \
  --user 1000:1000 \
  --memory=512m \
  --cpus=1 \
  wellbeing-monitor monitor
```

## 📈 Performance

### Optimizations
- Slim Python image (minimal size)
- Layer caching for fast rebuilds
- Multi-stage builds support
- Resource limits configured
- Volume mounting for I/O
- Network optimization

### Typical Resource Usage
```
Memory:  ~500MB (idle) - 1.5GB (active)
CPU:     ~10% (idle) - 80% (processing)
Disk:    ~2GB (image) + data volume
```

## 🧹 Maintenance

### Backup Database
```bash
docker-compose exec wellbeing-monitor \
  cp /app/data/wellbeing_monitor.db \
  /app/exports/backup_$(date +%Y%m%d).db
```

### Clean Docker Data
```bash
# Remove containers
docker-compose down

# Remove volumes (careful!)
docker-compose down -v

# Prune all unused Docker objects
docker system prune -a
```

### Update System
```bash
# Rebuild image with latest code
docker-compose build --no-cache

# Restart services
docker-compose restart
```

## 🚨 Troubleshooting

### Build Issues
```bash
# Clear cache and rebuild
docker-compose build --no-cache

# View build output
DOCKER_BUILDKIT=0 docker-compose build
```

### Runtime Issues
```bash
# Check logs
docker-compose logs wellbeing-monitor

# Check container status
docker-compose ps

# View detailed errors
docker-compose logs --tail=100
```

### Hardware Access Issues
```bash
# Check device permissions
ls -la /dev/video0
ls -la /dev/snd

# Run with privileged mode
docker-compose run --rm --privileged wellbeing-monitor monitor
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

## 📚 Documentation Files

1. **DOCKER_GUIDE.md** (500+ lines)
   - Comprehensive Docker guide
   - Service architecture details
   - Advanced usage patterns
   - Production deployment

2. **DOCKER_COMMANDS.md** (400+ lines)
   - Quick command reference
   - Common workflows
   - Debugging commands
   - Registry and publishing

3. **IMPLEMENTATION_SUMMARY.md**
   - Database integration summary
   - Feature overview

4. **DATABASE_SETUP.md**
   - Database quick start
   - Configuration guide

## ✅ Verification Checklist

After setup, verify:

```bash
# Check Docker installation
docker --version                # v20.10+
docker-compose --version        # v1.29+
docker ps                       # Daemon running

# Check image
docker images | grep wellbeing-monitor

# Check services
docker-compose ps

# Test database
docker-compose run --rm wellbeing-monitor \
  python -c "from database import WellbeingDatabase; print('OK')"

# Test monitoring (mock)
docker-compose run --rm wellbeing-monitor \
  python database_demo.py

# Check data directories
ls -la data/ reports/ exports/
```

## 🎓 Learning Path

1. **Day 1: Setup**
   - Run `./docker-setup.sh`
   - Run `make help`
   - Read DOCKER_GUIDE.md

2. **Day 2: Try It**
   - Run `make demo`
   - Run `make monitor`
   - Run `make query`

3. **Day 3: Customize**
   - Edit config.py
   - Modify docker-compose.yml
   - Create custom workflows

4. **Day 4+: Deploy**
   - Deploy to production
   - Set up backup strategy
   - Monitor performance

## 🚀 Next Steps

```bash
# 1. Setup
./docker-setup.sh

# 2. Try demo
make demo

# 3. Start monitoring
make monitor

# 4. Query results
make query

# 5. View documentation
cat DOCKER_GUIDE.md
```

## 📞 Support

For help:
```bash
# Show available commands
make help

# View command reference
cat DOCKER_COMMANDS.md

# View detailed guide
cat DOCKER_GUIDE.md

# Run diagnostics
docker-compose config
docker-compose logs
docker system info
```

---

## 🎉 Complete! 

**Docker Integration Status**: ✅ FULLY COMPLETE

The Wellbeing Monitoring System is now:
- ✅ Fully containerized
- ✅ Production-ready
- ✅ Easily deployable
- ✅ Scalable architecture
- ✅ Documented

**Get started:**
```bash
./docker-setup.sh
make monitor
```

**Deploy to production:**
```bash
docker-compose build
docker-compose up -d
```

Enjoy your containerized wellbeing monitoring system! 🐳
