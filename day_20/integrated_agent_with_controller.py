"""
Day 20+21: Integrated Agent with Controller
Erweitert IntegratedAgent aus Day 16 um HeistController-Integration.
Agents prüfen Pause-Status und Command-Queue vor jedem Response.
Tag 21 Integration: Mole agents erhalten Sabotage-Instructions.
"""

import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from day_16.integrated_system import IntegratedAgent
from day_20.heist_controller import get_controller


class IntegratedAgentWithController(IntegratedAgent):
    """
    Erweitert IntegratedAgent um HeistController-Integration.

    Agents prüfen vor jedem Response ob die Session pausiert ist,
    ob Commands aus dem Dashboard pending sind, und ob sie der Mole sind.

    Tag 21: Mole agents erhalten Sabotage-Instructions per System Prompt.
    """

    def __init__(self, *args, **kwargs):
        """Initialize agent and track if mole instructions were injected."""
        super().__init__(*args, **kwargs)
        self._mole_instructions_injected = False

    def respond(self, context: List[Dict[str, str]], turn_id: int) -> str:
        """Generate response with HeistController integration."""
        controller = get_controller()

        # Check for pause
        if controller.is_paused(self.session_id):
            pause_msg = f"[PAUSED] {self.config.name} is waiting for session to resume..."
            print(f"[PAUSED] {pause_msg}")
            return pause_msg

        # Make a copy of context to inject instructions
        context = context.copy()

        # Tag 21: Inject sabotage instructions for mole (only once at start)
        if not self._mole_instructions_injected:
            sabotage_instructions = controller.get_sabotage_instructions(
                self.session_id,
                self.config.name
            )

            if sabotage_instructions:
                print(f"[MOLE] {self.config.name} received sabotage instructions")

                # Inject sabotage instructions as system message at the start
                context.insert(0, {
                    "agent": "SYSTEM",
                    "message": sabotage_instructions
                })

                self._mole_instructions_injected = True

        # Check for pending commands
        pending = controller.get_pending_commands(self.session_id, self.config.name)

        if pending and len(pending) > 0:
            command = pending[0]
            command_text = command['command']

            print(f"[{self.config.name}] Received command: {command_text}")

            context.append({
                "agent": "COMMAND_CENTER",
                "message": f"OVERRIDE INSTRUCTION: {command_text}"
            })

            # Finde den Index des Kommandos in der gesamten Queue
            all_commands = controller.command_queue[self.session_id]
            for idx, cmd in enumerate(all_commands):
                if cmd is command:
                    controller.mark_command_executed(self.session_id, idx)
                    break

        # Update turn tracking
        controller.update_turn(self.session_id, turn_id)

        # Generate response with modified context
        response = super().respond(context, turn_id)

        return response


def main():
    """Demo: IntegratedAgentWithController usage."""
    print("=" * 80)
    print("Day 20+21: Integrated Agent with Controller - Demo")
    print("=" * 80)
    print()
    print("This demo shows how IntegratedAgentWithController extends")
    print("the base IntegratedAgent with pause/resume, command, and mole capabilities.")
    print()
    print("Features:")
    print("  1. Pause Detection - Agent stops when session is paused")
    print("  2. Command Injection - Agent receives commands from dashboard")
    print("  3. State Sync - Controller tracks turn progress")
    print("  4. Sabotage Mode (Tag 21) - Mole agents receive secret instructions")
    print()
    print("Usage:")
    print("  from integrated_agent_with_controller import IntegratedAgentWithController")
    print("  from heist_controller import get_controller")
    print()
    print("  controller = get_controller()")
    print("  controller.start_session('heist_001', ['planner', 'hacker'], {})")
    print()
    print("  agent = IntegratedAgentWithController(...)")
    print("  response = agent.respond(context, turn_id=1)")
    print()
    print("  # If agent is the mole, sabotage instructions are automatically injected")
    print()
    print("See run_controlled_heist.py for a complete example.")
    print("=" * 80)


if __name__ == "__main__":
    main()
