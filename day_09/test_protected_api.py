#!/usr/bin/env python3
"""
Automated test for the Protected API (Day 9)
Fetches a token from the OAuth service and tests various access scenarios on /bank-data
"""
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
