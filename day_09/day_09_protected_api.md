
Tag neun. Wir kommen der Sache näher. Heute geht es um Protected APIs.

Vieles wird dir hoffentlich bekannt vorkommen. Teilweise von gestern. Der eigentliche Code: 

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

Das Skript startet einen FastAPI-Service, der sensible Bankdaten nur an berechtigte Agenten herausgibt. Die Authentifizierung läuft über einen Bearer Token (ein JWT), der vorher vom OAuth-Service ausgestellt wurde. Ohne gültigen Token gibt es keinen Zutritt, und mit dem falschen Scope auch nicht.

Etwas detaillierter: Der Token wird aus dem Authorization-Header extrahiert und geprüft (Ablaufdatum, Signatur). Nur wer den Scope "simulation:read" hat, bekommt Zugriff auf die Bankdaten. 

**Einordnung:**
Solche Architekturen sind Standard, wenn Microservices oder verschiedene Agenten sicher miteinander kommunizieren sollen. Über Scopes und Tokens lassen sich Berechtigungen klar und flexibel steuern – und man kann gezielt Information Asymmetrie herstellen.


```bash
lsof -i :8001
lsof -i :8003
```

Mit den obigen Befehlen kann man prüfen, ob die Services laufen.


Kommen wir nun zum Testen. Dafür habe ich ein Testskript geschrieben. Das nimmt uns das automatisiert ab. 

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


Die Rückmeldung ist:

```bash
== Successful access (Hacker) ==
Token request (hacker-client, simulation:read): 200
Response: {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoYWNrZXItY2xpZW50Iiwic2NvcGUiOiJzaW11bGF0aW9uOnJlYWQiLCJleHAiOjE3NjUyOTQxNzMsImlhdCI6MTc2NTI5MDU3MywiaXNzIjoiaGVpc3Qtb2F1dGgtc2VydmljZSJ9.t_HPWh62Ykie6GtG7CKJ19jJOqYZZFstpR6xylLhs5Y","token_type":"Bearer","expires_in":3600,"scope":"simulation:read"}

/bank-data status: 200
Response: {"data":{"name":"First National Bank","address":"123 Main Street","floors":3,"vault_rating":"TL-30","security_systems":["CCTV","Motion Sensors","Alarm"],"guard_count":4},"access_granted_to":"hacker-client","scope":"simulation:read"}

== Wrong secret ==
Token request (hacker-client, simulation:read): 401
Response: {"detail":"Invalid secret"}

/bank-data status: 401
Response: {"detail":"No authorization header"}

== Wrong scope ==
Token request (hacker-client, memory:read): 403
Response: {"detail":"Scope not allowed"}

/bank-data status: 401
Response: {"detail":"No authorization header"}

== Planner tries to access ==
Token request (planner-client, simulation:read): 403
Response: {"detail":"Scope not allowed"}

/bank-data status: 401
Response: {"detail":"No authorization header"}

== No token ==
/bank-data status: 401
Response: {"detail":"No authorization header"}
```


Und was bedeutet das nun? 
Nur der Hacker bekommt mit korrektem Secret und passendem Scope ein Token und den Zugriff. Alle anderen Fälle (falsches Secret, falscher Scope, Planner, kein Token) werden korrekt abgelehnt. Die Rückgaben spiegeln die Sicherheitslogik wider: Ohne gültigen Token kein Zugang zu sensiblen Daten.

**Weitere Fehlerfälle:**
- Ist das Token abgelaufen, gibt es ein `401 Token expired`.
- Ist das Token manipuliert oder die Signatur ungültig, gibt es ein `401 Invalid token`.
- Fehlt der Authorization-Header ganz, gibt es ein `401 No authorization header`.


## Zusammenfassung
Rollenspezifische Zugriffsrechte sorgen für Informationsasymmetrie – genau wie im echten Leben. Nur der Hacker-Agent kommt rein, alle anderen müssen draußen bleiben.