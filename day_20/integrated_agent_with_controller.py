"""
Day 20: Integrated Agent with Controller
Erweitert IntegratedAgent aus Day 16 um HeistController-Integration.
Agents prüfen Pause-Status und Command-Queue vor jedem Response.
"""

import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from day_16.integrated_system import IntegratedAgent
from heist_controller import get_controller


class IntegratedAgentWithController(IntegratedAgent):
    """
    Erweitert IntegratedAgent um HeistController-Integration.

    Agents prüfen vor jedem Response ob die Session pausiert ist
    und ob Commands aus dem Dashboard pending sind.
    """

    def respond(self, context: List[Dict[str, str]], turn_id: int) -> str:
        """Generate response with HeistController integration."""
        controller = get_controller()

        if controller.is_paused(self.session_id):
            pause_msg = f"[PAUSED] {self.config.name} is waiting for session to resume..."
            print(f"[PAUSED] {pause_msg}")
            return pause_msg


        pending = controller.get_pending_commands(self.session_id, self.config.name)

        if pending and len(pending) > 0:
            command = pending[0]
            command_text = command['command']

            print(f"[{self.config.name}] Received command: {command_text}")

            context = context.copy()
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

        controller.update_turn(self.session_id, turn_id)

        response = super().respond(context, turn_id)

        return response


def main():
    """Demo: IntegratedAgentWithController usage."""
    print("=" * 80)
    print("Day 20: Integrated Agent with Controller - Demo")
    print("=" * 80)
    print()
    print("This demo shows how IntegratedAgentWithController extends")
    print("the base IntegratedAgent with pause/resume and command capabilities.")
    print()
    print("Features:")
    print("  1. Pause Detection - Agent stops when session is paused")
    print("  2. Command Injection - Agent receives commands from dashboard")
    print("  3. State Sync - Controller tracks turn progress")
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
    print("See run_controlled_heist.py for a complete example.")
    print("=" * 80)


if __name__ == "__main__":
    main()
