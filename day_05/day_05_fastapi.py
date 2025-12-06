#!/usr/bin/env python3
"""
Tag 5: FastAPI REST API
Agent als Web Service

Starten mit: python day_05_fastapi.py
Dann öffnen: http://localhost:8000/docs
"""

from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import uvicorn

app = FastAPI(title="AI Agent API", version="1.0")

# LM Studio client
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    agent_type: str = "planner"

class ChatResponse(BaseModel):
    agent: str
    response: str
    tokens_used: int

# In-memory conversation storage
conversations = {}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Chat with an AI agent"""

    # Get or create conversation history
    if request.agent_type not in conversations:
        conversations[request.agent_type] = []

    # Add user message
    conversations[request.agent_type].append({
        "role": "user",
        "content": request.message
    })

    # Generate response
    response = client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=[
            {"role": "system", "content": f"You are a {request.agent_type} agent."},
            *conversations[request.agent_type]
        ],
        max_tokens=150
    )

    agent_message = response.choices[0].message.content

    # Add to history
    conversations[request.agent_type].append({
        "role": "assistant",
        "content": agent_message
    })

    return ChatResponse(
        agent=request.agent_type,
        response=agent_message,
        tokens_used=response.usage.total_tokens
    )

@app.get("/history/{agent_type}")
def get_history(agent_type: str):
    """Get conversation history"""
    return {
        "agent": agent_type,
        "messages": conversations.get(agent_type, []),
        "count": len(conversations.get(agent_type, []))
    }

@app.get("/")
def root():
    return {
        "message": "AI Agent API",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /chat",
            "history": "GET /history/{agent_type}"
        }
    }

if __name__ == "__main__":
    print("="*60)
    print("TAG 5: FASTAPI REST API")
    print("="*60)
    print("\n🚀 Starting API server...")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🧪 Test: curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"message\": \"Hello\", \"agent_type\": \"planner\"}'")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000)
