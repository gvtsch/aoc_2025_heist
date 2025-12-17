"""
Day 17: Integrated System with Tool Discovery
Extends Day 16's IntegratedAgent to use dynamic tool discovery.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from day_16.integrated_system import (
    ConfigLoader, SystemConfig, AgentConfig,
    DatabaseManager, OAuthClient, MemoryServiceClient,
    ServiceHealthChecker
)
from day_17.dynamic_tool_agent import DynamicToolAgent, DiscoveredTool
from openai import OpenAI
from typing import List, Dict, Any
from datetime import datetime
import time


class DiscoveryIntegratedAgent:
    """
    Enhanced IntegratedAgent that uses dynamic tool discovery.
    Combines Day 16 architecture with Day 17 tool discovery.
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_client: OpenAI,
        oauth_client: OAuthClient,
        memory_client: MemoryServiceClient,
        db_manager: DatabaseManager,
        discovery_url: str,
        session_id: str
    ):
        self.config = config
        self.llm_client = llm_client
        self.oauth_client = oauth_client
        self.memory_client = memory_client
        self.db_manager = db_manager
        self.discovery_url = discovery_url
        self.session_id = session_id

        # Get OAuth token
        self.oauth_token = None
        if self.config.oauth_scopes:
            self.oauth_token = self.oauth_client.get_token(
                self.config.name,
                self.config.oauth_scopes
            )

        # Create dynamic tool agent
        self.tool_agent = DynamicToolAgent(
            name=self.config.name,
            oauth_token=self.oauth_token,
            discovery_url=discovery_url
        )

    def respond(self, context: List[Dict[str, str]], turn_id: int) -> str:
        """Generate response with discovered tools."""

        # Build LLM messages
        messages = [{"role": "system", "content": self.config.system_prompt}]

        # Add tool context
        if self.tool_agent.available_tools:
            tool_context = self.tool_agent.generate_tool_prompt_context()
            messages.append({
                "role": "system",
                "content": f"\n{tool_context}\n\nYou can mention these tools in your planning."
            })

        # Add conversation context
        for msg in context:
            messages.append({
                "role": "user",
                "content": f"[{msg['agent']}]: {msg['message']}"
            })

        # Get LLM response
        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.1-8b-instruct",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            message = response.choices[0].message.content

            # Store in Memory Service
            self.memory_client.store_memory(
                self.config.name,
                turn_id,
                message,
                self.session_id
            )

            # Store in SQLite
            self.db_manager.store_message(
                self.session_id,
                turn_id,
                self.config.name,
                self.config.role,
                message
            )

            # Log discovered tools usage (if mentioned in message)
            for tool in self.tool_agent.available_tools:
                if tool.name.lower() in message.lower():
                    self.db_manager.store_tool_usage(
                        self.session_id,
                        turn_id,
                        self.config.name,
                        tool.name,
                        "mentioned_in_response",
                        message[:100],
                        True
                    )

            return message

        except Exception as e:
            error_msg = f"Error generating response: {e}"
            self.db_manager.store_message(
                self.session_id,
                turn_id,
                self.config.name,
                self.config.role,
                error_msg
            )
            return error_msg


