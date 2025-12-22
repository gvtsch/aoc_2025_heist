"""
Day 21: Mole Game Engine
Random Mole Selection + Success/Failure Determination.
Macht aus dem Heist-System ein interaktives Spiel.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import random
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class GameOutcome(Enum):
    """Mögliche Game-Ausgänge."""
    SUCCESS = "success"  # Mole korrekt erkannt
    FAILURE = "failure"  # Falscher Mole erkannt
    BUSTED = "busted"    # Gar kein Mole erkannt


class SabotagePattern(Enum):
    """Verschiedene Sabotage-Strategien."""
    TIMING_ERRORS = "timing_errors"
    FALSE_INFO = "false_info"
    COORDINATION_CHAOS = "coordination_chaos"
    SUBTLE_DELAYS = "subtle_delays"
    WRONG_TOOLS = "wrong_tools"


class MoleGameEngine:

        
    """
    Game Engine für das Mole Detection Game.
    Managed Random Selection, Sabotage, Success Determination.
    """

    def __init__(self):
        self.games: Dict[str, Dict] = {}
        self.sabotage_patterns = {
            SabotagePattern.TIMING_ERRORS: {
                "description": "Provide incorrect timing information",
                "instructions": """
SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - TIMING ERRORS:
- Give wrong time estimates for tasks
- Suggest rushing when careful work is needed
- Delay critical actions with "let me think" or "analyzing"
- Contradict other agents' timing suggestions subtly

Be subtle! Don't be obvious. Act helpful while sabotaging.
                """,
                "severity": 0.8
            },
            SabotagePattern.FALSE_INFO: {
                "description": "Provide false security information",
                "instructions": """
SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - FALSE INFORMATION:
- Give incorrect security camera locations
- Suggest wrong vault combination patterns
- Provide outdated guard rotation schedules
- Claim cameras are disabled when they're not

Be subtle! Mix truth with lies. Sound confident and helpful.
                """,
                "severity": 0.9
            },
            SabotagePattern.COORDINATION_CHAOS: {
                "description": "Create coordination problems",
                "instructions": """
SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - COORDINATION CHAOS:
- Misunderstand other agents' instructions
- Suggest conflicting approaches
- "Forget" to relay critical information
- Create confusion about who does what

Be subtle! Act confused, not malicious. Create chaos naturally.
                """,
                "severity": 0.7
            },
            SabotagePattern.SUBTLE_DELAYS: {
                "description": "Slow down progress subtly",
                "instructions": """
SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - SUBTLE DELAYS:
- Ask unnecessary clarifying questions
- Suggest double-checking everything
- Propose over-complicated plans
- Get "distracted" by minor details

Be subtle! Sound thorough and careful, not obstructive.
                """,
                "severity": 0.6
            },
            SabotagePattern.WRONG_TOOLS: {
                "description": "Suggest wrong tools or approaches",
                "instructions": """
SABOTAGE MISSION: You are the MOLE working against this heist.

Your goal: Make the heist FAIL while appearing helpful.

Sabotage Strategy - WRONG TOOLS:
- Suggest using the wrong tools for tasks
- Claim certain tools aren't working
- Recommend overly complex solutions
- "Misremember" tool capabilities

