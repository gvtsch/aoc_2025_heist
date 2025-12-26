#!/usr/bin/env python3
"""
Day 22: AI-Powered Detection Dashboard Server (Docker Version)
Extends Day 20's Interactive Dashboard with AI-powered Mole Detection.
Built on Day 20's HeistController and IntegratedAgentWithController.

Docker Version Changes:
- Fixed duplicate message storage bug (only dashboard stores, not both agent and dashboard)
- Fixed session completion tracking (marks sessions as 'completed' when done)
- Uses Docker service names for configuration
"""

import sys
from pathlib import Path
import os

# Environment variables for Docker
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/heist_analytics.db")
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://host.docker.internal:1234/v1")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import infrastructure
from day_20.heist_controller import get_controller
from day_20.session_analytics import SessionAnalytics
from day_20.integrated_agent_with_controller import IntegratedAgentWithController
from day_16.integrated_system import ConfigLoader, DatabaseManager, OAuthClient, ToolClient, MemoryServiceClient
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from openai import OpenAI
import asyncio
import sqlite3
import logging

# Import detection components
from day_22.sabotage_detector_docker import SabotageDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket Manager
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
            except:
                pass

# Initialize components
app = FastAPI(title="AI-Powered Mole Detection Command Center")
controller = get_controller()
analytics = SessionAnalytics(db_path=DATABASE_PATH)
detector = SabotageDetector(db_path=DATABASE_PATH, lm_studio_url=LM_STUDIO_URL)
manager = ConnectionManager()

# Track running agent sessions
running_sessions: Dict[str, bool] = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve dashboard
@app.get("/")
async def get_dashboard():
    """Serve the AI Detection Dashboard HTML."""
    html_path = os.path.join(os.path.dirname(__file__), "detection_dashboard_docker.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Detection Dashboard HTML not found")
    return FileResponse(html_path)

# Pydantic models
class SessionStartRequest(BaseModel):
    session_id: str
    agents: List[str]
    config: Dict = {}

class CommandRequest(BaseModel):
    agent: str
    command: str

class MoleDetectionRequest(BaseModel):
    agent: str

# Analytics endpoints
@app.get("/api/agents")
async def get_available_agents():
    """Get all available agents from config."""
    try:
        config_path = os.path.join(project_root, "day_20", "agents_config.docker.yaml")
        if not os.path.exists(config_path):
            return {"agents": [], "error": "Config not found"}

        config = ConfigLoader.load_config(config_path)
        agent_names = [agent.name for agent in config.agents]

        return {
            "agents": agent_names,
            "count": len(agent_names)
        }
    except Exception as e:
        return {"agents": [], "error": str(e)}

@app.get("/api/sessions")
async def get_sessions():
    """Get all sessions"""
    sessions = analytics.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}

