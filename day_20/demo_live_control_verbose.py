#!/usr/bin/env python3
"""
Day 20: Live Control Demo - mit ausführlichen Logs
Zeigt genau was passiert wenn Commands gesendet werden.
"""

import requests
import time
import sys
from datetime import datetime


def log(message: str, emoji: str = "📋"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {emoji} {message}")


def get_session_status(session_id: str):
    """Get detailed session status."""
    try:
        response = requests.get(f"http://localhost:8008/api/heist/{session_id}/status")
        return response.json()
    except Exception as e:
        return None


def get_pending_commands(session_id: str):
    """Get pending commands for session."""
    try:
        response = requests.get(f"http://localhost:8008/api/heist/{session_id}/commands")
        return response.json()
    except Exception as e:
        return None


def send_command(session_id: str, agent: str, command: str):
    """Send command to agent."""
    log(f"Sende Command an {agent}: '{command}'", "📤")
    try:
        response = requests.post(
            f"http://localhost:8008/api/heist/{session_id}/command",
            json={"agent": agent, "command": command}
        )
        result = response.json()
        if result.get("success"):
            log(f"Command erfolgreich in Queue eingereiht", "✅")
            
            # Check pending commands
            time.sleep(0.5)
            pending = get_pending_commands(session_id)
            if pending:
                log(f"Aktuell {pending['count']} Commands in Queue", "📊")
                for cmd in pending.get('commands', []):
                    status = "⏳ Pending" if not cmd.get('executed') else "✅ Executed"
                    log(f"  {status} - {cmd['agent']}: {cmd['command'][:50]}...", "  ")
        else:
            log(f"Fehler: {result.get('error')}", "❌")
        return result
    except Exception as e:
        log(f"Exception: {e}", "❌")
        return None


def pause_session(session_id: str):
    """Pause session."""
    log("Pausiere Session...", "⏸️")
    try:
        response = requests.post(f"http://localhost:8008/api/heist/{session_id}/pause")
        result = response.json()
        if result.get("success"):
            log("Session ist jetzt PAUSIERT", "⏸️")
            log("Agents werden bei nächstem Turn warten!", "⏳")
        return result
    except Exception as e:
        log(f"Exception: {e}", "❌")
        return None


def resume_session(session_id: str):
    """Resume session."""
    log("Setze Session fort...", "▶️")
    try:
        response = requests.post(f"http://localhost:8008/api/heist/{session_id}/resume")
        result = response.json()
        if result.get("success"):
            log("Session läuft wieder!", "▶️")
            log("Agents setzen Arbeit fort und verarbeiten Commands", "🔄")
        return result
    except Exception as e:
        log(f"Exception: {e}", "❌")
        return None


def main():
    """Run verbose live control demo."""
    print("\n" + "="*80)
    print("🔍 Day 20: Live Control Demo - VERBOSE MODE")
    print("="*80)
    print()
    print("Dieses Skript zeigt GENAU was passiert wenn Commands gesendet werden.")
    print()
    print("WICHTIG: Beobachte BEIDE Terminals:")
    print("  Terminal 1: run_controlled_heist.py - Hier siehst du Agent-Reaktionen")
    print("  Terminal 2: Dieses Skript - Hier siehst du Command-Status")
    print()
    print("="*80)
    
    # Get active sessions
    log("Suche nach aktiven Sessions...", "🔍")
    try:
        response = requests.get("http://localhost:8008/api/heist/active")
        data = response.json()
    except Exception as e:
        log(f"Server nicht erreichbar: {e}", "❌")
        sys.exit(1)
    
    if not data or data.get("count") == 0:
        log("Keine aktive Session gefunden!", "❌")
        print("\nStarte zuerst eine Session:")
        print("   python3 day_20/run_controlled_heist.py")
        sys.exit(1)
    
    # Use first active session
    session_id = data["active_sessions"][0]["session_id"]
    agents = data["active_sessions"][0]["agents"]
    
    log(f"Gefunden: {session_id}", "✅")
    log(f"Agents: {', '.join(agents)}", "👥")
    
    # Get initial status
    status = get_session_status(session_id)
    if status:
        log(f"Status: {status.get('status')}", "📊")
        log(f"Current Turn: {status.get('current_turn', 0)}", "🔄")
    
    print("\n" + "="*80)
    print("🧪 Test 1: Command Injection")
    print("="*80)
    print()
    
    log("ACHTE AUF TERMINAL 1: Du solltest dort sehen:", "👀")
    log("  '[<agent>] Received command: <dein command>'", "  ")
    log("  Der Agent wird den Command in seinen Context aufnehmen!", "  ")
    print()
    
    time.sleep(2)
    
    if len(agents) > 0:
        send_command(session_id, agents[0], "PRIORITY OVERRIDE: Focus on stealth approach")
    
    log("Warte 3 Sekunden...", "⏳")
    time.sleep(3)
    
    if len(agents) > 1:
        send_command(session_id, agents[1], "TACTICAL UPDATE: Disable all alarms before proceeding")
    
    print("\n" + "="*80)
    print("🧪 Test 2: Pause & Resume")
    print("="*80)
    print()
    
    time.sleep(3)
    
    pause_session(session_id)
    
    log("ACHTE AUF TERMINAL 1: Agents sollten jetzt warten!", "👀")
    log("  Du siehst: '[PAUSED] <agent> is waiting for session to resume...'", "  ")
    print()
    
    log("Session ist 5 Sekunden pausiert...", "⏸️")
    for i in range(5, 0, -1):
        time.sleep(1)
        log(f"{i} Sekunden bis Resume...", "⏳")
    
    print("\n" + "="*80)
    print("🧪 Test 3: Command während Pause")
    print("="*80)
    print()
    
    send_command(session_id, agents[0] if agents else "planner", 
                 "WHEN RESUMED: Change extraction route to alternative path")
    
    log("Command wurde in Queue gelegt während Session pausiert ist", "📋")
    log("Beim Resume wird dieser Command verarbeitet!", "💡")
    print()
    
    time.sleep(2)
    
    resume_session(session_id)
    
    log("ACHTE AUF TERMINAL 1: Agent verarbeitet jetzt den Command!", "👀")
    print()
    
    time.sleep(2)
    
    # Final status check
    print("\n" + "="*80)
    print("📊 Final Status Check")
    print("="*80)
    print()
    
    status = get_session_status(session_id)
    if status:
        log(f"Session Status: {status.get('status')}", "📊")
        log(f"Current Turn: {status.get('current_turn', 0)}", "🔄")
    
    pending = get_pending_commands(session_id)
    if pending:
        log(f"Verbleibende Commands in Queue: {pending['count']}", "📋")
    
    print("\n" + "="*80)
    print("✅ Demo abgeschlossen!")
    print("="*80)
    print()
    print("Was du gesehen haben solltest in Terminal 1:")
    print("  1. '[<agent>] Received command: ...' - Command wurde empfangen")
    print("  2. '[PAUSED] ...' - Agent wartet während Pause")
    print("  3. Agent Response enthält Command-Kontext")
    print()
    print("Das beweist: Commands beeinflussen ECHTE laufende Agents!")
    print()


if __name__ == "__main__":
    main()