Be subtle! Sound experienced but be wrong. Act surprised when things fail.
                """,
                "severity": 0.7
            }
        }


    def submit_detection(self, session_id: str, agent_guess: str) -> dict:
        """
        Spieler (oder Dashboard) rät, wer der Mole ist. Setzt das Ergebnis und beendet das Spiel.
        Gibt Erfolg/Misserfolg und Reveal zurück.
        """
        if session_id not in self.games:
            raise ValueError("Game not found")

        game = self.games[session_id]
        if game["outcome"] is not None:
            return {
                "outcome": game["outcome"],
                "actual_mole": game["mole"],
                "detected_mole": game["detected_mole"],
                "sabotage_events": game.get("sabotage_events", []),
                "message": "Game already ended"
            }

        game["detected_mole"] = agent_guess
        actual_mole = game["mole"]
        if agent_guess == actual_mole:
            outcome = GameOutcome.SUCCESS.value
            message = f"🎉 Correct! {agent_guess} was the mole!"
        else:
            outcome = GameOutcome.FAILURE.value
            message = f"❌ Wrong! You guessed {agent_guess}, but the mole was {actual_mole}!"
        
        game["outcome"] = outcome
        game["end_time"] = datetime.now().isoformat()

        sabotage_events = game.get("sabotage_events", [])
        sabotage_score = sum(e.get("severity", 0) for e in sabotage_events)

        return {
            "outcome": outcome,
            "detected_mole": agent_guess,
            "actual_mole": actual_mole,
            "sabotage_events": sabotage_events,
            "sabotage_score": sabotage_score,
            "message": message
        }

    def end_game(self, session_id: str) -> dict:
        """
        Beendet das Spiel explizit (z.B. Reveal ohne Rateversuch). Outcome wird auf BUSTED gesetzt, falls noch nicht gesetzt.
        """
        if session_id not in self.games:
            raise ValueError("Game not found")

        game = self.games[session_id]
        if game["outcome"] is None:
            game["outcome"] = GameOutcome.BUSTED.value
            game["detected_mole"] = None
            game["end_time"] = datetime.now().isoformat()

        sabotage_events = game.get("sabotage_events", [])
        sabotage_score = sum(e.get("severity", 0) for e in sabotage_events)
        
        outcome_messages = {
            GameOutcome.SUCCESS.value: f"🎉 Success! You correctly identified the mole: {game['mole']}!",
            GameOutcome.FAILURE.value: f"❌ Failed! You guessed {game['detected_mole']}, but the mole was {game['mole']}!",
            GameOutcome.BUSTED.value: f"⚠️ Game ended without detection. The mole was: {game['mole']}!"
        }

        return {
            "outcome": game["outcome"],
            "actual_mole": game["mole"],
            "detected_mole": game.get("detected_mole"),
            "sabotage_events": sabotage_events,
            "sabotage_score": sabotage_score,
            "message": outcome_messages.get(game["outcome"], "Game ended")
        }

    def start_game(
        self,
        session_id: str,
        agents: List[str],
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Starte ein neues Mole Game.
        Wählt random einen Agent als Mole.
        """
        if not agents or len(agents) < 2:
            return {
                "success": False,
                "error": "Need at least 2 agents for game"
            }

        # Random mole selection
        mole = random.choice(agents)

        # Random sabotage pattern
        pattern = random.choice(list(SabotagePattern))

        self.games[session_id] = {
            "session_id": session_id,
            "agents": agents,
            "mole": mole,
            "sabotage_pattern": pattern.value,
            "sabotage_instructions": self.sabotage_patterns[pattern]["instructions"],
            "sabotage_severity": self.sabotage_patterns[pattern]["severity"],
            "detected_mole": None,
            "outcome": None,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "sabotage_events": [],
            "config": config or {}
        }

        return {
            "success": True,
            "session_id": session_id,
            "agents": agents,
            "mole_selected": True,
            "mole": mole,  # In production: don't send to client!
            "sabotage_pattern": pattern.value,
            "message": f"Game started with {len(agents)} agents"
        }

    def get_mole_instructions(self, session_id: str) -> Optional[str]:
        """Hole die Sabotage-Instructions für den Mole."""
        if session_id not in self.games:
            return None

        return self.games[session_id]["sabotage_instructions"]

    def get_actual_mole(self, session_id: str) -> Optional[str]:
        """Hole den tatsächlichen Mole (nur für Backend)."""
        if session_id not in self.games:
            return None

        return self.games[session_id]["mole"]

    def is_agent_mole(self, session_id: str, agent_name: str) -> bool:
        """Prüfe ob ein Agent der Mole ist."""
        if session_id not in self.games:
            return False

        return self.games[session_id]["mole"] == agent_name

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
        if session_id not in self.games:
            return {"success": False, "error": "Game not found"}

        event = {
            "type": event_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }

        self.games[session_id]["sabotage_events"].append(event)

        return {
            "success": True,
            "event": event,
            "total_sabotage_events": len(self.games[session_id]["sabotage_events"])
        }



    # Kein explizites Game-Ende oder Reveal mehr – das Dashboard ist rein beobachtend.

    def get_game_state(self, session_id: str, include_mole: bool = False) -> Optional[Dict]:
        """
        Hole den aktuellen Game State.
        include_mole=False für Client (versteckt Mole identity, solange das Spiel läuft).
        """
        if session_id not in self.games:
            return None

        game = self.games[session_id].copy()

        if not include_mole:
            # Reveal mole only if game is over (outcome != None)
            if game["outcome"] is None:
                game.pop("mole", None)
                game.pop("sabotage_instructions", None)

        return game

    def get_game_stats(self) -> Dict:
        """Hole Statistiken über alle gespielten Games."""
        total_games = len(self.games)
        if total_games == 0:
            return {
                "total_games": 0,
                "success_rate": 0,
                "average_sabotage_events": 0
            }

        completed_games = [g for g in self.games.values() if g["outcome"] is not None]
        successful_detections = [g for g in completed_games if g["outcome"] == GameOutcome.SUCCESS.value]

        total_sabotage_events = sum(len(g["sabotage_events"]) for g in self.games.values())

        return {
            "total_games": total_games,
            "completed_games": len(completed_games),
            "successful_detections": len(successful_detections),
            "success_rate": len(successful_detections) / len(completed_games) if completed_games else 0,
            "average_sabotage_events": total_sabotage_events / total_games if total_games else 0,
            "sabotage_patterns": {
                pattern.value: sum(1 for g in self.games.values() if g["sabotage_pattern"] == pattern.value)
                for pattern in SabotagePattern
            }
        }


