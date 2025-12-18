#!/bin/bash

# Day 18: Start Analytics API Server (Standalone)

cd "$(dirname "$0")"  # Go to day_18 directory

echo "================================================================================"
echo "Starting Day 18: Analytics API Server"
echo "================================================================================"
echo ""

# Set database path (local to day_18)
export DATABASE_PATH="./heist_audit.db"

# Check if database exists
if [ ! -f "$DATABASE_PATH" ]; then
    echo "⚠️  Database not found at $DATABASE_PATH"
    echo "   Running init_database.py..."
    python3 init_database.py
fi

echo "📊 Endpoints available:"
echo "   GET  http://localhost:8007/         - API Info"
echo "   GET  http://localhost:8007/health   - Health Check"
echo "   GET  http://localhost:8007/api/sessions"
echo "   GET  http://localhost:8007/api/sessions/{id}"
echo "   GET  http://localhost:8007/api/tool-stats"
echo "   GET  http://localhost:8007/api/agent-activity"
echo "   GET  http://localhost:8007/api/compare?session_ids=..."
echo "   GET  http://localhost:8007/api/timeline/{id}"
echo "   GET  http://localhost:8007/api/metrics"
echo ""
echo "================================================================================"
echo ""

# Start server
python3 -c "
from session_analytics import SessionAnalytics
import analytics_api

# Override database path (local to day_18)
analytics_api.analytics = SessionAnalytics(db_path='./heist_audit.db')

# Start server
import uvicorn
uvicorn.run(analytics_api.app, host='0.0.0.0', port=8007)
"
