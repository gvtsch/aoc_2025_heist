#!/usr/bin/env python3
"""
Day 22: AI Detection Integration Test
End-to-End Test der AI-powered Detection über Tag 20's Mole Game.
Testet das RAG-basierte Detection System auf echten Heist-Daten.
"""

import requests
import time
from datetime import datetime


def log(message: str, emoji: str = "📋"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {emoji} {message}")


def main():
    """Test complete AI Detection workflow."""
    print("\n" + "="*80)
    print("🤖 Day 22: AI-Powered Detection Integration Test")
    print("="*80)
    print()
    print("Testet das komplette AI-Detection-System über Tag 20's Heist-Daten:")
    print("  1. Session mit Daten finden")
    print("  2. AI-Analyse durchführen")
    print("  3. AI-Suggestion abrufen")
    print("  4. Suspicion Scores vergleichen")
    print("  5. Mit echtem Mole vergleichen und AI-Accuracy prüfen")
    print()
    print("="*80)
    
    base_url = "http://localhost:8010"
    
    # Test 1: Find an existing session with data
    log("Test 1: Finde Session mit Daten", "🔍")
    response = requests.get(f"{base_url}/api/sessions")
    sessions_data = response.json()
    sessions = sessions_data.get("sessions", [])
    
    if not sessions:
        log("❌ Keine Sessions gefunden. Bitte erst eine Session mit Daten erstellen.", "❌")
        return
    
    # Use first session
    session_id = sessions[0]["session_id"]
    log(f"✅ Nutze Session: {session_id}", "✅")
    
    print()
    
    # Test 2: Run full AI analysis
    log("Test 2: Führe vollständige AI-Analyse durch", "🤖")
    response = requests.post(
        f"{base_url}/api/ai-detect/analyze",
        json={"session_id": session_id}
    )
    
    if response.status_code == 200:
        analysis = response.json()
        log(f"✅ AI-Analyse abgeschlossen", "✅")
        log(f"   Suggested Mole: {analysis['suggested_mole']}", "  ")
        log(f"   Confidence: {analysis['confidence']:.2%}", "  ")
        
        # Show top 3 suspects
        scores = sorted(analysis['suspicion_scores'].items(), key=lambda x: x[1], reverse=True)
        log("   Top 3 Suspects:", "  ")
        for i, (agent, score) in enumerate(scores[:3], 1):
            log(f"      {i}. {agent}: {score:.2%}", "  ")
        
        ai_suggested_mole = analysis['suggested_mole']
        ai_confidence = analysis['confidence']
    else:
        log(f"❌ AI-Analyse fehlgeschlagen: {response.status_code}", "❌")
        return
    
    print()
    
    # Test 3: Quick AI suggestion
    log("Test 3: Hole schnelle AI-Suggestion", "⚡")
    response = requests.post(
        f"{base_url}/api/ai-detect/suggest",
        json={"session_id": session_id}
    )
    
    if response.status_code == 200:
        suggestion = response.json()
        log(f"✅ Quick Suggestion: {suggestion['suggested_mole']}", "✅")
        log(f"   Confidence: {suggestion['confidence']:.2%}", "  ")
    else:
        log(f"❌ Quick Suggestion fehlgeschlagen", "❌")
    
    print()
    
    # Test 4: Compare with actual mole (using Tag 20's mole-status endpoint)
    log("Test 4: Vergleiche AI-Suggestion mit echtem Mole", "🔍")

    # Get mole status from Tag 20's HeistController
    response = requests.get(f"{base_url}/api/heist/{session_id}/mole-status")
    mole_status = response.json()

    actual_mole = mole_status.get("actual_mole")

    if actual_mole:
        log(f"   Actual Mole: {actual_mole}", "🎭")
        log(f"   AI Suggested: {ai_suggested_mole}", "🤖")

        if actual_mole == ai_suggested_mole:
            log(f"🎉 AI WAR KORREKT! (Confidence: {ai_confidence:.2%})", "🎉")
        else:
            log(f"😢 AI war falsch (aber bei {ai_confidence:.2%} Confidence)", "😢")
            log(f"   (Actual suspicion score for {actual_mole}: {analysis['suspicion_scores'].get(actual_mole, 0):.2%})", "  ")
    else:
        log("⚠️  Kein Mole in dieser Session (normale Heist-Session)", "⚠️")
    
    print()
    
    # Test 5: Get detection info
    log("Test 5: Hole AI-Detection Info", "📊")
    response = requests.get(f"{base_url}/api/detection-info")
    
    if response.status_code == 200:
        info = response.json()
        log(f"✅ Detection System: {info['name']}", "✅")
        log(f"   Weights:", "  ")
        for key, weight in info['weights'].items():
            log(f"      {key}: {weight:.0%}", "  ")
    else:
        log(f"❌ Info abrufen fehlgeschlagen", "❌")
    
    print()
    print("="*80)
    print("✅ AI-Detection Integration Test abgeschlossen!")
    print("="*80)
    print()
    print("Öffne das Dashboard um die AI-Features zu testen:")
    print(f"   http://localhost:8010")
    print()
    print("Hinweis: Die AI-Accuracy hängt von der Datenmenge ab.")
    print("Bei mehr Session-Aktivität werden die Predictions besser!")
    print()


if __name__ == "__main__":
    main()
