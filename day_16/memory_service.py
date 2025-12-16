#!/usr/bin/env python3
"""
Day 16: Memory Service
A simple in-memory service that stores and retrieves agent memories.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import uvicorn

app = FastAPI(title="Memory Service")

# In-memory storage: {agent_id: {session_id: [memories]}}
memory_store: Dict[str, Dict[str, List[Dict]]] = {}


class StoreMemoryRequest(BaseModel):
    agent_id: str
    turn_id: int
    message: str
    game_session_id: str


class GetCompressedMemoryRequest(BaseModel):
    agent_id: str
    game_session_id: str
    max_tokens: int = 100
    recent_count: int = 3


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "memory-service"}


@app.post("/tools/store_memory")
async def store_memory(request: StoreMemoryRequest):
    """Store a memory for an agent in a specific game session."""
    agent_id = request.agent_id
    session_id = request.game_session_id

    # Initialize storage structure if needed
    if agent_id not in memory_store:
        memory_store[agent_id] = {}

    if session_id not in memory_store[agent_id]:
        memory_store[agent_id][session_id] = []

    # Store the memory
    memory_entry = {
        "turn_id": request.turn_id,
        "message": request.message,
        "timestamp": datetime.now().isoformat()
    }

    memory_store[agent_id][session_id].append(memory_entry)

    return {
        "status": "success",
        "agent_id": agent_id,
        "session_id": session_id,
        "memories_count": len(memory_store[agent_id][session_id])
    }


@app.post("/tools/get_compressed_memory")
async def get_compressed_memory(request: GetCompressedMemoryRequest):
    """Get a compressed summary of recent memories."""
    agent_id = request.agent_id
    session_id = request.game_session_id
    recent_count = request.recent_count

    # Check if we have memories for this agent/session
    if agent_id not in memory_store:
        return {
            "status": "success",
            "summary": "No previous memories found.",
            "memories_count": 0
        }

    if session_id not in memory_store[agent_id]:
        return {
            "status": "success",
            "summary": "No previous memories found for this session.",
            "memories_count": 0
        }

    # Get recent memories
    memories = memory_store[agent_id][session_id]
    recent_memories = memories[-recent_count:] if len(memories) > recent_count else memories

    # Create a simple summary
    if not recent_memories:
        summary = "No recent memories."
    else:
        summary_parts = [
            f"Turn {mem['turn_id']}: {mem['message'][:100]}..."
            for mem in recent_memories
        ]
        summary = "\n".join(summary_parts)

    return {
        "status": "success",
        "summary": summary,
        "memories_count": len(memories),
        "recent_count": len(recent_memories)
    }


@app.get("/stats")
async def get_stats():
    """Get statistics about stored memories."""
    total_agents = len(memory_store)
    total_sessions = sum(len(sessions) for sessions in memory_store.values())
    total_memories = sum(
        len(memories)
        for agent_sessions in memory_store.values()
        for memories in agent_sessions.values()
    )

    return {
        "total_agents": total_agents,
        "total_sessions": total_sessions,
        "total_memories": total_memories,
        "agents": list(memory_store.keys())
    }


@app.delete("/clear")
async def clear_memories():
    """Clear all stored memories (for testing)."""
    global memory_store
    memory_store = {}
    return {"status": "success", "message": "All memories cleared"}


if __name__ == "__main__":
    print("🧠 Starting Memory Service on port 8005...")
    print("📊 Endpoints:")
    print("   POST /tools/store_memory - Store agent memory")
    print("   POST /tools/get_compressed_memory - Get memory summary")
    print("   GET  /health - Health check")
    print("   GET  /stats - Memory statistics")
    print("   DELETE /clear - Clear all memories")

    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info")
