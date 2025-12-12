#!/usr/bin/env python3
"""
Tag 12: Memory Microservice + Model Context Protocol (MCP) Demo
Client-Demo für MCP Memory Server
"""

from fastapi.testclient import TestClient
from memory_server import app

# Test client für MCP Server
client = TestClient(app)


def main():
    print("="*60)
    print("TAG 12: MEMORY MICROSERVICE + MCP")
    print("="*60)

    # Health Check
    response = client.get("/health")
    health = response.json()
    print(f"Status: {health['status']}")
    print(f"Service: {health['service']}")

    # Tool Discovery
    response = client.get("/")
    info = response.json()
    print(f"Service: {info['service']}")
    print(f"Available Tools: {len(info['tools'])}")
    
    # Show discovered tools
    for tool in info['tools']:
        print(f"  POST /tools/{tool}")

    print("\n" + "="*40)

    session_id = "microservice-demo"

    # Store memory
    store_request = {
        "game_session_id": session_id,
        "agent_id": "planner",
        "turn_id": 1,
        "phase": "planning",
        "message": "We need to plan this carefully."
    }
    response = client.post("/tools/store_memory", json=store_request)
    print(f"Stored: {response.json()}")

    # Add test data
    test_messages = [
        "Security analysis: Two guards at main entrance, one at back.",
        "Timing critical: Bank closes at 6 PM, security system activates at 6:15 PM.",
        "Equipment check: Need 3 lockpicks, 2 radios, 1 thermal scanner.",
        "Escape route: Through maintenance tunnels to parking garage.",
        "Team coordination: Planner leads, Hacker disables alarms, Lookout watches streets.",
        "Risk assessment: Police response time approximately 8 minutes.",
        "Contingency plan: If detected, abort via emergency exit on 2nd floor.",
    ]
    
    for i, message in enumerate(test_messages, 2):
        test_request = {
            "agent_id": "planner",
            "turn_id": i,
            "message": message,
            "game_session_id": session_id,
            "phase": "planning"
        }
        client.post("/tools/store_memory", json=test_request)

    # Retrieve memory
    get_request = {
        "agent_id": "planner",
        "game_session_id": session_id,
        "limit": 5
    }
    response = client.post("/tools/get_recent_turns", json=get_request)
    data = response.json()
    print(f"Retrieved: {len(data.get('turns', []))} turns")

    # Test hierarchical compression (wie Tag 11)
    print("\nHierarchical Compression Tests:")
    
    for max_tokens, recent_count in [(30, 2), (150, 2)]:
        compress_request = {
            "agent_id": "planner",
            "game_session_id": session_id,
            "max_tokens": max_tokens,
            "recent_count": recent_count
        }
        response = client.post("/tools/get_compressed_memory", json=compress_request)
        data = response.json()
        
        print(f"\n📚 {max_tokens} tokens, recent_count={recent_count}:")
        if data.get('summary'):
            print(f"📝 Compressed: {data['summary']}")
        print(f"🔥 Recent ({len(data.get('recent_messages', []))}):")
        for msg in data.get('recent_messages', [])[-2:]:  # Nur letzte 2 zeigen
            print(f"  - {msg['message'][:50]}...")
        print(f"💾 Total tokens: {data.get('token_count', 0)}")

    print("\n✅ MCP Memory Service functional!")


if __name__ == "__main__":
    main()
