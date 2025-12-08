Day 8. The second week. Today is all about token-based authentication.

Today, we're building a simple OAuth 2.0 token service with FastAPI, implementing the Client Credentials Flow. It's a common authentication method to securely grant machines (or, in our case, microservices, bots, ...) access to an API.

Let's break it down before we implement it. First, the client sends its client ID, secret, and desired scope to the token endpoint of the auth server. The server checks the data and issues a JWT token. That's a JSON Web Token—a compact, URL-safe token format. It only contains characters that can be safely transmitted in a URL without encoding or modification: letters, numbers, dashes, underscores, and dots. The JWT token contains information as a JSON object, transferred between two parties. Finally, the client can use the token to access protected resources.

Important: The token isn't valid forever! It expires after a certain time (in our case, after one hour). If the token expires, the client needs to request a new one. This keeps access up-to-date and secure—stolen or outdated tokens automatically lose their validity.

And why is this important for our project? Not every "agent" should have access to all information! Just like in real, professional life.

**Quick detour: Why is this actually secure?**
The principle is simple. Only those who know the correct client ID and secret get a token. And only with this token can you access protected endpoints. The token itself is a signed JWT—it can't just be forged. The permissions (scopes) are checked when the token is issued and stored in the token. No valid token, no access.

Of course, anyone who knows the secret can impersonate that client. That's why, as always, secrets don't belong in the repo, but in environment variables or a secret management system. In real systems, they're rotated regularly and well protected. But the principle remains... No secret, no token; no token, no access. And that's exactly how we want it for our agents and services!

On to the implementation... Since we already know some of this, I won't show or mention everything again. The complete file is in the repository: https://github.com/gvtsch/aoc_2025_heist/blob/main/day_08

## The FastAPI app and the clients

```python
app = FastAPI(title="OAuth Service", version="1.0")

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
```

Here we define our API and the allowed clients. Each client has a secret and a list of scopes (permissions). In reality, this would be stored in a database, but for our purposes, a dictionary is enough.

## TokenRequest and TokenResponse

```python
class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    scope: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: str
```

These are the data models for the request and response at the token endpoint. The client sends its data as JSON, and we reply with the token and some metadata.

## Token generation

At some point, the JWT has to be built.

```python
def create_token(client_id: str, scope: str) -> str:
    payload = {
        "sub": client_id,
        "scope": scope,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "iss": "heist-oauth-service"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

The payload contains:
- sub: Who is the client?
- scope: What is allowed?
- exp: When does the token expire?
- iat: When was it created?
- iss: Who issued the token?

And this token is then signed with our secret key.

## Token validation

```python
def verify_token(authorization: str) -> dict:
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
```

Here, the token is extracted from the header and checked. If everything fits, we get the payload back—otherwise, there's an error.

## Token endpoint

And now to the endpoint where the magic happens.

```python
@app.post("/oauth/token", response_model=TokenResponse)
def get_token(request: TokenRequest):
    if request.client_id not in CLIENTS:
        raise HTTPException(status_code=401, detail="Unknown client")
    client = CLIENTS[request.client_id]
    if client["secret"] != request.client_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    if request.scope not in client["scopes"]:
        raise HTTPException(status_code=403, detail="Scope not allowed")
    token = create_token(request.client_id, request.scope)
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=3600,
        scope=request.scope
    )
```

The client sends its credentials and desired scope to the endpoint. The server checks if the client is known, if the secret matches, and if the scope is allowed. Only if all conditions are met is a token generated and returned. This token is the key for further access to protected resources—and that's exactly how the Client Credentials Flow in OAuth 2.0 works: machines authenticate, get a time-limited access token, and can then access APIs without a user being involved.

## Protected resource

To test all this, we need something that's protected.

```python
@app.get("/protected-resource")
def protected_resource(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    payload = verify_token(authorization)
    return {
        "message": "Access granted!",
        "client": payload["sub"],
        "scope": payload["scope"]
    }
```

Here, the client has to present its token. The token is checked, and we allow access if everything fits. This is how we protect our resource (or API) from unauthorized access and control who can do what.

And to test everything automatically, I wrote a test file.

```python
#!/usr/bin/env python3
"""
Simple test script for the OAuth 2.0 Service (Day 8)
Requests a token and tests access to the protected resource
"""
import requests

BASE_URL = "http://localhost:8001"

def get_token(client_id, client_secret, scope):
    resp = requests.post(
        f"{BASE_URL}/oauth/token",
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope
        }
    )
    print(f"Token request status: {resp.status_code}")
    print(f"Response: {resp.text}\n")
    return resp.json().get("access_token") if resp.ok else None

def test_protected(token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.get(f"{BASE_URL}/protected-resource", headers=headers)
    print(f"Protected resource status: {resp.status_code}")
    print(f"Response: {resp.text}\n")

def main():
    print("== Successful access ==")
    token = get_token("hacker-client", "hacker-secret-123", "simulation:read")
    test_protected(token)

    print("== Wrong secret ==")
    token = get_token("hacker-client", "wrong", "simulation:read")
    test_protected(token)

    print("== Wrong scope ==")
    token = get_token("hacker-client", "hacker-secret-123", "memory:read")
    test_protected(token)

    print("== No token ==")
    test_protected(None)

if __name__ == "__main__":
    main()
```

This file covers four cases:
1. Successful access: We get a token with correct data and use it to access the protected resource. Result: Access granted, everything works as planned.
2. Wrong secret: We intentionally provide a wrong secret. The server rejects it—no token, no access. That's how it should be!
3. Wrong scope: We request a scope the client isn't allowed to have. Again, no token and no access to the resource. Permissions are checked properly.
4. No token: We try to access the resource without a token. The server immediately blocks—no valid ID, no entry.

Each case shows how the service reacts to typical errors or missing permissions. Only those who identify themselves correctly and have the right permissions get through. That's exactly how we want it for our agents and services!

## What would be different in production?

In real applications, there are a few things to keep in mind:
- **Clients and secrets** aren't stored in code, but in a database or secret management system.
- **Secrets** should never be in the repository, but provided via environment variables or special tools.
- **HTTPS** is a must! Only then are data and tokens really transmitted securely.
- **Token lifetime and rotation**: Tokens should be renewed regularly and expired tokens invalidated.
- **Monitoring and logging**: Suspicious accesses and errors should be monitored.
- **Rate limits and IP whitelists**: Protect against abuse and attacks.

This example is intentionally simple so we can understand the principle and rebuild it directly. For production systems, there are many more best practices. But that's not my main focus here.

## Summary

Today, we successfully implemented an OAuth 2.0 service. This way, we control who has access to what—and who doesn't.