@app.get("/api/session/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed session information."""
    details = analytics.get_session_details(session_id)
    if "error" in details:
        raise HTTPException(status_code=404, detail=details["error"])
    return details

@app.get("/api/tool-stats")
async def get_tool_stats():
    """Get aggregated tool usage statistics."""
    return analytics.get_tool_statistics()

@app.get("/api/agent-activity/{session_id}")
async def get_agent_activity(session_id: str):
    """Get agent activity for a specific session."""
    activity = analytics.get_agent_activity(session_id)
    if "error" in activity:
        raise HTTPException(status_code=404, detail=activity["error"])
    return activity

@app.get("/api/stats/summary")
async def get_summary_stats():
    """Get summary statistics."""
    return analytics.get_summary_stats()

# Agent runner function (FIXED: No duplicate message storage + Session completion)
async def run_agents_loop(session_id: str, agent_names: List[str], num_turns: int = 10):
    """Run agents in a loop for the specified session."""
    try:
        # Load configuration
        config_path = os.path.join(project_root, "day_20", "agents_config.docker.yaml")
        if not os.path.exists(config_path):
            logger.error(f"Config not found: {config_path}")
            return

        config = ConfigLoader.load_config(config_path)

        # Initialize services
        db_manager = DatabaseManager(DATABASE_PATH)

        # Create session in DB
        db_manager.create_session(session_id)

        # LLM Client
        llm_client = OpenAI(
            base_url=config.llm['base_url'],
            api_key=config.llm['api_key']
        )

        # Other clients
        oauth_client = OAuthClient(config.oauth_service)
        tool_client = ToolClient(config.tool_services)
        memory_client = MemoryServiceClient(config.memory_service)

        # Create agents
        agents = []
        for agent_config in config.agents:
            if agent_config.name in agent_names:
                agent = IntegratedAgentWithController(
                    config=agent_config,
                    llm_client=llm_client,
                    llm_config=config.llm,
                    oauth_client=oauth_client,
                    tool_client=tool_client,
                    memory_client=memory_client,
                    db_manager=db_manager,
                    session_id=session_id
                )
                agents.append(agent)

        if not agents:
            logger.error(f"No agents created for session {session_id}")
            return

        logger.info(f"Starting {len(agents)} agents for session {session_id}")

        # Run heist loop
        conversation_context = []
        running_sessions[session_id] = True

        for turn in range(1, num_turns + 1):
            if not running_sessions.get(session_id, False):
                logger.info(f"Session {session_id} stopped")
                break

            # Check if session is paused and wait
            while controller.is_paused(session_id):
                if not running_sessions.get(session_id, False):
                    logger.info(f"Session {session_id} stopped while paused")
                    break
                await asyncio.sleep(1)

            if not running_sessions.get(session_id, False):
                break

            for agent in agents:
                # Check if stopped before each agent
                if not running_sessions.get(session_id, False):
                    logger.info(f"Session {session_id} stopped during turn")
                    break

                try:
                    response = agent.respond(conversation_context, turn)

                    if "[PAUSED]" not in response:
                        conversation_context.append({
                            "agent": agent.config.name,
                            "message": response
                        })

                        # FIX: Only store message once (not in agent.respond() AND here)
                        # The agent's respond() method already stores it, so we DON'T store it again
                        # This was causing duplicate message counts

                        # Broadcast to websocket
                        await manager.broadcast({
                            "type": "agent_message",
                            "session_id": session_id,
                            "agent": agent.config.name,
                            "message": response,
                            "turn": turn,
                            "timestamp": datetime.now().isoformat()
                        })

                    # Small delay between agents
                    for _ in range(5):
                        if not running_sessions.get(session_id, False):
                            break
                        await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Agent {agent.config.name} error: {e}")

            # Delay between turns
            for _ in range(10):
                if not running_sessions.get(session_id, False):
                    break
                await asyncio.sleep(0.1)

        # FIX: Mark session as completed when done
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.execute(
                "UPDATE heist_sessions SET status = 'completed', completed_at = ? WHERE session_id = ?",
                (datetime.now().isoformat(), session_id)
            )
            conn.commit()
            conn.close()
            logger.info(f"Session {session_id} marked as completed")
        except Exception as e:
            logger.error(f"Failed to mark session as completed: {e}")

        logger.info(f"Session {session_id} completed {num_turns} turns")
        running_sessions[session_id] = False

    except Exception as e:
        logger.error(f"Agent loop failed: {e}")
        running_sessions[session_id] = False

# Heist Control endpoints
@app.post("/api/heist/start")
async def start_heist(request: SessionStartRequest, background_tasks: BackgroundTasks):
    """Start a new heist session with mole game and run agents."""
    result = controller.start_session(
        session_id=request.session_id,
        agents=request.agents,
        config=request.config
    )

    await manager.broadcast({
        "type": "heist_started",
        "session_id": request.session_id,
        "agents": request.agents,
        "timestamp": datetime.now().isoformat()
    })

    # Start agents in background
    background_tasks.add_task(run_agents_loop, request.session_id, request.agents, 10)

    return result

@app.post("/api/heist/{session_id}/pause")
async def pause_heist(session_id: str):
    """Pause a running heist."""
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
    """Resume a paused heist."""
    result = controller.resume_session(session_id)

    if result["success"]:
        await manager.broadcast({
            "type": "heist_resumed",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

    return result

@app.post("/api/heist/{session_id}/stop")
async def stop_heist(session_id: str):
    """Stop a running heist."""
    running_sessions[session_id] = False
    logger.info(f"Session {session_id} stop requested")

    await manager.broadcast({
        "type": "heist_stopped",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "success": True,
        "message": f"Heist {session_id} stopped"
    }

@app.post("/api/heist/{session_id}/command")
async def send_agent_command(session_id: str, request: CommandRequest):
    """Send a command to a specific agent."""
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
    """Get pending commands for a session or agent."""
    commands = controller.get_pending_commands(session_id, agent)
    return {
        "session_id": session_id,
        "agent": agent,
        "commands": commands,
        "count": len(commands)
    }

@app.get("/api/heist/{session_id}/status")
async def get_heist_status(session_id: str):
    """Get current heist status."""
    status = controller.get_session_status(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status

@app.get("/api/heist/active")
async def get_active_heists():
    """Get all active heist sessions."""
    active = controller.get_all_active_sessions()
    return {
        "active_sessions": active,
        "count": len(active)
    }

# Mole Detection endpoints
@app.post("/api/heist/{session_id}/detect-mole")
async def detect_mole(session_id: str, request: MoleDetectionRequest):
    """User submits their mole detection."""
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
    """Get mole detection status."""
    return controller.get_mole_status(session_id)

@app.post("/api/heist/{session_id}/evaluate-detection")
async def evaluate_detection(session_id: str):
    """Evaluate the mole detection."""
    result = controller.evaluate_detection(session_id)

    if result["success"]:
        await manager.broadcast({
            "type": "detection_evaluated",
            "session_id": session_id,
            "outcome": result["outcome"],
            "timestamp": datetime.now().isoformat()
        })

    return result

@app.post("/api/heist/{session_id}/reveal-mole")
async def reveal_mole(session_id: str):
    """Reveal the actual mole for the session."""
    session = controller.active_sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    actual_mole = session.get("mole")
    sabotage_pattern = session.get("sabotage_pattern")

    if not actual_mole:
        raise HTTPException(status_code=400, detail="No mole in this session")

    message = f"The actual mole was: {actual_mole}"
    if sabotage_pattern:
        message += f" (using {sabotage_pattern} strategy)"

    return {
        "success": True,
        "message": message,
        "mole": actual_mole,
        "sabotage_pattern": sabotage_pattern
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-detection-dashboard",
        "timestamp": datetime.now().isoformat()
    }

# AI-Powered Detection Endpoints
class DetectionRequest(BaseModel):
    session_id: str
    agents: Optional[List[str]] = None

@app.post("/api/ai-detect/analyze")
async def ai_analyze_session(request: DetectionRequest):
    """AI-powered analysis: Calculate suspicion scores for all agents."""
    session_id = request.session_id

    # Get session data from analytics
    details = analytics.get_session_details(session_id)

    if "error" in details:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Get session ID from DB
    conn = sqlite3.connect(DATABASE_PATH)
    session_row = conn.execute(
        "SELECT id FROM heist_sessions WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    conn.close()

    if not session_row:
        raise HTTPException(status_code=404, detail=f"Session not found in DB: {session_id}")

    db_session_id = session_row[0]

    # Run AI detection
    analysis = await detector.detect_mole(db_session_id)

    return analysis

@app.post("/api/ai-detect/suggest")
async def ai_suggest_mole(request: DetectionRequest):
    """Quick AI suggestion: Only the mole suggestion without full analysis."""
    analysis = await ai_analyze_session(request)

    return {
        "session_id": analysis["session_id"],
        "suggested_mole": analysis.get("most_suspicious", "unknown"),
        "confidence": analysis.get("confidence", 0.0),
        "suspicion_scores": analysis.get("agent_scores", {})
    }

@app.get("/api/ai-detect/session/{session_id}")
async def get_ai_detection_for_session(session_id: str):
    """Convenience endpoint: AI-Detection for a session (agents auto-extracted)."""
    request = DetectionRequest(session_id=session_id)
    return await ai_analyze_session(request)

@app.get("/api/detection-info")
async def get_detection_info():
    """Get information about the AI Detection system."""
    return {
        "name": "AI-Powered Mole Detection",
        "description": "RAG-powered mole detection using pattern analysis",
        "features": [
            "Perfect Tool Usage Detection (suspicious when >95%)",
            "Message Content Analysis via LLM",
            "Timing Pattern Recognition",
            "Combined Suspicion Scores (0.0-1.0)"
        ],
        "based_on": "Day 21 Mole Detection Game"
    }

if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("🤖 Day 22: AI-Powered Mole Detection Dashboard (Docker Version)")
    print("=" * 80)
    print()
    print("Server starting on http://localhost:8008")
    print("Dashboard: http://localhost:8008")
    print("API Docs: http://localhost:8008/docs")
    print()
    print("🤖 AI Detection Features (RAG-powered):")
    print("  • 🔍 Tool Usage Pattern Analysis (Inverted Logic)")
    print("  • 💬 Message Content Analysis via LLM")
    print("  • 🎯 Combined Suspicion Scores (0.0-1.0)")
    print()
    print("🐛 Bug Fixes:")
    print("  • ✅ Fixed duplicate message storage")
    print("  • ✅ Fixed session completion tracking")
    print()
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8008, reload=False)