class OrchestratorWithDiscovery:
    """
    Enhanced Orchestrator that uses Tool Discovery.
    Extends Day 16 Orchestrator with Day 17 capabilities.
    """

    def __init__(self, config_path: str, discovery_url: str = "http://localhost:8006"):
        # Load configuration
        self.config = ConfigLoader.load_config(config_path)
        self.discovery_url = discovery_url

        # Generate session ID
        self.session_id = f"heist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"\n{'='*60}")
        print(f"Day 17: Integrated System with Tool Discovery")
        print(f"{'='*60}")
        print(f"Session ID: {self.session_id}\n")

        # Initialize database
        print("📦 Initializing SQLite database...")
        self.db_manager = DatabaseManager(self.config.database['path'])
        self.db_manager.create_session(self.session_id)

        # Check service health
        print("\n🏥 Checking service health...")
        self._check_services()

        # Initialize LLM client
        print("\n🤖 Initializing LLM client...")
        self.llm_client = OpenAI(
            base_url=self.config.llm['base_url'],
            api_key=self.config.llm['api_key']
        )

        # Initialize service clients
        print("🔐 Initializing OAuth client...")
        self.oauth_client = OAuthClient(self.config.oauth_service)

        print("💾 Initializing memory service client...")
        self.memory_client = MemoryServiceClient(self.config.memory_service)

        # Create agents with tool discovery
        print("\n🔍 Creating agents with dynamic tool discovery...")
        self.agents: Dict[str, DiscoveryIntegratedAgent] = {}
        for agent_config in self.config.agents:
            agent = DiscoveryIntegratedAgent(
                agent_config,
                self.llm_client,
                self.oauth_client,
                self.memory_client,
                self.db_manager,
                self.discovery_url,
                self.session_id
            )
            self.agents[agent_config.name] = agent

            # Print agent info
            print(f"\n   ✓ {agent_config.role} ({agent_config.name})")
            print(f"      OAuth Scopes: {', '.join(agent_config.oauth_scopes) if agent_config.oauth_scopes else 'None'}")
            print(f"      Discovered Tools: {', '.join(agent.tool_agent.list_tools()) if agent.tool_agent.available_tools else 'None'}")

        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []

        print(f"\n✅ System initialized with dynamic tool discovery!")

    def _check_services(self):
        """Check health of all services including discovery server."""
        checker = ServiceHealthChecker()

        # OAuth service
        if 'base_url' in self.config.oauth_service:
            checker.check_service(
                self.config.oauth_service['base_url'],
                "OAuth Service"
            )

        # Memory service
        if 'base_url' in self.config.memory_service:
            checker.check_service(
                self.config.memory_service['base_url'],
                "Memory Service"
            )

        # Tool Discovery Server
        checker.check_service(
            self.discovery_url,
            "Tool Discovery Server"
        )

    def run_conversation(self, num_turns: int = None):
        """Run integrated multi-agent conversation with tool discovery."""
        if num_turns is None:
            num_turns = self.config.session['max_turns']

        turn_order = self.config.session['turn_order']

        print(f"\n{'='*60}")
        print(f"Starting Conversation with Tool Discovery ({num_turns} turns)")
        print(f"{'='*60}\n")

        turn_counter = 0

        for turn in range(num_turns):
            for agent_name in turn_order:
                turn_counter += 1
                agent = self.agents[agent_name]

                # Get recent context
                context = self.conversation_history[-5:]

                # Agent responds
                print(f"[Turn {turn_counter}] {agent.config.role} ({agent_name}):")
                print(f"  Available tools: {', '.join(agent.tool_agent.list_tools()) if agent.tool_agent.available_tools else 'None'}")
                response = agent.respond(context, turn_counter)
                print(f"  {response}\n")

                # Log message
                message = {
                    "turn": turn_counter,
                    "agent": agent_name,
                    "role": agent.config.role,
                    "message": response
                }
                self.conversation_history.append(message)

                # Small delay for readability
                time.sleep(0.5)

        # End session
        self.db_manager.end_session(self.session_id, turn_counter)

        print(f"\n{'='*60}")
        print(f"✅ Conversation complete: {turn_counter} messages")
        print(f"{'='*60}\n")

        # Show tool usage stats
        self._show_tool_stats()

    def _show_tool_stats(self):
        """Show tool discovery and usage statistics."""
        print(f"\n{'Tool Discovery Statistics':-^60}\n")

        for agent_name, agent in self.agents.items():
            stats = agent.tool_agent.get_tool_usage_stats()
            print(f"🤖 {agent_name}:")
            print(f"   Tools discovered: {stats['total_tools_available']}")
            print(f"   Tools mentioned: {stats['total_tool_calls']}")
            if stats['total_tool_calls'] > 0:
                print(f"   Most mentioned: {stats['most_used_tool']}")
            print()

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the session including tool discovery info."""
        messages = self.db_manager.get_session_messages(self.session_id)

        tool_discovery_info = {}
        for agent_name, agent in self.agents.items():
            tool_discovery_info[agent_name] = {
                "tools_available": agent.tool_agent.list_tools(),
                "total_tools": len(agent.tool_agent.available_tools)
            }

        return {
            "session_id": self.session_id,
            "total_messages": len(messages),
            "agents": list(self.agents.keys()),
            "database_path": self.config.database['path'],
            "tool_discovery": tool_discovery_info
        }

    def cleanup(self):
        """Cleanup resources."""
        self.db_manager.close()


def main():
    """Demo: Integrated System with Tool Discovery."""

    print("=" * 80)
    print("Starting Day 17 Demo: Tool Discovery Integration")
    print("=" * 80)
    print("\n⚠️  Prerequisites:")
    print("   1. LM Studio running on port 1234")
    print("   2. OAuth Service running on port 8001")
    print("   3. Memory Service running on port 8005")
    print("   4. Tool Discovery Server running on port 8006")
    print("\n   Start services with: ./day_16/start_services.sh")
    print("   Then: python day_17/tool_discovery_server.py")
    print("\n" + "=" * 80 + "\n")

    try:
        # Create orchestrator with tool discovery
        system = OrchestratorWithDiscovery(
            config_path="day_15/agents_config.yaml",
            discovery_url="http://localhost:8006"
        )

        # Run conversation
        system.run_conversation(num_turns=2)

        # Get summary
        summary = system.get_session_summary()
        print("\n📊 Session Summary:")
        print(f"   Session ID: {summary['session_id']}")
        print(f"   Total Messages: {summary['total_messages']}")
        print(f"   Agents: {', '.join(summary['agents'])}")
        print(f"   Database: {summary['database_path']}")

        print(f"\n🔍 Tool Discovery Summary:")
        for agent, info in summary['tool_discovery'].items():
            print(f"   {agent}: {info['total_tools']} tools → {', '.join(info['tools_available']) if info['tools_available'] else 'None'}")

        # Cleanup
        system.cleanup()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure all services are running!")


if __name__ == "__main__":
    main()
