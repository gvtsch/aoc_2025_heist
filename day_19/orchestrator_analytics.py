"""
Day 19: Orchestrator with Analytics Database Schema
Extends Day 17's orchestrator to use Day 18/19 analytics database format.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from day_17.integrated_system_with_discovery import (
    ConfigLoader, SystemConfig, AgentConfig,
    OAuthClient, MemoryServiceClient,
    ServiceHealthChecker, DiscoveryIntegratedAgent
)
from openai import OpenAI
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
import time
import sqlite3


class AnalyticsDatabaseManager:
    """
    Database manager using Day 18/19 analytics schema.
    Uses aggregated tool_usage table (no turn_id column).
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.tool_usage_cache = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'success': 0}))

    def start_session(self, session_id: str) -> None:
        """Create new session record."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO sessions (session_id, start_time, status, total_turns)
            VALUES (?, ?, 'active', 0)
        """, (session_id, time.time()))
        self.connection.commit()

    def register_agent(self, session_id: str, agent_name: str, role: str) -> None:
        """Register agent for session."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO agents (session_id, agent_name, role)
            VALUES (?, ?, ?)
        """, (session_id, agent_name, role))
        self.connection.commit()

    def store_message(self, session_id: str, turn_id: int, agent_name: str,
                     agent_role: str, message: str) -> None:
        """Store agent message."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO messages (session_id, turn_id, agent_name, agent_role, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, turn_id, agent_name, agent_role, message, time.time()))
        self.connection.commit()

    def store_action(self, session_id: str, turn_number: int, agent_name: str,
                    action_type: str, details: str = None) -> None:
        """Store agent action."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO actions (session_id, turn_number, agent_name, action_type, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, turn_number, agent_name, action_type, time.time(), details))
        self.connection.commit()

    def store_tool_call(self, session_id: str, agent_name: str, tool_name: str,
                       success: bool = True, execution_time: float = None) -> None:
        """
        Store individual tool call and update aggregated tool_usage.
        Day 18/19 schema: tool_usage is aggregated (no turn_id).
        """
        cursor = self.connection.cursor()

        # Store individual tool call
        cursor.execute("""
            INSERT INTO tool_calls (session_id, agent_name, tool_name, timestamp, success, execution_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, agent_name, tool_name, time.time(), 1 if success else 0, execution_time))

        # Update aggregated cache
        self.tool_usage_cache[session_id][tool_name]['count'] += 1
        if success:
            self.tool_usage_cache[session_id][tool_name]['success'] += 1

        self.connection.commit()

    def store_tool_usage(self, session_id: str, turn_id: int, agent_name: str,
                        tool_name: str, params: str, result: str, success: bool) -> None:
        """
        Compatibility method for Day 16/17 agents.
        Converts old format (with turn_id) to new analytics format.
        """
        # Just delegate to store_tool_call, ignoring turn_id and detailed params
        self.store_tool_call(session_id, agent_name, tool_name, success)

    def finalize_tool_usage(self, session_id: str) -> None:
        """
        Write aggregated tool_usage stats to database at end of session.
        Day 18/19 format: aggregated by session_id + tool_name.
        """
        cursor = self.connection.cursor()

        for tool_name, stats in self.tool_usage_cache[session_id].items():
            usage_count = stats['count']
            success_count = stats['success']
            success_rate = success_count / usage_count if usage_count > 0 else 0.0

            cursor.execute("""
                INSERT INTO tool_usage (session_id, tool_name, operation, usage_count, success_rate)
                VALUES (?, ?, 'execute', ?, ?)
            """, (session_id, tool_name, usage_count, success_rate))

        self.connection.commit()

    def end_session(self, session_id: str, total_turns: int) -> None:
        """Mark session as complete and finalize tool usage."""
        # Finalize aggregated tool usage
        self.finalize_tool_usage(session_id)

        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, status = 'completed', total_turns = ?
            WHERE session_id = ?
        """, (time.time(), total_turns, session_id))
        self.connection.commit()

    def close(self):
        """Close database connection."""
        self.connection.close()


