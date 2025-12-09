#!/usr/bin/env python3
"""
Tag 9: Protected API (OAuth in Action)
Simulation Service = OAuth-geschützt!

Bearer Token Validation + Scope Checking
"""

import jwt
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Protected Simulation Service", version="1.0")

# Secret Key (gleicher wie OAuth Service)
SECRET_KEY = "super-secret-change-in-production"

# Fake Bank Data (nur für Demo)
BANK_DATA = {
    "name": "First National Bank",
    "address": "123 Main Street",
    "floors": 3,
    "vault_rating": "TL-30",
    "security_systems": ["CCTV", "Motion Sensors", "Alarm"],
    "guard_count": 4
}

class BankDataResponse(BaseModel):
    data: dict
    access_granted_to: str
    scope: str

def verify_token(authorization: str) -> dict:
    """Verify and decode JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")

    try:
        # Extract token from "Bearer <token>"
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization format")

        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # Check token expiration
        if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token expired")

        return payload

    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def check_scope(token_payload: dict, required_scope: str):
    """Check if token has required scope"""
    token_scope = token_payload.get("scope", "")

    if required_scope not in token_scope:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required: {required_scope}, Got: {token_scope}"
        )

@app.get("/")
def root():
    """Public endpoint - no auth required"""
    return {
        "service": "Protected Simulation API",
        "status": "online",
        "auth": "OAuth 2.0 Bearer Token required",
        "endpoints": {
            "/bank-data": "GET (requires simulation:read scope)"
        }
    }

@app.get("/bank-data", response_model=BankDataResponse)
def get_bank_data(authorization: str = Header(None)):
    """
    Protected endpoint - requires valid OAuth token with simulation:read scope

    Only Hacker Agent has this scope!
    """

    # 1. Verify token
    token_payload = verify_token(authorization)

    # 2. Check scope
    check_scope(token_payload, "simulation:read")

    # 3. Access granted! Return sensitive data
    return BankDataResponse(
        data=BANK_DATA,
        access_granted_to=token_payload["sub"],
        scope=token_payload["scope"]
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
