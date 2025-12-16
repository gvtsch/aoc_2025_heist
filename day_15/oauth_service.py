"""
Day 15: OAuth Service
Simplified OAuth2 service for agent authentication
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="OAuth Service", version="1.0.0")

# Simple token storage (in-memory)
tokens = {}
token_counter = 0


class TokenRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    scope: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scope: str


@app.post("/token", response_model=TokenResponse)
def create_token(request: TokenRequest):
    """Generate access token for agent with requested scopes."""
    global token_counter

    # Validate grant type
    if request.grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")

    # Simple validation (in real app: check client credentials)
    if not request.client_id:
        raise HTTPException(status_code=400, detail="Missing client_id")

    # Generate token
    token_counter += 1
    token = f"token_{request.client_id}_{token_counter}"

    # Store token with metadata
    tokens[token] = {
        "client_id": request.client_id,
        "scopes": request.scope.split() if request.scope else []
    }

    return TokenResponse(
        access_token=token,
        scope=request.scope
    )


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "oauth-service",
        "active_tokens": len(tokens)
    }


if __name__ == "__main__":
    print("🔐 Starting OAuth Service")
    print("🚀 Service running on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
