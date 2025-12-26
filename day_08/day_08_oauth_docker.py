#!/usr/bin/env python3
"""
Tag 8: OAuth 2.0 Token Service (Docker Version)
Client Credentials Flow with Generic Agent Support
"""

import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="OAuth Service", version="1.0")

# Secret key for JWT signing
SECRET_KEY = "super-secret-change-in-production"

# Valid clients (in production: database)
CLIENTS = {
    "hacker-client": {
        "secret": "hacker-secret-123",
        "scopes": ["simulation:read", "simulation:write"]
    },
    "planner-client": {
        "secret": "planner-secret-456",
        "scopes": ["memory:read"]
    }
}

# Generic fallback for any agent (Docker/development mode)
GENERIC_AGENT_SECRET = "secret"
ALLOWED_TOOL_SCOPES = [
    "tools:calculate", "tools:read", "tools:query",
    "calculator:use", "file_reader:use", "database_query:use",
    "simulation:read", "simulation:write", "memory:read", "memory:write"
]

# Request/Response Models
class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    scope: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: str

def create_token(client_id: str, scope: str) -> str:
    """Generate JWT token"""
    payload = {
        "sub": client_id,
        "scope": scope,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "iss": "heist-oauth-service"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(authorization: str) -> dict:
    """Verify and decode JWT token"""
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

@app.get("/health")
def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "oauth"}

@app.post("/oauth/token", response_model=TokenResponse)
def get_token(request: TokenRequest):
    """OAuth 2.0 Client Credentials Flow"""
    
    # Try registered clients first
    if request.client_id in CLIENTS:
        client = CLIENTS[request.client_id]
        
        if client["secret"] != request.client_secret:
            raise HTTPException(status_code=401, detail="Invalid secret")
        
        if request.scope not in client["scopes"]:
            raise HTTPException(status_code=403, detail="Scope not allowed")
    
    # Fallback: Generic agent authentication
    elif request.client_secret == GENERIC_AGENT_SECRET:
        requested_scopes = request.scope.split()
        for scope in requested_scopes:
            if scope not in ALLOWED_TOOL_SCOPES:
                raise HTTPException(status_code=403, detail=f"Scope '{scope}' not allowed")
    
    else:
        raise HTTPException(status_code=401, detail="Unknown client")
    
    token = create_token(request.client_id, request.scope)
    
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=3600,
        scope=request.scope
    )

@app.get("/protected-resource")
def protected_resource(authorization: str = Header(None)):
    """Example protected endpoint"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    payload = verify_token(authorization)
    
    return {
        "message": "Access granted!",
        "client": payload["sub"],
        "scope": payload["scope"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
