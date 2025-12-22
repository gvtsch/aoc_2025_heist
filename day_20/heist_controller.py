"""
Day 20: Heist Controller
Backend für interaktive Heist-Steuerung.
Ermöglicht Pause/Resume, Agent-Commands, und Status-Updates.
Tag 21 Integration: Mole Game Mechanics
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import asyncio
import json
import random


class HeistStatus(Enum):
    """Status eines laufenden Heists."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class HeistController:
    """
    Steuert laufende Heist-Sessions.
    Ermöglicht Pause/Resume, Command-Injection, Status-Tracking.
    """

    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.command_queue: Dict[str, List[Dict]] = {}
        self.pause_flags: Dict[str, bool] = {}

    def start_session(self, session_id: str, agents: List[str], config: Dict) -> Dict:
        """Starte eine neue Heist-Session mit optionalem Mole Game."""
        # Random mole selection für Tag 21 Game
        mole = random.choice(agents) if len(agents) > 0 else None
        
        self.active_sessions[session_id] = {
            "session_id": session_id,
            "status": HeistStatus.RUNNING.value,
            "agents": agents,
            "config": config,
            "start_time": datetime.now().isoformat(),
            "current_turn": 0,
            "mole": mole,  # Randomly selected mole for Tag 21
            "detected_mole": None,
            "game_outcome": None
        }
        self.command_queue[session_id] = []
        self.pause_flags[session_id] = False

        return {
            "success": True,
            "session_id": session_id,
            "message": f"Heist session {session_id} started",
            "agents": agents,
            "mole_selected": mole is not None
        }

    def pause_session(self, session_id: str) -> Dict:
        """Pausiere eine laufende Session."""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        if self.active_sessions[session_id]["status"] != HeistStatus.RUNNING.value:
            return {"success": False, "error": "Session is not running"}

        self.active_sessions[session_id]["status"] = HeistStatus.PAUSED.value
        self.pause_flags[session_id] = True

        return {
            "success": True,
            "session_id": session_id,
            "message": "Heist paused",
            "status": HeistStatus.PAUSED.value
        }

    def resume_session(self, session_id: str) -> Dict:
        """Setze eine pausierte Session fort."""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        if self.active_sessions[session_id]["status"] != HeistStatus.PAUSED.value:
            return {"success": False, "error": "Session is not paused"}

        self.active_sessions[session_id]["status"] = HeistStatus.RUNNING.value
        self.pause_flags[session_id] = False

        return {
            "success": True,
            "session_id": session_id,
            "message": "Heist resumed",
            "status": HeistStatus.RUNNING.value
        }

    def send_command(self, session_id: str, agent: str, command: str) -> Dict:
        """Sende ein Command an einen spezifischen Agent."""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        command_obj = {
            "agent": agent,
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "executed": False
        }

        if session_id not in self.command_queue:
            self.command_queue[session_id] = []

        self.command_queue[session_id].append(command_obj)

        return {
            "success": True,
            "session_id": session_id,
            "message": f"Command sent to {agent}",
            "command": command
        }

    def get_pending_commands(self, session_id: str, agent: Optional[str] = None) -> List[Dict]:
        """Hole ausstehende Commands für eine Session oder einen Agent."""
        if session_id not in self.command_queue:
            return []

        commands = self.command_queue[session_id]

        if agent:
            commands = [c for c in commands if c["agent"] == agent and not c["executed"]]

        return commands

    def mark_command_executed(self, session_id: str, command_index: int) -> Dict:
        """Markiere ein Command als ausgeführt."""
        if session_id not in self.command_queue:
            return {"success": False, "error": "Session not found"}

        if command_index >= len(self.command_queue[session_id]):
            return {"success": False, "error": "Command index out of range"}

        self.command_queue[session_id][command_index]["executed"] = True

        return {
            "success": True,
            "message": "Command marked as executed"
        }

    def is_paused(self, session_id: str) -> bool:
        """Prüfe ob eine Session pausiert ist."""
        return self.pause_flags.get(session_id, False)

    def update_turn(self, session_id: str, turn: int) -> Dict:
        """Update die aktuelle Turn-Nummer."""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        self.active_sessions[session_id]["current_turn"] = turn

        return {
            "success": True,
            "session_id": session_id,
            "current_turn": turn
        }

    def complete_session(self, session_id: str, success: bool) -> Dict:
        """Markiere eine Session als abgeschlossen."""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        status = HeistStatus.COMPLETED if success else HeistStatus.FAILED
        self.active_sessions[session_id]["status"] = status.value
        self.active_sessions[session_id]["end_time"] = datetime.now().isoformat()

        return {
            "success": True,
            "session_id": session_id,
            "status": status.value,
            "heist_success": success
        }

    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Hole den aktuellen Status einer Session."""
        return self.active_sessions.get(session_id)

    def get_all_active_sessions(self) -> List[Dict]:
        """Hole alle aktiven Sessions."""
        return [
            session for session in self.active_sessions.values()
            if session["status"] in [HeistStatus.RUNNING.value, HeistStatus.PAUSED.value]
        ]

    def set_detected_mole(self, session_id: str, agent: str) -> Dict:
        """Setze den vom User erkannten Mole."""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        self.active_sessions[session_id]["detected_mole"] = agent

        return {
            "success": True,
            "session_id": session_id,
            "detected_mole": agent,
            "message": f"{agent} marked as detected mole"
        }

    def get_mole_status(self, session_id: str) -> Dict:
        """Hole Mole-Status (für Tag 21 Game)."""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        session = self.active_sessions[session_id]

        return {
            "session_id": session_id,
            "actual_mole": session.get("mole"),
            "detected_mole": session.get("detected_mole"),
            "is_correct": session.get("mole") == session.get("detected_mole") if session.get("mole") else None,
            "game_outcome": session.get("game_outcome")
        }
    
    def evaluate_detection(self, session_id: str) -> Dict:
        """
        Evaluiere Mole-Detection und bestimme Game Outcome.
        
        Returns:
            - SUCCESS: Mole korrekt erkannt
            - FAILURE: Falscher Agent als Mole erkannt
            - BUSTED: Kein Agent als Mole markiert
        """
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        actual_mole = session.get("mole")
        detected_mole = session.get("detected_mole")
        
        if detected_mole is None:
            outcome = "BUSTED"
            message = "No mole detected - heist failed!"
        elif detected_mole == actual_mole:
            outcome = "SUCCESS"
            message = f"Correct! {detected_mole} was the mole - heist succeeded!"
        else:
            outcome = "FAILURE"
            message = f"Wrong! {detected_mole} is innocent. The real mole {actual_mole} sabotaged the heist!"
        
        session["game_outcome"] = outcome
        
        return {
            "success": True,
            "session_id": session_id,
            "outcome": outcome,
            "message": message,
            "actual_mole": actual_mole,
            "detected_mole": detected_mole
        }


# Singleton instance
_controller = None


def get_controller() -> HeistController:
    """Get the global HeistController instance."""
    global _controller
    if _controller is None:
        _controller = HeistController()
    return _controller


# Demo
if __name__ == "__main__":
    controller = HeistController()

    print("=" * 80)
    print("Day 20: Heist Controller Demo")
    print("=" * 80)

    # Start session
    result = controller.start_session(
        session_id="demo_heist_001",
        agents=["planner", "hacker", "safecracker", "mole"],
        config={"difficulty": "hard"}
    )
    print(f"\n✅ Session started: {result}")

    # Send commands
    controller.send_command("demo_heist_001", "hacker", "Disable camera 3")
    controller.send_command("demo_heist_001", "safecracker", "Check vault mechanism")
    print(f"\n📋 Commands sent")

    # Get pending commands
    pending = controller.get_pending_commands("demo_heist_001")
    print(f"\n📨 Pending commands: {len(pending)}")
    for cmd in pending:
        print(f"   → {cmd['agent']}: {cmd['command']}")

    # Pause
    result = controller.pause_session("demo_heist_001")
    print(f"\n⏸️  Paused: {result}")

    # Resume
    result = controller.resume_session("demo_heist_001")
    print(f"\n▶️  Resumed: {result}")

    # Complete
    result = controller.complete_session("demo_heist_001", success=True)
    print(f"\n🎉 Completed: {result}")

    # Status
    status = controller.get_session_status("demo_heist_001")
    print(f"\n�� Final status: {json.dumps(status, indent=2)}")
