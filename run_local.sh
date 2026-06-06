#!/usr/bin/env bash
set -euo pipefail

# run_local.sh — starts backend on port 5000 and serves the frontend via /site
# Usage: ./run_local.sh

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Stopping previous backend processes on ports 5000/5001/8888 if any..."
# kill processes using ports if possible
lsof -ti:5000 2>/dev/null | xargs -r kill -9 || true
lsof -ti:5001 2>/dev/null | xargs -r kill -9 || true
lsof -ti:8888 2>/dev/null | xargs -r kill -9 || true

echo "Installing Python dependencies (only if missing)..."
if [ -f requirements_app.txt ]; then
  python3 -m pip install -r requirements_app.txt || python3 -m pip install flask flask-cors flask-sqlalchemy
else
  python3 -m pip install flask flask-cors flask-sqlalchemy
fi

echo "Starting backend (serves API + /site) on http://localhost:5000 ..."
# Start backend on port 5000 in background
python3 - <<PY &
from app_backend import app
app.run(host='0.0.0.0', port=5000, debug=False)
PY

sleep 1

echo
echo "Frontend (site) available at: http://localhost:5000/site"
echo "API base available at: http://localhost:5000/api"

echo "If you want a separate static server for development, run: python3 -m http.server 8888"

