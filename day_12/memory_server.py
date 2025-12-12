#!/usr/bin/env python3
"""
Memory Server (MCP) - Tag 12 Implementation
Minimal MCP Server für Memory Management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from openai import OpenAI

# LM Studio Integration - wie in Tag 1, 6, 7
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
llm_client = OpenAI(
    base_url=LM_STUDIO_URL,
    api_key="lm-studio"
)

# Simulate simple in-memory storage for demo
memory_store = []

# MCP Server Implementation
app = FastAPI(
    title="Memory Server (MCP)",
    description="Agent memory management with MCP protocol",
    version="1.0.0"
)

# MCP Request/Response Models
class StoreMemoryRequest(BaseModel):
    agent_id: str
    turn_id: int
    message: str
    game_session_id: Optional[str] = None
    phase: Optional[str] = None

class StoreMemoryResponse(BaseModel):
    memory_id: int
    stored: bool

class GetRecentTurnsRequest(BaseModel):
    agent_id: str
    limit: int = 5
    game_session_id: Optional[str] = None

class GetRecentTurnsResponse(BaseModel):
    agent_id: str
    turns: List[Dict]
    turn_count: int

class GetCompressedMemoryRequest(BaseModel):
    agent_id: str
    game_session_id: Optional[str] = None
    max_tokens: int = 500
    recent_count: int = 2  # Anzahl der letzten Nachrichten, die vollständig bleiben

class GetCompressedMemoryResponse(BaseModel):
    agent_id: str
    summary: str  # Komprimierte ältere Nachrichten
    recent_messages: List[Dict]  # Letzte X Nachrichten vollständig
    token_count: int

# MCP Tool Endpoints
@app.post("/tools/store_memory", response_model=StoreMemoryResponse)
async def tool_store_memory(request: StoreMemoryRequest):
    """MCP Tool: Store memory turn"""
    memory_id = len(memory_store) + 1
    memory_store.append({
        "memory_id": memory_id,
        "agent_id": request.agent_id,
        "turn_id": request.turn_id,
        "message": request.message,
        "game_session_id": request.game_session_id,
        "phase": request.phase,
        "timestamp": datetime.now().isoformat()
    })
    return StoreMemoryResponse(memory_id=memory_id, stored=True)

@app.post("/tools/get_recent_turns", response_model=GetRecentTurnsResponse)
async def tool_get_recent_turns(request: GetRecentTurnsRequest):
    """MCP Tool: Get recent turns"""
    # Filter by agent and session
    filtered = [m for m in memory_store 
                if m["agent_id"] == request.agent_id
                and (not request.game_session_id or m["game_session_id"] == request.game_session_id)]
    
    # Get last N turns
    recent = filtered[-request.limit:] if filtered else []
    
    return GetRecentTurnsResponse(
        agent_id=request.agent_id,
        turns=recent,
        turn_count=len(recent)
    )

def compress_with_llm(messages: List[str], agent_id: str, max_tokens: int, phases: List[str]) -> str:
    """Echte LLM-basierte Memory Compression (LM Studio)"""
    try:
        # Formatiere Nachrichten für LLM
        message_text = "\n".join([f"- {msg}" for msg in messages])
        phase_text = ", ".join(phases) if phases else "unknown"
        
        # LLM Prompt für Memory Compression
        prompt = f"""Erstelle eine präzise Zusammenfassung der folgenden Agent-Nachrichten:

AGENT: {agent_id}
PHASE(N): {phase_text}
NACHRICHTEN ({len(messages)} total):
{message_text}

AUFGABE: Fasse die wichtigsten Punkte in MAXIMAL {max_tokens} Wörtern zusammen. 
- Fokus auf konkrete Aktionen und Entscheidungen
- Bewahre wichtige Details (Zahlen, Namen, Zeiten)
- Nutze präzise, sachliche Sprache
- Keine Einleitung oder Erklärung der Aufgabe

ZUSAMMENFASSUNG:"""

        response = llm_client.chat.completions.create(
            model="google/gemma-3n-e4b",
            messages=[
                {"role": "system", "content": "Du bist ein präziser Zusammenfassungsexperte. Erstelle kompakte, sachliche Summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens * 2,  # Etwas Puffer für bessere Qualität
            temperature=0.3  # Wenig Kreativität, mehr Präzision
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Falls LLM zu lang wird, kürzen
        words = summary.split()
        if len(words) > max_tokens:
            summary = " ".join(words[:max_tokens]) + "..."
            
        return summary
        
    except Exception as e:
        # Fallback zur simplen Methode wenn LLM nicht verfügbar
        print(f"⚠️  LLM compression failed, using fallback: {e}")
        return f"Agent {agent_id}: {len(messages)} messages in phases {', '.join(phases)}"

@app.post("/tools/get_compressed_memory", response_model=GetCompressedMemoryResponse)
async def tool_get_compressed_memory(request: GetCompressedMemoryRequest):
    """MCP Tool: Get hierarchical compressed memory - recent messages full, older compressed"""
    # Get all messages for this agent and session, sorted by turn_id
    filtered = sorted(
        [m for m in memory_store 
         if m["agent_id"] == request.agent_id
         and (not request.game_session_id or m["game_session_id"] == request.game_session_id)],
        key=lambda x: x["turn_id"]
    )
    
    if not filtered:
        return GetCompressedMemoryResponse(
            agent_id=request.agent_id,
            summary="No memory data found",
            recent_messages=[],
            token_count=0
        )
    
    # 📚 HIERARCHISCHE KOMPRESSION (wie Tag 11)
    if len(filtered) <= request.recent_count:
        # Wenig Nachrichten: Alles bleibt vollständig
        return GetCompressedMemoryResponse(
            agent_id=request.agent_id,
            summary="",  # Keine Kompression nötig
            recent_messages=filtered,
            token_count=sum(len(m["message"].split()) for m in filtered)
        )
    
    # Split: Alte Nachrichten komprimieren, neue vollständig behalten
    old_messages = filtered[:-request.recent_count]
    recent_messages = filtered[-request.recent_count:]
    
    # Komprimiere nur die alten Nachrichten
    old_texts = [m["message"] for m in old_messages]
    phases = list(set([m.get("phase", "unknown") for m in old_messages if m.get("phase")]))
    
    summary = compress_with_llm(old_texts, request.agent_id, request.max_tokens, phases)
    total_tokens = len(summary.split()) + sum(len(m["message"].split()) for m in recent_messages)
    
    return GetCompressedMemoryResponse(
        agent_id=request.agent_id,
        summary=summary,
        recent_messages=recent_messages,
        token_count=total_tokens
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "memory-server",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """MCP Tool Discovery - Service info"""
    return {
        "service": "Memory Server (MCP)",
        "version": "1.0.0",
        "tools": [
            "store_memory",
            "get_recent_turns", 
            "get_compressed_memory"
        ],
        "description": "Agent memory management with MCP protocol"
    }

# Standalone server runner
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Memory Server (MCP) on http://localhost:8000")
    print("📋 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)