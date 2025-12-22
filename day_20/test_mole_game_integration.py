#!/usr/bin/env python3
"""
Day 20/21: Mole Game Integration Test
End-to-End Test des Mole Games über Tag 20's Interactive Dashboard.
"""

import requests
import time
from datetime import datetime


def log(message: str, emoji: str = "📋"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {emoji} {message}")


def main():
    """Test complete Mole Game workflow."""
    print("\n" + "="*80)
    print("🎮 Day 20/21: Mole Game Integration Test")
    print("="*80)
    print()
    print("Testet das komplette Mole Game über Tag 20's Dashboard:")
    print("  1. Session mit Mole starten")
    print("  2. Mole markieren (Detection)")
    print("  3. Detection evaluieren (SUCCESS/FAILURE/BUSTED)")
    print("  4. Mole aufdecken (Reveal)")
    print()
    print("="*80)
    
    base_url = "http://localhost:8008"
    session_id = f"mole_test_{int(time.time())}"
    
    # Test 1: Start Session with Mole
    log("Test 1: Starte Session mit zufälligem Mole", "🎲")
    response = requests.post(
        f"{base_url}/api/heist/start",
        json={
            "session_id": session_id,
            "agents": ["planner", "hacker", "safecracker"],
            "config": {}
        }
    )
    data = response.json()
    
    if data.get("success") and data.get("mole_selected"):
        log(f"✅ Session gestartet: {session_id}", "✅")
        log(f"   Agents: {', '.join(data['agents'])}", "  ")
        log(f"   Mole wurde zufällig ausgewählt!", "🎭")
    else:
        log("❌ Session-Start fehlgeschlagen", "❌")
        return
    
    print()
    
    # Test 2: Get initial mole status (should hide actual mole)
    log("Test 2: Hole Mole-Status", "🔍")
    response = requests.get(f"{base_url}/api/heist/{session_id}/mole-status")
    status = response.json()
    
    log(f"   Detected Mole: {status.get('detected_mole', 'None')}", "  ")
    log(f"   Actual Mole: {status.get('actual_mole', 'Hidden')}", "  ")
    print()
    
    # Test 3: Mark suspect (simulate user clicking on agent)
    log("Test 3: Markiere Verdächtigen", "🕵️")
    suspected_agent = data["agents"][0]  # Pick first agent
    response = requests.post(
        f"{base_url}/api/heist/{session_id}/detect-mole",
        json={"agent": suspected_agent}
    )
    result = response.json()
    
    if result.get("success"):
        log(f"✅ {suspected_agent} als Verdächtiger markiert", "✅")
    else:
        log(f"❌ Fehler: {result.get('error')}", "❌")
    
    print()
    
    # Test 4: Evaluate detection
    log("Test 4: Evaluiere Detection", "🎯")
    response = requests.post(f"{base_url}/api/heist/{session_id}/evaluate-detection")
    evaluation = response.json()
    
    if evaluation.get("success"):
        outcome = evaluation["outcome"]
        message = evaluation["message"]
        
        if outcome == "SUCCESS":
            log(f"🎉 {message}", "🎉")
        elif outcome == "FAILURE":
            log(f"😢 {message}", "😢")
        else:  # BUSTED
            log(f"💥 {message}", "💥")
        
        log(f"   Outcome: {outcome}", "  ")
        log(f"   Suspected: {evaluation['detected_mole']}", "  ")
        log(f"   Actual: {evaluation['actual_mole']}", "  ")
    else:
        log(f"❌ Fehler: {evaluation.get('error')}", "❌")
    
    print()
    
    # Test 5: Reveal mole
    log("Test 5: Decke Mole auf", "🔍")
    response = requests.post(f"{base_url}/api/heist/{session_id}/reveal-mole")
    reveal = response.json()
    
    if reveal.get("success"):
        log(f"   {reveal['message']}", "🎭")
        log(f"   Korrekt erkannt: {reveal['is_correct']}", "  ")
    else:
        log(f"❌ Fehler", "❌")
    
    print()
    
    # Final status
    log("Final: Hole finalen Status", "📊")
    response = requests.get(f"{base_url}/api/heist/{session_id}/mole-status")
    final_status = response.json()
    
    log(f"   Actual Mole: {final_status['actual_mole']}", "  ")
    log(f"   Detected Mole: {final_status['detected_mole']}", "  ")
    log(f"   Is Correct: {final_status['is_correct']}", "  ")
    log(f"   Game Outcome: {final_status['game_outcome']}", "  ")
    
    print()
    print("="*80)
    print("✅ Mole Game Integration Test abgeschlossen!")
    print("="*80)
    print()
    print("Öffne das Dashboard um die UI zu testen:")
    print(f"   http://localhost:8008")
    print()


if __name__ == "__main__":
    main()
