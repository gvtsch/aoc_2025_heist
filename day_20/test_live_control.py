#!/usr/bin/env python3
"""
Day 20: Live Control Test
End-to-End Test mit echten Agents und LM Studio.
Startet eine echte Heist-Session und testet Command-Injection während der Ausführung.
"""

import sys
import os
from pathlib import Path
import time
import threading
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from day_16.integrated_system import (
    ConfigLoader,
    DatabaseManager,
    OAuthClient,
    ToolClient,
    MemoryServiceClient
)
from integrated_agent_with_controller import IntegratedAgentWithController
from heist_controller import get_controller
from openai import OpenAI


def run_heist_session(session_id: str, max_turns: int = 5):
    """
    Führt eine echte Heist-Session mit Agents aus.
    Diese Funktion läuft in einem separaten Thread.
    """
    print(f"\n{'='*80}")
    print(f"🎮 Starting Live Heist Session: {session_id}")
    print(f"{'='*80}\n")
    
    # ========================================================================
    # 1. LOAD CONFIGURATION
    # ========================================================================
    config_path = os.path.join(os.path.dirname(__file__), "agents_config.yaml")
    config = ConfigLoader.load_config(config_path)
    
    # ========================================================================
    # 2. INITIALIZE SERVICES
    # ========================================================================
    db_path = os.path.join(os.path.dirname(__file__), "controlled_heist.db")
    db_manager = DatabaseManager(db_path)
    
    llm_client = OpenAI(
        base_url=config.llm['base_url'],
        api_key=config.llm['api_key']
    )
    
    oauth_client = OAuthClient(config.oauth_service)
    tool_client = ToolClient(config.tool_services)
    memory_client = MemoryServiceClient(config.memory_service)
    
    # ========================================================================
    # 3. INITIALIZE AGENTS WITH CONTROLLER INTEGRATION
    # ========================================================================
    agents = []
    for agent_config in config.agents[:2]:  # Nur 2 Agents für schnelleren Test
        agent = IntegratedAgentWithController(
            config=agent_config,
            llm_client=llm_client,
            oauth_client=oauth_client,
            tool_client=tool_client,
            memory_client=memory_client,
            session_id=session_id,
            db_manager=db_manager
        )
        agents.append(agent)
        print(f"   ✓ Agent initialized: {agent_config.name}")
    
    # ========================================================================
    # 4. REGISTER SESSION IN CONTROLLER FIRST
    # ========================================================================
    controller = get_controller()
    
    agent_names = [agent.config.name for agent in agents]
    controller.start_session(
        session_id=session_id,
        agents=agent_names,
        config={}
    )
    
    # Then create in database
    db_manager.create_session(session_id)
    
    print(f"\n✅ Session {session_id} registered in controller\n")
    print(f"   Agents: {', '.join(agent_names)}")
    
    # ========================================================================
    # 5. RUN HEIST WITH CONTROLLER INTEGRATION
    # ========================================================================
    conversation_history = []
    
    for turn in range(1, max_turns + 1):
        print(f"\n{'='*80}")
        print(f"🔄 TURN {turn}/{max_turns}")
        print(f"{'='*80}")
        
        # Check if paused
        if controller.is_paused(session_id):
            print(f"⏸️  Session is PAUSED - waiting...")
            while controller.is_paused(session_id):
                time.sleep(1)
            print(f"▶️  Session RESUMED")
        
        for agent in agents:
            print(f"\n💬 {agent.config.name}:")
            
            try:
                # Agent respond (with controller integration)
                response = agent.respond(conversation_history, turn)
                
                print(f"   {response[:100]}...")
                
                conversation_history.append({
                    "agent": agent.config.name,
                    "message": response
                })
                
                # Small delay between agents
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Delay between turns
        time.sleep(2)
    
    print(f"\n{'='*80}")
    print(f"✅ Heist Session {session_id} completed!")
    print(f"{'='*80}\n")


def send_test_commands(session_id: str, base_url: str = "http://localhost:8008"):
    """
    Sendet Test-Commands während die Session läuft.
    Diese Funktion läuft im Hauptthread.
    """
    print(f"\n{'='*80}")
    print(f"📡 Command Injection Test")
    print(f"{'='*80}\n")
    
    # Wait for session to start
    print("⏳ Waiting for session to initialize...")
    time.sleep(3)
    
    # Test 1: Send command to first agent
    print("\n🔹 Test 1: Sending command to 'planner'")
    response = requests.post(
        f"{base_url}/api/heist/{session_id}/command",
        json={
            "agent": "planner",
            "command": "Change strategy: Focus on stealth over speed"
        }
    )
    result = response.json()
    print(f"   Result: {result}")
    
    time.sleep(5)
    
    # Test 2: Pause session
    print("\n🔹 Test 2: Pausing session")
    response = requests.post(f"{base_url}/api/heist/{session_id}/pause")
    result = response.json()
    print(f"   Result: {result}")
    
    time.sleep(3)
    
    # Test 3: Send command while paused
    print("\n🔹 Test 3: Sending command while paused")
    response = requests.post(
        f"{base_url}/api/heist/{session_id}/command",
        json={
            "agent": "hacker",
            "command": "When you resume, focus on disabling alarms"
        }
    )
    result = response.json()
    print(f"   Result: {result}")
    
    time.sleep(3)
    
    # Test 4: Resume session
    print("\n🔹 Test 4: Resuming session")
    response = requests.post(f"{base_url}/api/heist/{session_id}/resume")
    result = response.json()
    print(f"   Result: {result}")
    
    # Wait for session to finish
    print("\n⏳ Waiting for session to complete...")
    time.sleep(15)
    
    # Test 5: Check final status
    print("\n🔹 Test 5: Checking final status")
    response = requests.get(f"{base_url}/api/heist/{session_id}/status")
    result = response.json()
    print(f"   Final Status: {result}")
    
    print(f"\n{'='*80}")
    print(f"✅ Command Injection Test completed!")
    print(f"{'='*80}\n")


def main():
    """Run live control test."""
    session_id = f"live_test_{int(time.time())}"
    
    print("\n" + "="*80)
    print("🧪 Day 20: Live Control Test - End-to-End")
    print("="*80)
    print()
    print("Dieser Test startet eine ECHTE Heist-Session mit LM Studio")
    print("und sendet Commands während der Ausführung.")
    print()
    print("Was getestet wird:")
    print("  1. ✅ Echte Agents mit LM Studio Integration")
    print("  2. ✅ Command Injection während der Ausführung")
    print("  3. ✅ Pause/Resume einer laufenden Session")
    print("  4. ✅ Agent-Reaktion auf Commands")
    print()
    print("="*80)
    
    # Start heist in separate thread
    heist_thread = threading.Thread(
        target=run_heist_session,
        args=(session_id, 5)
    )
    heist_thread.start()
    
    # Send commands from main thread
    send_test_commands(session_id)
    
    # Wait for heist to finish
    heist_thread.join()
    
    print("\n" + "="*80)
    print("🎉 Live Control Test abgeschlossen!")
    print("="*80)


if __name__ == "__main__":
    main()
