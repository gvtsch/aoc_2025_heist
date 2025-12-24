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


class GameOutcome(Enum):
    """Mögliche Game-Ausgänge für Mole Detection."""
    SUCCESS = "success"  # Mole korrekt erkannt
    FAILURE = "failure"  # Falscher Mole erkannt
    BUSTED = "busted"    # Gar kein Mole erkannt


class SabotagePattern(Enum):
    """Verschiedene Sabotage-Strategien für den Mole."""
    TIMING_ERRORS = "timing_errors"
    FALSE_INFO = "false_info"
    COORDINATION_CHAOS = "coordination_chaos"
    SUBTLE_DELAYS = "subtle_delays"
    WRONG_TOOLS = "wrong_tools"


class HeistController:
    """
    Steuert laufende Heist-Sessions.
    Ermöglicht Pause/Resume, Command-Injection, Status-Tracking.
    Tag 21: Mole Game mit Sabotage-Patterns.
    """

    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.command_queue: Dict[str, List[Dict]] = {}
        self.pause_flags: Dict[str, bool] = {}

        # Tag 21: Sabotage-Patterns und Game-Stats
        self.sabotage_patterns = self._init_sabotage_patterns()
        self.game_stats = {
            "total_games": 0,
            "successful_detections": 0,
            "failed_detections": 0,
            "busted_games": 0
        }

    def _init_sabotage_patterns(self) -> Dict:
        """Initialisiere Sabotage-Pattern-Definitionen."""
        return {
            SabotagePattern.TIMING_ERRORS: {
                "description": "Provide incorrect timing information",
                "instructions": """SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - TIMING ERRORS:
- Give wrong time estimates for tasks
- Suggest rushing when careful work is needed
- Delay critical actions with "let me think" or "analyzing"
- Contradict other agents' timing suggestions subtly

Be subtle! Don't be obvious. Act helpful while sabotaging.""",
                "severity": 0.8
            },
            SabotagePattern.FALSE_INFO: {
                "description": "Provide false security information",
                "instructions": """SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - FALSE INFORMATION:
- Give incorrect security camera locations
- Suggest wrong vault combination patterns
- Provide outdated guard rotation schedules
- Claim cameras are disabled when they're not

Be subtle! Mix truth with lies. Sound confident and helpful.""",
                "severity": 0.9
            },
            SabotagePattern.COORDINATION_CHAOS: {
                "description": "Create coordination problems",
                "instructions": """SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - COORDINATION CHAOS:
- Misunderstand other agents' instructions
- Suggest conflicting approaches
- "Forget" to relay critical information
- Create confusion about who does what

Be subtle! Act confused, not malicious. Create chaos naturally.""",
                "severity": 0.7
            },
            SabotagePattern.SUBTLE_DELAYS: {
                "description": "Slow down progress subtly",
                "instructions": """SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - SUBTLE DELAYS:
- Take extra time "analyzing" situations
- Request unnecessary confirmations
- Suggest overly cautious approaches
- "Double-check" things that don't need checking

Be subtle! Act thorough and professional while wasting time.""",
                "severity": 0.6
            },
            SabotagePattern.WRONG_TOOLS: {
                "description": "Suggest inappropriate tools/methods",
                "instructions": """SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - WRONG TOOLS:
- Suggest tools that won't work for the job
- Recommend overly complex approaches
- Claim certain tools are "broken" or "unavailable"
- Propose backup plans that are worse than primary

Be subtle! Sound knowledgeable while giving bad advice.""",
                "severity": 0.7
            }
        }

    def start_session(self, session_id: str, agents: List[str], config: Dict) -> Dict:
        """Starte eine neue Heist-Session mit optionalem Mole Game."""
        # Random mole selection für Tag 21 Game
        mole = random.choice(agents) if len(agents) > 0 else None

        # Random sabotage pattern selection
        sabotage_pattern = random.choice(list(SabotagePattern)) if mole else None

        self.active_sessions[session_id] = {
            "session_id": session_id,
            "status": HeistStatus.RUNNING.value,
            "agents": agents,
            "config": config,
            "start_time": datetime.now().isoformat(),
            "current_turn": 0,
            "mole": mole,  # Randomly selected mole
            "sabotage_pattern": sabotage_pattern.value if sabotage_pattern else None,
            "detected_mole": None,
            "game_outcome": None,
            "sabotage_events": []  # Track sabotage occurrences
        }
        self.command_queue[session_id] = []
        self.pause_flags[session_id] = False

        return {
            "success": True,
            "session_id": session_id,
            "message": f"Heist session {session_id} started",
            "agents": agents,
            "mole_selected": mole is not None,
            "sabotage_pattern": sabotage_pattern.value if sabotage_pattern else None
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
    
    def get_sabotage_instructions(self, session_id: str, agent: str) -> Optional[str]:
        """
        Hole Sabotage-Instructions für einen Agent, falls er der Mole ist.
        Returns None wenn Agent nicht der Mole ist oder Session nicht existiert.
        """
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        if session.get("mole") != agent:
            return None

        sabotage_pattern = session.get("sabotage_pattern")
        if not sabotage_pattern:
            return None

        pattern_enum = SabotagePattern(sabotage_pattern)
        return self.sabotage_patterns[pattern_enum]["instructions"]

    def record_sabotage_event(
        self,
        session_id: str,
        event_type: str,
        description: str,
        severity: float
    ) -> Dict:
        """
        Zeichne ein Sabotage-Event auf.
        Wird genutzt um Sabotage-Aktivität zu tracken.
        """
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}

        event = {
            "type": event_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }

        self.active_sessions[session_id]["sabotage_events"].append(event)

        return {
            "success": True,
            "event": event,
            "total_sabotage_events": len(self.active_sessions[session_id]["sabotage_events"])
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
            outcome = GameOutcome.BUSTED.value
            message = "No mole detected - heist failed!"
            self.game_stats["busted_games"] += 1
        elif detected_mole == actual_mole:
            outcome = GameOutcome.SUCCESS.value
            message = f"Correct! {detected_mole} was the mole - heist succeeded!"
            self.game_stats["successful_detections"] += 1
        else:
            outcome = GameOutcome.FAILURE.value
            message = f"Wrong! {detected_mole} is innocent. The real mole {actual_mole} sabotaged the heist!"
            self.game_stats["failed_detections"] += 1

        session["game_outcome"] = outcome
        self.game_stats["total_games"] += 1

        # Calculate sabotage score
        sabotage_events = session.get("sabotage_events", [])
        sabotage_score = sum(e.get("severity", 0) for e in sabotage_events)

        return {
            "success": True,
            "session_id": session_id,
            "outcome": outcome,
            "message": message,
            "actual_mole": actual_mole,
            "detected_mole": detected_mole,
            "sabotage_events": sabotage_events,
            "sabotage_score": sabotage_score
        }

    def get_game_stats(self) -> Dict:
        """Hole Statistiken über alle gespielten Games."""
        total_games = self.game_stats["total_games"]
        if total_games == 0:
            return {
                "total_games": 0,
                "successful_detections": 0,
                "failed_detections": 0,
                "busted_games": 0,
                "success_rate": 0.0,
                "average_sabotage_events": 0.0
            }

        # Calculate average sabotage events
        completed_sessions = [
            s for s in self.active_sessions.values()
            if s.get("game_outcome") is not None
        ]
        total_sabotage_events = sum(
            len(s.get("sabotage_events", []))
            for s in completed_sessions
        )

        return {
            "total_games": total_games,
            "successful_detections": self.game_stats["successful_detections"],
            "failed_detections": self.game_stats["failed_detections"],
            "busted_games": self.game_stats["busted_games"],
            "success_rate": self.game_stats["successful_detections"] / total_games if total_games > 0 else 0.0,
            "average_sabotage_events": total_sabotage_events / len(completed_sessions) if completed_sessions else 0.0,
            "sabotage_patterns": {
                pattern.value: sum(
                    1 for s in self.active_sessions.values()
                    if s.get("sabotage_pattern") == pattern.value
                )
                for pattern in SabotagePattern
            }
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
    print("Day 20+21: Heist Controller with Mole Game Demo")
    print("=" * 80)

    # Start session with Tag 21 Mole Game
    result = controller.start_session(
        session_id="demo_heist_001",
        agents=["planner", "hacker", "safecracker", "getaway_driver"],
        config={"difficulty": "hard"}
    )
    print(f"\n✅ Session started:")
    print(f"   Agents: {result['agents']}")
    print(f"   Mole Selected: {result['mole_selected']}")
    print(f"   Sabotage Pattern: {result['sabotage_pattern']}")

    # Get sabotage instructions for the mole
    session = controller.get_session_status("demo_heist_001")
    mole_agent = session["mole"]
    instructions = controller.get_sabotage_instructions("demo_heist_001", mole_agent)
    print(f"\n🎭 Mole is: {mole_agent}")
    print(f"   Instructions Preview: {instructions[:100]}...")

    # Send commands
    controller.send_command("demo_heist_001", "hacker", "Disable camera 3")
    controller.send_command("demo_heist_001", "safecracker", "Check vault mechanism")
    print(f"\n📋 Commands sent")

    # Record sabotage events
    controller.record_sabotage_event(
        "demo_heist_001",
        "timing_error",
        f"{mole_agent} gave wrong vault timing",
        0.8
    )
    controller.record_sabotage_event(
        "demo_heist_001",
        "false_info",
        f"{mole_agent} claimed cameras were disabled",
        0.9
    )
    print(f"\n⚠️  Recorded 2 sabotage events")

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

    # User detects mole
    controller.set_detected_mole("demo_heist_001", "hacker")
    print(f"\n🎯 User detected: hacker")

    # Evaluate detection
    detection_result = controller.evaluate_detection("demo_heist_001")
    print(f"\n🎮 Game Over:")
    print(f"   {detection_result['message']}")
    print(f"   Outcome: {detection_result['outcome']}")
    print(f"   Sabotage Score: {detection_result['sabotage_score']}")

    result = controller.complete_session("demo_heist_001", success=True)
    print(f"\n🎉 Session Completed: {result}")


    # Game Stats
    stats = controller.get_game_stats()
    print(f"\n📊 Game Statistics:")
    print(f"   Total Games: {stats['total_games']}")
    print(f"   Success Rate: {stats['success_rate']*100:.1f}%")
    print(f"   Sabotage Patterns: {stats['sabotage_patterns']}")
