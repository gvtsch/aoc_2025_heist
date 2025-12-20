"""
Day 19: Dashboard Visualization
FastAPI backend for the Heist Analytics Dashboard.
Integrates with Day 18 Session Analytics API.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from typing import List
import sys
from pathlib import Path
import yaml
import os

# Import session analytics from local copy
from session_analytics import SessionAnalytics

import asyncio
from datetime import datetime


# Load configuration from CLI argument or default
import argparse

def load_config(config_file: str = None) -> dict:
    """Load configuration from YAML file."""
    if config_file is None:
        config_file = str(Path(__file__).parent / "config.yaml")

    config_path = Path(config_file)
    if not config_path.is_absolute():
        # Make relative paths relative to day_19 directory
        config_path = Path(__file__).parent / config_file

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Parse CLI arguments
parser = argparse.ArgumentParser(description='Heist Analytics Dashboard Server')
parser.add_argument('--config', '-c', type=str, default=None,
                    help='Path to config file (default: day_19/config.yaml)')
args, unknown = parser.parse_known_args()

# Load configuration
config = load_config(args.config)

# Initialize FastAPI with config
app = FastAPI(title=config['server']['title'])

# Initialize analytics with database path from config
db_path = config['database']['path']
if not os.path.isabs(db_path):
    # Make path absolute relative to day_19 directory
    db_path = str(Path(__file__).parent / db_path)

analytics = SessionAnalytics(db_path=db_path)


# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.get("/")
async def get_dashboard():
    """Serve the main dashboard HTML."""
    import os
    return FileResponse(os.path.join(os.path.dirname(__file__), "dashboard.html"))


@app.get("/api/sessions")
async def get_sessions():
    """Get all sessions with summary statistics."""
    sessions = analytics.list_sessions()

    return {
        "sessions": sessions,
        "total_sessions": len(sessions)
    }


@app.get("/api/session/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed information about a specific session."""
    details = analytics.get_session_details(session_id)
    return details


@app.get("/api/tool-stats")
async def get_tool_stats():
    """Get tool usage statistics across all sessions."""
    stats = analytics.get_tool_statistics()

    return {
        "tools": stats["tool_statistics"],
        "total_tools": len(stats["tool_statistics"])
    }


@app.get("/api/agent-activity/{session_id}")
async def get_agent_activity(session_id: str):
    """Get agent activity timeline for a session."""
    activity_data = analytics.get_agent_activity(session_id)

    if "error" in activity_data:
        return {"error": activity_data["error"]}

    return {
        "session_id": session_id,
        "activity": activity_data["agent_activity"],
        "interactions": activity_data["agent_interactions"]
    }


@app.get("/api/interaction-matrix/{session_id}")
async def get_interaction_matrix(session_id: str):
    """Get agent interaction matrix."""
    activity_data = analytics.get_agent_activity(session_id)
    return {
        "session_id": session_id,
        "interactions": activity_data["agent_interactions"]
    }


@app.get("/api/latest-session")
async def get_latest_session():
    """Get the most recent session."""
    sessions = analytics.list_sessions()

    if not sessions:
        return {"error": "No sessions found"}

    latest = sessions[0]  # Already sorted by start_time DESC

    return {
        "session_id": latest["session_id"],
        "start_time": latest["start_time"],
        "status": latest["status"],
        "total_turns": latest["total_turns"]
    }


@app.post("/api/session/{session_id}/mark-suspect")
async def mark_suspect(session_id: str, data: dict):
    """Mark an agent as suspected mole (for interactive game)."""
    agent_name = data.get("agent")

    # Store in a simple in-memory cache (in production: use Redis/DB)
    # For now, just broadcast to dashboard
    await manager.broadcast({
        "type": "suspect_marked",
        "session_id": session_id,
        "agent": agent_name,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "success": True,
        "message": f"Marked {agent_name} as suspect in {session_id}"
    }


@app.get("/api/stats/summary")
async def get_summary_stats():
    """Get overall system statistics."""
    metrics = analytics.get_success_metrics()

    return {
        "total_sessions": metrics["total_sessions"],
        "completed_sessions": metrics["completed_sessions"],
        "completion_rate": metrics["completion_rate"],
        "avg_turns_per_session": metrics["average_turns_per_session"],
        "tool_success_rates": metrics["tool_success_rates"]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Heist Command Center",
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back for now (in production: handle commands)
            await websocket.send_json({
                "type": "echo",
                "message": data,
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/search")
async def search_messages(keyword: str, session_id: str = None):
    """Search for messages containing keyword."""
    # Get session details and filter messages
    if session_id:
        details = analytics.get_session_details(session_id)
        if "error" in details:
            return {"error": details["error"]}
        messages = details["messages"]
    else:
        # Search across all sessions
        sessions = analytics.list_sessions()
        messages = []
        for session in sessions:
            details = analytics.get_session_details(session["session_id"])
            if "messages" in details:
                messages.extend(details["messages"])

    # Filter messages containing keyword
    results = [
        msg for msg in messages
        if keyword.lower() in msg["message"].lower()
    ]

    return {
        "keyword": keyword,
        "session_id": session_id,
        "results": results[:20],  # Limit to 20 results
        "total_found": len(results)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dashboard-server",
        "timestamp": datetime.now().isoformat()
    }


# Simulate real-time heist updates (for demo purposes)
async def simulate_heist_updates():
    """Simulate ongoing heist for demo purposes."""
    await asyncio.sleep(5)  # Wait 5 seconds after startup

    demo_messages = [
        {"agent": "planner", "message": "Team, we need to finalize the entry strategy."},
        {"agent": "hacker", "message": "Security cameras looped. We have 15 minutes."},
        {"agent": "safecracker", "message": "Vault mechanism analyzed. Need 45 minutes."},
        {"agent": "mole", "message": "Actually, the vault might take longer..."}
    ]

    for i, msg in enumerate(demo_messages):
        await asyncio.sleep(3)
        await manager.broadcast({
            "type": "agent_message",
            "turn": i + 1,
            "agent": msg["agent"],
            "message": msg["message"],
            "timestamp": datetime.now().isoformat()
        })


# Optional: Start simulation on server startup
# @app.on_event("startup")
# async def startup_event():
#     asyncio.create_task(simulate_heist_updates())


if __name__ == "__main__":
    import uvicorn

    host = config['server']['host']
    port = config['server']['port']
    reload = config['server']['reload']

    print("=" * 80)
    print(f"🎯 {config['server']['title']}")
    print("=" * 80)
    print(f"Starting server on http://{host}:{port}")
    print(f"Dashboard: http://localhost:{port}")
    print(f"API Docs: http://localhost:{port}/docs")
    print(f"Database: {db_path}")
    print("=" * 80)

    uvicorn.run(app, host=host, port=port, reload=reload)