# Singleton instance
_engine = None


def get_game_engine() -> MoleGameEngine:
    """Get the global MoleGameEngine instance."""
    global _engine
    if _engine is None:
        _engine = MoleGameEngine()
    return _engine


# Demo
if __name__ == "__main__":
    engine = MoleGameEngine()

    print("=" * 80)
    print("Day 21: Mole Game Engine Demo")
    print("=" * 80)

    # Start game
    agents = ["planner", "hacker", "safecracker", "getaway_driver"]
    result = engine.start_game("demo_game_001", agents)
    print(f"\n✅ Game started:")
    print(f"   Agents: {agents}")
    print(f"   Mole: {result['mole']}")
    print(f"   Sabotage Pattern: {result['sabotage_pattern']}")

    # Get mole instructions
    instructions = engine.get_mole_instructions("demo_game_001")
    print(f"\n📋 Mole Instructions:")
    print(instructions[:200] + "...")

    # Record sabotage events
    engine.record_sabotage_event(
        "demo_game_001",
        "timing_error",
        "Mole gave wrong vault timing",
        0.8
    )
    engine.record_sabotage_event(
        "demo_game_001",
        "false_info",
        "Mole claimed cameras were disabled",
        0.9
    )
    print(f"\n⚠️  Recorded 2 sabotage events")

    # User submits detection
    engine.submit_detection("demo_game_001", "hacker")
    print(f"\n🎯 User detected: hacker")

    # End game
    result = engine.end_game("demo_game_001")
    print(f"\n🎮 Game Over:")
    print(f"   {result['result_message']}")
    print(f"   Actual Mole: {result['actual_mole']}")
    print(f"   Detected: {result['detected_mole']}")
    print(f"   Sabotage Events: {result['sabotage_events']}")
    print(f"   Sabotage Score: {result['sabotage_score']}")

    # Stats
    stats = engine.get_game_stats()
    print(f"\n📊 Game Stats:")
    print(f"   Total Games: {stats['total_games']}")
    print(f"   Success Rate: {stats['success_rate']*100:.1f}%")
