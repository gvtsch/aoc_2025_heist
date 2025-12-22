"""
Day 20: Interactive Dashboard Server
Erweitert Tag 19's Dashboard um interaktive Steuerung.
Ermöglicht Heist Control, Agent Commands, Live Interaction.
Standalone version mit lokaler session_analytics.py Kopie.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path
import yaml
import os
import asyncio
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import local modules with proper paths
from day_20.session_analytics import SessionAnalytics
from day_20.heist_controller import HeistController, get_controller


# Load configuration from CLI argument or default
import argparse

def load_config(config_file: str = None) -> dict:
    """Load configuration from YAML file."""
    if config_file is None:
        config_file = str(Path(__file__).parent / "config.yaml")

    config_path = Path(config_file)
    if not config_path.is_absolute():
        # Make relative paths relative to day_20 directory
        config_path = Path(__file__).parent / config_file

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Parse CLI arguments
parser = argparse.ArgumentParser(description='Interactive Heist Command Center Server')
parser.add_argument('--config', '-c', type=str, default=None,
                    help='Path to config file (default: day_20/config.yaml)')
args, unknown = parser.parse_known_args()

# Load configuration
config = load_config(args.config)

# Initialize FastAPI with config
app = FastAPI(title=config['server']['title'])

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database path from config
db_path = config['database']['path']
if not os.path.isabs(db_path):
    # Make path absolute relative to day_20 directory
    db_path = str(Path(__file__).parent / db_path)

# Initialize services
analytics = SessionAnalytics(db_path=db_path)
controller = get_controller()


# Request models
class SessionStartRequest(BaseModel):
    session_id: str
    agents: List[str]
    config: Optional[dict] = {}


class CommandRequest(BaseModel):
    agent: str
    command: str


class MoleDetectionRequest(BaseModel):
    agent: str


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send to specific client."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass


manager = ConnectionManager()


# ============================================================================
# Static Files
# ============================================================================

@app.get("/")
async def get_dashboard():
    """Serve the interactive dashboard HTML."""
    html_path = os.path.join(os.path.dirname(__file__), "interactive_dashboard.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Dashboard HTML not found")
    return FileResponse(html_path)


# ============================================================================
# Analytics Endpoints (von Tag 19)
# ============================================================================

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


# ============================================================================
# Heist Control Endpoints (NEU in Tag 20)
# ============================================================================

@app.post("/api/heist/start")
async def start_heist(request: SessionStartRequest):
    """Starte einen neuen Heist."""
    result = controller.start_session(
        session_id=request.session_id,
        agents=request.agents,
        config=request.config
    )

    # Broadcast to all clients
    await manager.broadcast({
        "type": "heist_started",
        "session_id": request.session_id,
        "agents": request.agents,
        "timestamp": datetime.now().isoformat()
    })

    return result


@app.post("/api/heist/{session_id}/pause")
async def pause_heist(session_id: str):
    """Pausiere einen laufenden Heist."""
    result = controller.pause_session(session_id)

    if result["success"]:
        await manager.broadcast({
            "type": "heist_paused",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

    return result


@app.post("/api/heist/{session_id}/resume")
async def resume_heist(session_id: str):
    """Setze einen pausierten Heist fort."""
    result = controller.resume_session(session_id)

    if result["success"]:
        await manager.broadcast({
            "type": "heist_resumed",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

    return result


@app.post("/api/heist/{session_id}/command")
async def send_agent_command(session_id: str, request: CommandRequest):
    """Sende ein Command an einen Agent."""
    result = controller.send_command(
        session_id=session_id,
        agent=request.agent,
        command=request.command
    )

    if result["success"]:
        await manager.broadcast({
            "type": "command_sent",
            "session_id": session_id,
            "agent": request.agent,
            "command": request.command,
            "timestamp": datetime.now().isoformat()
        })

    return result


@app.get("/api/heist/{session_id}/commands")
async def get_pending_commands(session_id: str, agent: Optional[str] = None):
    """Hole ausstehende Commands."""
    commands = controller.get_pending_commands(session_id, agent)
    return {
        "session_id": session_id,
        "agent": agent,
        "commands": commands,
        "count": len(commands)
    }


@app.get("/api/heist/{session_id}/status")
async def get_heist_status(session_id: str):
    """Hole den aktuellen Heist-Status."""
    status = controller.get_session_status(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status


@app.get("/api/heist/active")
async def get_active_heists():
    """Hole alle aktiven Heists."""
    active = controller.get_all_active_sessions()
    return {
        "active_sessions": active,
        "count": len(active)
    }


@app.post("/api/heist/{session_id}/detect-mole")
async def detect_mole(session_id: str, request: MoleDetectionRequest):
    """Markiere einen Agent als erkannten Mole."""
    result = controller.set_detected_mole(session_id, request.agent)

    if result["success"]:
        await manager.broadcast({
            "type": "mole_detected",
            "session_id": session_id,
            "agent": request.agent,
            "timestamp": datetime.now().isoformat()
        })

    return result


@app.get("/api/heist/{session_id}/mole-status")
async def get_mole_status(session_id: str):
    """Hole Mole-Status (für Tag 21 Game)."""
    return controller.get_mole_status(session_id)


@app.post("/api/heist/{session_id}/evaluate-detection")
async def evaluate_detection(session_id: str):
    """
    Evaluiere die Mole-Detection und bestimme das Game Outcome.
    Gibt SUCCESS, FAILURE oder BUSTED zurück.
    """
    result = controller.evaluate_detection(session_id)
    
    if result.get("success"):
        await manager.broadcast({
            "type": "game_evaluated",
            "session_id": session_id,
            "outcome": result["outcome"],
            "message": result["message"],
            "timestamp": datetime.now().isoformat()
        })
    
    return result


@app.post("/api/heist/{session_id}/reveal-mole")
async def reveal_mole(session_id: str):
    """Decke den echten Mole auf (End Game)."""
    status = controller.get_mole_status(session_id)
    
    if not status.get("actual_mole"):
        raise HTTPException(status_code=404, detail="No mole in this session")
    
    await manager.broadcast({
        "type": "mole_revealed",
        "session_id": session_id,
        "actual_mole": status["actual_mole"],
        "detected_mole": status["detected_mole"],
        "is_correct": status["is_correct"],
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "success": True,
        "actual_mole": status["actual_mole"],
        "detected_mole": status["detected_mole"],
        "is_correct": status["is_correct"],
        "message": f"The mole was: {status['actual_mole']}"
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket für Real-time Updates."""
    await manager.connect(websocket)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Interactive Heist Command Center",
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()

            # Parse and handle different message types
            try:
                message = eval(data) if isinstance(data, str) and data.startswith("{") else {"raw": data}

                # Echo for now
                await manager.send_personal({
                    "type": "echo",
                    "message": data,
                    "timestamp": datetime.now().isoformat()
                }, websocket)

            except Exception as e:
                await manager.send_personal({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "interactive-dashboard-server",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections),
        "active_heists": len(controller.get_all_active_sessions())
    }


# ============================================================================
# Startup
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    host = config['server']['host']
    port = config['server']['port']
    reload = config['server']['reload']

    print("=" * 80)
    print(f"🎮 {config['server']['title']}")
    print("=" * 80)
    print(f"Starting server on http://{host}:{port}")
    print(f"Dashboard: http://localhost:{port}")
    print(f"API Docs: http://localhost:{port}/docs")
    print(f"Database: {db_path}")
    print("")
    print("🎯 Interactive Features:")
    print("  • ⏸️  Heist Pause/Resume Control")
    print("  • 📡 Send Commands to Agents")
    print("  • 🏦 Interactive Bank Layout")
    print("  • 🕵️  Mole Detection Game")
    print("  • 📋 Real-time Activity Log")
    print("  • 🔄 Live Status Updates")
    print("=" * 80)

    uvicorn.run(app, host=host, port=port, reload=reload)
