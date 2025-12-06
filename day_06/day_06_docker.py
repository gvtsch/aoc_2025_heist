#!/usr/bin/env python3
"""
Tag 6: Docker Container
Agent läuft im Docker Container

Dieser Code zeigt die Python-Seite.
Siehe auch: Dockerfile und docker-compose.yml im Projekt-Root

Ein Befehl: docker-compose up → Agent läuft
"""

from openai import OpenAI
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="Dockerized Agent", version="1.0")

# LM Studio läuft auf Host-Maschine
# Docker Container kann via host.docker.internal darauf zugreifen
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://host.docker.internal:1234/v1")

client = OpenAI(
    base_url=LM_STUDIO_URL,
    api_key="not-needed"
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    container_id: str

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dockerized-agent",
        "lm_studio_url": LM_STUDIO_URL
    }

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Chat endpoint - läuft im Container"""

    response = client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=[
            {"role": "system", "content": "You are a helpful AI agent running in a Docker container."},
            {"role": "user", "content": request.message}
        ],
        max_tokens=100
    )

    # Container ID aus Umgebungsvariable (wird von Docker gesetzt)
    container_id = os.getenv("HOSTNAME", "local")

    return ChatResponse(
        response=response.choices[0].message.content,
        container_id=container_id
    )

if __name__ == "__main__":
    print("="*60)
    print("TAG 6: DOCKER CONTAINER")
    print("="*60)
    print("\n🐳 Agent läuft im Docker Container")
    print(f"📡 LM Studio URL: {LM_STUDIO_URL}")
    print("🏥 Health Check: http://localhost:8000/health")
    print("💬 Chat Endpoint: http://localhost:8000/chat")
    print("\n" + "="*60)
    print("WARUM DOCKER?")
    print("="*60)
    print("✅ Gleiche Environment überall (Dev = Prod)")
    print("✅ Isolation zwischen Services")
    print("✅ Easy Deployment")
    print("✅ Skalierbar (mehrere Container)")
    print("✅ Reproduzierbar")
    print("="*60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
