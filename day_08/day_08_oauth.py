#!/usr/bin/env python3
"""
Tag 8: OAuth 2.0 Token Service
Client Credentials Flow
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
        # Extract token from "Bearer <token>"
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

@app.post("/oauth/token", response_model=TokenResponse)
def get_token(request: TokenRequest):
    """OAuth 2.0 Client Credentials Flow"""

    # Validate client credentials
    if request.client_id not in CLIENTS:
        raise HTTPException(status_code=401, detail="Unknown client")

    client = CLIENTS[request.client_id]

    if client["secret"] != request.client_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")

    # Check if scope is allowed
    if request.scope not in client["scopes"]:
        raise HTTPException(status_code=403, detail="Scope not allowed")

    # Generate token
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
    print("="*60)
    print("TAG 8: OAUTH 2.0")
    print("="*60)
    print("\n🚀 OAuth Service starting...")
    print("\n📖 Test flow:")
    print("1. Get token:")
    print('   curl -X POST http://localhost:8001/oauth/token \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"client_id": "hacker-client", "client_secret": "hacker-secret-123", "scope": "simulation:read"}\'')
    print("\n2. Use token:")
    print('   curl http://localhost:8001/protected-resource \\')
    print('     -H "Authorization: Bearer <your-token>"')
    print()

    uvicorn.run(app, host="0.0.0.0", port=8001)
