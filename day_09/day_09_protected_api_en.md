Day nine. We're getting closer. Today is all about protected APIs.

Much of this will hopefully look familiar—some of it from yesterday. Here’s the core code:

```python
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
```

The script starts a FastAPI service that only gives out sensitive bank data to authorized agents. Authentication is done via a Bearer token (a JWT) previously issued by the OAuth service. No valid token, no access. And with the wrong scope, access is denied as well.

A bit more detail: The token is extracted from the Authorization header and checked (expiration, signature). Only those with the "simulation:read" scope get access to the bank data.

**Context:**
This kind of architecture is standard when microservices or different agents need to communicate securely. Scopes and tokens allow you to control permissions flexibly and precisely—and you can intentionally create information asymmetry.

You start by running the service with `day_09_protected_api.py`. You’ll also need to start the OAuth service from day eight (`day_08_oauth.py`) on port 8001.

```bash
lsof -i :8001
lsof -i :8003
```

The above commands let you check if the services are running.

Now for the fun part: testing. I wrote a test script to automate this for you.

```python
import requests

OAUTH_URL = "http://localhost:8001/oauth/token"
PROTECTED_URL = "http://localhost:8003/bank-data"

CLIENTS = [
    {"id": "hacker-client", "secret": "hacker-secret-123", "scope": "simulation:read"},  # Successful
    {"id": "hacker-client", "secret": "wrong", "scope": "simulation:read"},              # Wrong secret
    {"id": "hacker-client", "secret": "hacker-secret-123", "scope": "memory:read"},      # Wrong scope
    {"id": "planner-client", "secret": "planner-secret-456", "scope": "simulation:read"} # Planner not allowed
]

def get_token(client_id, client_secret, scope):
    resp = requests.post(
        OAUTH_URL,
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope
        }
    )

    print(f"Token request ({client_id}, {scope}): {resp.status_code}")
    print(f"Response: {resp.text}\n")
    return resp.json().get("access_token") if resp.ok else None

def test_bank_data(token):

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.get(PROTECTED_URL, headers=headers)
    print(f"/bank-data status: {resp.status_code}")
    print(f"Response: {resp.text}\n")

def main():
    print("== Successful access (Hacker) ==")
    token = get_token("hacker-client", "hacker-secret-123", "simulation:read")
    test_bank_data(token)

    print("== Wrong secret ==")
    token = get_token("hacker-client", "wrong", "simulation:read")
    test_bank_data(token)

    print("== Wrong scope ==")
    token = get_token("hacker-client", "hacker-secret-123", "memory:read")
    test_bank_data(token)

    print("== Planner tries to access ==")
    token = get_token("planner-client", "planner-secret-456", "simulation:read")
    test_bank_data(token)

    print("== No token ==")
    test_bank_data(None)

if __name__ == "__main__":
    main()
```

The output is:

```bash
== Successful access (Hacker) ==
Token request (hacker-client, simulation:read): 200
Response: { ... }

/bank-data status: 200
Response: { ... }

== Wrong secret ==
Token request (hacker-client, simulation:read): 401
Response: { ... }

/bank-data status: 401
Response: { ... }

== Wrong scope ==
Token request (hacker-client, memory:read): 403
Response: { ... }

/bank-data status: 401
Response: { ... }

== Planner tries to access ==
Token request (planner-client, simulation:read): 403
Response: { ... }

/bank-data status: 401
Response: { ... }

== No token ==
/bank-data status: 401
Response: { ... }
```

What does this mean?
Only the hacker gets a token and access with the correct secret and scope. All other cases (wrong secret, wrong scope, planner, no token) are correctly denied. The responses simply reflect the security logic: no valid token, no access to sensitive data.

**Other error cases:**
- If the token is expired, you get a `401 Token expired`.
- If the token is manipulated or the signature is invalid, you get a `401 Invalid token`.
- If the Authorization header is missing, you get a `401 No authorization header`.

## Security Best Practices
- Never store secrets or tokens in code or repositories—use environment variables or secret management instead.
- Always use HTTPS so tokens and sensitive data aren’t sent in plain text.
- Tokens should have a reasonable lifetime and be renewed regularly.
- Logging and monitoring help detect suspicious access.


## Summary
Role-based access control creates information asymmetry—just like in real life. Only the hacker agent gets in; everyone else stays outside.
