"""
Day 18: Analytics REST API
FastAPI server for session analytics endpoints.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from day_18.session_analytics import SessionAnalytics
import uvicorn

app = FastAPI(
    title="Heist Session Analytics API",
    description="REST API for analyzing multi-agent heist sessions",
    version="1.0.0"
)

# Initialize analytics
analytics = SessionAnalytics()


@app.get("/")
async def root():
    """API root with available endpoints."""
    return {
        "service": "Heist Session Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "sessions": "/api/sessions - List all sessions",
            "session_details": "/api/sessions/{session_id} - Get session details",
            "tool_stats": "/api/tool-stats - Tool usage statistics",
            "agent_activity": "/api/agent-activity - Agent activity patterns",
            "compare": "/api/compare - Compare multiple sessions",
            "timeline": "/api/timeline/{session_id} - Session timeline",
            "metrics": "/api/metrics - Success metrics",
            "health": "/health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        sessions = analytics.list_sessions()
        return {
            "status": "healthy",
            "database": "connected",
            "total_sessions": len(sessions)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/api/sessions")
async def get_sessions():
    """Get list of all sessions."""
    try:
        sessions = analytics.list_sessions()
        return {
            "total": len(sessions),
            "sessions": sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed information about a specific session."""
    try:
        details = analytics.get_session_details(session_id)
        if "error" in details:
            raise HTTPException(status_code=404, detail=details["error"])
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tool-stats")
async def get_tool_statistics(session_id: Optional[str] = Query(None)):
    """
    Get tool usage statistics.

    Args:
        session_id: Optional session ID to filter stats for specific session
    """
    try:
        stats = analytics.get_tool_statistics(session_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-activity")
async def get_agent_activity(session_id: Optional[str] = Query(None)):
    """
    Get agent activity and interaction patterns.

    Args:
        session_id: Optional session ID to filter activity for specific session
    """
    try:
        activity = analytics.get_agent_activity(session_id)
        return activity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare")
async def compare_sessions(session_ids: List[str] = Query(...)):
    """
    Compare multiple sessions.

    Args:
        session_ids: List of session IDs to compare (query param can be repeated)

    Example:
        /api/compare?session_ids=heist_001&session_ids=heist_002
    """
    try:
        if len(session_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 session IDs required for comparison"
            )

        comparison = analytics.compare_sessions(session_ids)
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/timeline/{session_id}")
async def get_session_timeline(session_id: str):
    """Get chronological timeline of a session."""
    try:
        timeline = analytics.get_session_timeline(session_id)
        if not timeline:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "session_id": session_id,
            "event_count": len(timeline),
            "timeline": timeline
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
async def get_success_metrics():
    """Get overall success metrics across all sessions."""
    try:
        metrics = analytics.get_success_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the Analytics API server."""
    print("=" * 80)
    print("Starting Day 18: Analytics API Server")
    print("=" * 80)
    print("\n📊 Endpoints available:")
    print("   GET  http://localhost:8007/         - API Info")
    print("   GET  http://localhost:8007/health   - Health Check")
    print("   GET  http://localhost:8007/api/sessions")
    print("   GET  http://localhost:8007/api/sessions/{id}")
    print("   GET  http://localhost:8007/api/tool-stats")
    print("   GET  http://localhost:8007/api/agent-activity")
    print("   GET  http://localhost:8007/api/compare?session_ids=...")
    print("   GET  http://localhost:8007/api/timeline/{id}")
    print("   GET  http://localhost:8007/api/metrics")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8007)


if __name__ == "__main__":
    main()
