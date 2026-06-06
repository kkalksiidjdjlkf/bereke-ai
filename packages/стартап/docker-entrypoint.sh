#!/bin/bash
# Entrypoint script for Wellbeing Monitoring Docker container

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  WELLBEING MONITORING SYSTEM - DOCKER CONTAINER            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to wait for database
wait_for_db() {
    local db_path=$1
    local max_attempts=30
    local attempt=1
    
    echo "🔄 Waiting for database to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if sqlite3 "$db_path" "SELECT 1;" 2>/dev/null; then
            echo "✅ Database is ready"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts - Database not ready yet..."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo "⚠️  Database not ready, continuing anyway..."
    return 0
}

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p /app/reports
mkdir -p /app/data
mkdir -p /app/exports
mkdir -p /app/logs

# Set permissions
chmod 755 /app/reports
chmod 755 /app/data
chmod 755 /app/exports
chmod 755 /app/logs

echo "✅ Directories created"
echo ""

# Check for database initialization
if [ ! -f "/app/data/wellbeing_monitor.db" ]; then
    echo "💾 Initializing database..."
    python /app/database.py
    echo "✅ Database initialized"
else
    echo "✅ Database already exists"
fi

echo ""
echo "📊 System Status:"
echo "   • Python: $(python --version)"
echo "   • Working directory: $(pwd)"
echo "   • Database location: /app/data/wellbeing_monitor.db"
echo "   • Reports location: /app/reports/"
echo "   • Exports location: /app/exports/"
echo ""

# Handle different commands
case "$1" in
    "monitor")
        echo "🚀 Starting monitoring system..."
        echo ""
        exec python /app/main.py
        ;;
    "query")
        echo "🔍 Starting query tool..."
        echo ""
        exec python /app/query_database.py
        ;;
    "demo")
        echo "🧪 Running database demo..."
        echo ""
        exec python /app/database_demo.py
        ;;
    "shell")
        echo "🐚 Starting interactive shell..."
        echo ""
        /bin/bash
        ;;
    "app-shell")
        echo "🐚 Starting shell with monitoring system available..."
        echo ""
        /bin/bash -c 'python -i /app/query_database.py'
        ;;
    *)
        echo "📚 Available commands:"
        echo ""
        echo "  monitor       - Start real-time monitoring"
        echo "  query         - Launch interactive query tool"
        echo "  demo          - Run database demonstration"
        echo "  shell         - Start bash shell"
        echo "  app-shell     - Interactive Python shell with monitoring"
        echo ""
        echo "Usage: docker-compose run wellbeing-monitor <command>"
        echo ""
        echo "Examples:"
        echo "  docker-compose run wellbeing-monitor monitor"
        echo "  docker-compose run wellbeing-monitor query"
        echo "  docker-compose run wellbeing-monitor demo"
        echo "  docker-compose run wellbeing-monitor shell"
        echo ""
        echo "Or: docker-compose up -d    # Run in background"
        echo ""
        
        # If no command provided, show help
        exec python /app/query_database.py --help
        ;;
esac
