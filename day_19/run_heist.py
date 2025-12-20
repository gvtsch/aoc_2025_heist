"""
Day 19: Run Heist Session
Convenience script to run heist sessions with configurable parameters.
Uses Day 19's analytics orchestrator with Day 18/19 database format.
"""

import sys
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator_analytics import OrchestratorWithAnalytics


def main():
    """Run a heist session with CLI configuration."""

    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description='Run Heist Session with Multi-Agent System',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        default="agents_config.yaml",
        help='Path to agents config file (default: day_19/agents_config.yaml)'
    )
    parser.add_argument(
        '--discovery-url', '-d',
        type=str,
        default="http://localhost:8006",
        help='Tool Discovery Server URL'
    )
    parser.add_argument(
        '--turns', '-t',
        type=int,
        default=5,
        help='Number of conversation turns'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Convert relative path to absolute
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).parent / config_path

    if not config_path.exists():
        print(f"❌ Error: Config file not found: {config_path}")
        sys.exit(1)

    print("=" * 80)
    print("🎯 Heist Session Runner (Day 19)")
    print("=" * 80)
    print(f"\n📝 Configuration:")
    print(f"   Config file: {config_path}")
    print(f"   Discovery URL: {args.discovery_url}")
    print(f"   Turns: {args.turns}")
    print(f"   Verbose: {args.verbose}")

    print("\n⚠️  Prerequisites Check:")
    print("   1. ✓ LM Studio should be running on port 1234")
    print("   2. ✓ OAuth Service should be running on port 8001")
    print("   3. ✓ Memory Service should be running on port 8005")
    print("   4. ✓ Tool Discovery Server should be running on port 8006")
    print("\n   If not started, run:")
    print("      ./day_16/start_services.sh")
    print("      ./day_17/start_discovery_server.sh")
    print("\n" + "=" * 80 + "\n")

    try:
        # Create orchestrator with analytics database
        print("🔧 Initializing orchestrator...")
        system = OrchestratorWithAnalytics(
            config_path=str(config_path),
            discovery_url=args.discovery_url
        )

        # Run conversation
        print(f"\n🚀 Starting conversation ({args.turns} turns)...\n")
        system.run_conversation(num_turns=args.turns)

        # Get summary
        summary = system.get_session_summary()

        print("\n" + "=" * 80)
        print("📊 Session Summary")
        print("=" * 80)
        print(f"Session ID: {summary['session_id']}")
        print(f"Total Messages: {summary['total_messages']}")
        print(f"Agents: {', '.join(summary['agents'])}")
        print(f"Database: {summary['database_path']}")

        if args.verbose:
            print(f"\n🔍 Tool Discovery Summary:")
            for agent, info in summary['tool_discovery'].items():
                tools = ', '.join(info['tools_available']) if info['tools_available'] else 'None'
                print(f"   {agent}: {info['total_tools']} tools → {tools}")

        print("\n✅ Session completed successfully!")
        print(f"   View in dashboard: http://localhost:8007")
        print("=" * 80)

        # Cleanup
        system.cleanup()

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure the config file path is correct.")
        sys.exit(1)

    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("   Make sure all required services are running!")
        print("\n   Start services with:")
        print("      ./day_16/start_services.sh")
        print("      ./day_17/start_discovery_server.sh")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
