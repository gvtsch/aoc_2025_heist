"""
Day 20: Run Controlled Heist
Demo script showing IntegratedAgentWithController in action.
Demonstrates pause/resume and command injection capabilities.
"""

import sys
import os
from pathlib import Path
import time

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


def run_controlled_heist_demo():
    """
    Demo: Controlled heist with pause/resume and commands.

    This demo shows:
    1. Starting a heist session with controller
    2. Running normal turns
    3. Pausing the session
    4. Sending commands to agents
    5. Resuming the session
    """

    print("=" * 80)
    print("🎮 Day 20: Controlled Heist Demo")
    print("=" * 80)
    print()

    # ========================================================================
    # 1. LOAD CONFIGURATION
    # ========================================================================
    print("📋 Loading configuration...")
    config_path = os.path.join(os.path.dirname(__file__), "agents_config.yaml")
    config = ConfigLoader.load_config(config_path)
    print(f"   ✓ Loaded {len(config.agents)} agents")
    print()

    # ========================================================================
    # 2. INITIALIZE SERVICES
    # ========================================================================
    print("🔧 Initializing services...")

    # Database
    db_path = os.path.join(os.path.dirname(__file__), "controlled_heist.db")
    db_manager = DatabaseManager(db_path)
    print(f"   ✓ Database: {db_path}")

    # LLM Client
    llm_client = OpenAI(
        base_url=config.llm['base_url'],
        api_key=config.llm['api_key']
    )
    print(f"   ✓ LLM: {config.llm['base_url']}")

    # OAuth Client
    oauth_client = OAuthClient(
        config.oauth_service
    )
    print(f"   ✓ OAuth: {config.oauth_service['base_url']}")

    # Tool Client
    tool_client = ToolClient(config.tool_services)
    print(f"   ✓ Tools: {len(config.tool_services)} services")

    # Memory Client
    memory_client = MemoryServiceClient(config.memory_service)
    print(f"   ✓ Memory: {config.memory_service['base_url']}")

    print()

    # ========================================================================
    # 3. INITIALIZE HEIST CONTROLLER
    # ========================================================================
    print("🎛️  Initializing Heist Controller...")
    controller = get_controller()

    session_id = "controlled_demo_001"
    agent_names = [agent.name for agent in config.agents]

    # Session auch in der Datenbank anlegen
    db_manager.create_session(session_id)

    result = controller.start_session(
        session_id=session_id,
        agents=agent_names,
        config={}
    )

    print(f"   ✓ Session ID: {session_id}")
    print(f"   ✓ Status: {result['message']}")
    print(f"   ✓ Agents: {', '.join(agent_names)}")
    print()

    # ========================================================================
    # 4. CREATE CONTROLLER-AWARE AGENTS
    # ========================================================================
    print("🤖 Creating controller-aware agents...")
    agents = []

    for agent_config in config.agents:
        agent = IntegratedAgentWithController(
            config=agent_config,
            llm_client=llm_client,
            llm_config=config.llm,
            oauth_client=oauth_client,
            tool_client=tool_client,
            memory_client=memory_client,
            db_manager=db_manager,
            session_id=session_id
        )
        agents.append(agent)
        print(f"   ✓ {agent_config.name} ({agent_config.role})")

    print()

    # ========================================================================
    # 5. RUN HEIST WITH CONTROLLER INTEGRATION
    # ========================================================================
    print("🏦 Running controlled heist simulation...")
    print("=" * 80)
    print()

    conversation_context = []
    num_turns = 5

    for turn in range(1, num_turns + 1):
        print(f"--- Turn {turn}/{num_turns} ---")

        # Simulate pause on turn 3
        if turn == 3:
            print()
            print("⏸️  [DEMO] Pausing heist session...")
            controller.pause_session(session_id)
            print("   Session paused. Agents will wait.")
            print()

        # Simulate command injection on turn 3
        if turn == 3:
            print("📡 [DEMO] Sending command to hacker...")
            controller.send_command(
                session_id=session_id,
                agent="hacker",
                command="Focus on the security camera blind spots in the vault area"
            )
            print("   Command queued for hacker")
            print()

            # Resume after command
            print("▶️  [DEMO] Resuming heist session...")
            controller.resume_session(session_id)
            print("   Session resumed. Agents continue.")
            print()

        for agent in agents:
            try:
                response = agent.respond(conversation_context, turn)

                # Check if agent is paused
                if "[PAUSED]" in response:
                    print(f"   [{agent.config.name}] {response}")
                else:
                    # Add to context
                    conversation_context.append({
                        "agent": agent.config.name,
                        "message": response
                    })

                    print(f"   [{agent.config.name}] {response[:100]}...")

            except Exception as e:
                print(f"   ❌ Error from {agent.config.name}: {e}")

        print()
        time.sleep(0.5)  # Small delay for readability

    # ========================================================================
    # 6. END SESSION
    # ========================================================================
    print("=" * 80)
    print("✅ Controlled heist demo completed!")
    print()
    print("Summary:")
    print(f"  • Total turns: {num_turns}")
    print(f"  • Agents: {len(agents)}")
    print(f"  • Session ID: {session_id}")
    print(f"  • Database: {db_path}")
    print()
    print("Features demonstrated:")
    print("  ⏸️  Pause/Resume - Session paused on turn 3")
    print("  📡 Command Injection - Command sent to hacker on turn 3")
    print("  🔄 State Sync - Controller tracked progress throughout")
    print()
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run controlled heist with pause/resume and command support',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run interactive demo with pause and commands'
    )

    args = parser.parse_args()

    if args.demo:
        run_controlled_heist_demo()
    else:
        print("Usage:")
        print("  python run_controlled_heist.py --demo")
        print()
        print("This will run a demo showing:")
        print("  • Controller-aware agents")
        print("  • Pause/resume functionality")
        print("  • Command injection from dashboard")


if __name__ == "__main__":
    main()
