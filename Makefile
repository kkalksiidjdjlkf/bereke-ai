# Makefile for Wellbeing Monitoring System Docker

.PHONY: help build up down logs shell monitor demo query restart clean

# Default target
help:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║       WELLBEING MONITORING SYSTEM - DOCKER MAKEFILE        ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 QUICK START:"
	@echo "  make build                 Build Docker image"
	@echo "  make up                    Start services in background"
	@echo "  make monitor               Start real-time monitoring"
	@echo "  make query                 Launch query tool"
	@echo "  make demo                  Run demo with sample data"
	@echo ""
	@echo "🔧 MANAGEMENT:"
	@echo "  make logs                  View service logs"
	@echo "  make shell                 Get bash shell in container"
	@echo "  make stop                  Stop all services"
	@echo "  make down                  Stop and remove containers"
	@echo "  make restart               Restart all services"
	@echo "  make clean                 Clean up Docker artifacts"
	@echo ""
	@echo "📊 ADVANCED:"
	@echo "  make stats                 View container statistics"
	@echo "  make ps                    List running containers"
	@echo "  make health                Check container health"
	@echo "  make test                  Run all tests"
	@echo ""
	@echo "📚 For more commands, see: DOCKER_COMMANDS.md"
	@echo ""

# Build Docker image
build:
	@echo "🏗️  Building Docker image..."
	docker-compose build
	@echo "✅ Build complete!"

# Build without cache
build-fresh:
	@echo "🏗️  Building Docker image (fresh)..."
	docker-compose build --no-cache
	@echo "✅ Build complete!"

# Start services in background
up:
	@echo "🚀 Starting services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo ""
	@echo "📊 View logs with: make logs"
	@echo "🛑 Stop with: make down"

# Start monitoring
monitor:
	@echo "📹 Starting real-time monitoring..."
	docker-compose run --rm wellbeing-monitor monitor

# Launch query tool
query:
	@echo "🔍 Launching query tool..."
	docker-compose run --rm wellbeing-monitor query

# Run demo
demo:
	@echo "🧪 Running demo with sample data..."
	docker-compose run --rm wellbeing-monitor demo

# Interactive shell
shell:
	@echo "🐚 Starting bash shell..."
	docker-compose run --rm wellbeing-monitor shell

# Python shell
python:
	@echo "🐍 Starting Python shell..."
	docker-compose run --rm wellbeing-monitor app-shell

# View logs
logs:
	docker-compose logs -f wellbeing-monitor

# View service status
ps:
	docker-compose ps

# Container health check
health:
	@echo "💚 Checking container health..."
	docker-compose exec wellbeing-monitor healthcheck || echo "⚠️  Health check failed"

# Container statistics
stats:
	docker stats wellbeing-monitor

# Stop services
stop:
	@echo "🛑 Stopping services..."
	docker-compose stop
	@echo "✅ Services stopped!"

# Stop and remove containers
down:
	@echo "🗑️  Removing containers..."
	docker-compose down
	@echo "✅ Containers removed!"

# Full cleanup (including volumes)
clean-all:
	@echo "🧹 Full cleanup (removing volumes)..."
	docker-compose down -v
	@echo "✅ Full cleanup complete!"

# Restart services
restart:
	@echo "🔄 Restarting services..."
	docker-compose restart
	@echo "✅ Services restarted!"

# Basic cleanup
clean:
	@echo "🧹 Cleaning up..."
	docker system prune -f
	@echo "✅ Cleanup complete!"

# Install and build everything
install: build
	@echo "📦 Installation complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  make up        - Start services"
	@echo "  make monitor   - Start monitoring"
	@echo "  make query     - View saved data"

# Run all tests
test:
	@echo "🧪 Running tests..."
	docker-compose run --rm wellbeing-monitor python -m pytest tests/
	@echo "✅ Tests complete!"

# Setup environment
setup:
	@echo "⚙️  Setting up environment..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp .env.example .env; \
		echo "📝 Edit .env with your settings"; \
	fi
	@echo "✅ Setup complete!"

# List all available targets
targets:
	@grep "^[a-z-]*:" Makefile | cut -d: -f1 | sed 's/^/  /'

# Development: Build, start services, show logs
dev: build up logs

# Production: Build with no cache, start, show health
prod: build-fresh up health

# Status: Show all services status
status:
	@echo "📊 Status Report:"
	@echo ""
	@echo "Containers:"
	@docker-compose ps
	@echo ""
	@echo "Disk Usage:"
	@docker system df | head -5
	@echo ""
	@echo "Recent Logs:"
	@docker-compose logs --tail=5 wellbeing-monitor | tail -6

# Version info
version:
	@echo "Versions:"
	@echo "  Docker:"
	@docker --version
	@echo "  Docker Compose:"
	@docker-compose --version
	@echo "  Python (in container):"
	@docker-compose run --rm wellbeing-monitor python --version

# View available data
data:
	@echo "📁 Available Data:"
	@echo ""
	@echo "Database:"
	@ls -lh data/wellbeing_monitor.db 2>/dev/null || echo "  No database found"
	@echo ""
	@echo "Reports:"
	@ls -lh reports/ 2>/dev/null | tail -5 || echo "  No reports found"
	@echo ""
	@echo "Exports:"
	@ls -lh exports/ 2>/dev/null | tail -5 || echo "  No exports found"

# Backup data
backup:
	@echo "💾 Backing up data..."
	@mkdir -p backups
	@cp data/wellbeing_monitor.db backups/wellbeing_monitor_$(shell date +%Y%m%d_%H%M%S).db
	@echo "✅ Backup created!"

# Format code
format:
	@echo "📐 Formatting code..."
	docker-compose run --rm wellbeing-monitor python -m black *.py
	@echo "✅ Code formatted!"

# Lint code
lint:
	@echo "🔍 Linting code..."
	docker-compose run --rm wellbeing-monitor python -m flake8 *.py
	@echo "✅ Linting complete!"

# View all database sessions
sessions:
	docker-compose run --rm wellbeing-monitor python query_database.py --sessions

# View specific session
session-%:
	docker-compose run --rm wellbeing-monitor python query_database.py --session $*

# Generate report
report-%:
	docker-compose run --rm wellbeing-monitor python query_database.py --report $*

# Export session
export-%:
	docker-compose run --rm wellbeing-monitor python query_database.py --export $*

# Compare sessions
compare-%:
	docker-compose run --rm wellbeing-monitor python query_database.py --compare $*

.SILENT: help targets status data
