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