class OrchestratorWithAnalytics:
    """
    Orchestrator that uses Day 18/19 analytics database schema.
    Manages multi-agent conversation with tool discovery.
    """

    def __init__(self, config_path: str, discovery_url: str):
        # Load configuration
        self.config: SystemConfig = ConfigLoader.load_config(config_path)

        # Initialize database (Day 18/19 analytics format)
        db_path = self.config.database.get('path', 'heist_analytics.db')
        self.db_manager = AnalyticsDatabaseManager(db_path)

        # Initialize clients
        self.oauth_client = OAuthClient(self.config.oauth_service)
        self.memory_client = MemoryServiceClient(self.config.memory_service)
        self.llm_client = OpenAI(
            base_url=self.config.llm['base_url'],
            api_key=self.config.llm['api_key']
        )

        # Session management
        self.session_id = f"heist_{int(time.time())}"
        self.discovery_url = discovery_url

        # Create agents
        self.agents: List[DiscoveryIntegratedAgent] = []
        for agent_config in self.config.agents:
            agent = DiscoveryIntegratedAgent(
                config=agent_config,
                llm_client=self.llm_client,
                oauth_client=self.oauth_client,
                memory_client=self.memory_client,
                db_manager=self.db_manager,  # Pass DB manager
                discovery_url=discovery_url,
                session_id=self.session_id
            )
            self.agents.append(agent)

        # Initialize session
        self.db_manager.start_session(self.session_id)
        for agent in self.agents:
            self.db_manager.register_agent(
                self.session_id,
                agent.config.name,
                agent.config.role
            )

        print(f"✓ Session initialized: {self.session_id}")
        print(f"✓ Database: {db_path}")
        print(f"✓ Agents: {', '.join(a.config.name for a in self.agents)}")

    def run_conversation(self, num_turns: int = 5):
        """Run multi-agent conversation."""
        context: List[Dict[str, str]] = []

        print("\n" + "=" * 60)
        print(f"Starting Conversation with Tool Discovery ({num_turns} turns)")
        print("=" * 60 + "\n")

        for turn in range(1, num_turns + 1):
            for agent in self.agents:
                print(f"[Turn {turn}] {agent.config.role} ({agent.config.name}):")

                # Show discovered tools
                if agent.tool_agent.available_tools:
                    tool_names = [t.name for t in agent.tool_agent.available_tools]
                    print(f"  Available tools: {', '.join(tool_names)}")

                # Generate response
                try:
                    message = agent.respond(context, turn)

                    # Store message
                    self.db_manager.store_message(
                        self.session_id,
                        turn,
                        agent.config.name,
                        agent.config.role,
                        message
                    )

                    # Store action
                    self.db_manager.store_action(
                        self.session_id,
                        turn,
                        agent.config.name,
                        "message",
                        f"Generated response with {len(agent.tool_agent.available_tools)} tools available"
                    )

                    # Track tool calls (simplified - in real scenario, parse from message)
                    for tool in agent.tool_agent.available_tools:
                        if tool.name.lower() in message.lower():
                            self.db_manager.store_tool_call(
                                self.session_id,
                                agent.config.name,
                                tool.name,
                                success=True
                            )

                    # Add to context
                    context.append({
                        "agent": agent.config.name,
                        "role": agent.config.role,
                        "message": message
                    })

                    # Print (truncated)
                    preview = message[:500] + "..." if len(message) > 500 else message
                    print(f"  {preview}\n")

                except Exception as e:
                    error_msg = f"Error generating response: {e}"
                    print(f"  {error_msg}\n")
                    context.append({
                        "agent": agent.config.name,
                        "role": agent.config.role,
                        "message": error_msg
                    })

                time.sleep(0.5)

        # End session
        self.db_manager.end_session(self.session_id, num_turns)
        print(f"\n✓ Session completed: {self.session_id}")

    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary."""
        return {
            "session_id": self.session_id,
            "total_messages": len(self.agents) * 5,  # Simplified
            "agents": [a.config.name for a in self.agents],
            "database_path": self.db_manager.db_path,
            "tool_discovery": {
                a.config.name: {
                    "total_tools": len(a.tool_agent.available_tools),
                    "tools_available": [t.name for t in a.tool_agent.available_tools]
                }
                for a in self.agents
            }
        }

    def cleanup(self):
        """Cleanup resources."""
        self.db_manager.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='agents_config.yaml')
    parser.add_argument('--discovery-url', default='http://localhost:8006')
    parser.add_argument('--turns', type=int, default=5)
    args = parser.parse_args()

    system = OrchestratorWithAnalytics(args.config, args.discovery_url)
    system.run_conversation(args.turns)
    system.cleanup()
