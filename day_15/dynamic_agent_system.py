"""
Day 15: Dynamic Agent System
Configuration-driven multi-agent system with YAML-based agent definitions.
"""

import yaml
import requests
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dataclasses import dataclass
import json


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    name: str
    role: str
    tools: List[str]
    oauth_scopes: List[str]
    system_prompt: str
    is_saboteur: bool


@dataclass
class SystemConfig:
    """Complete system configuration."""
    agents: List[AgentConfig]
    oauth_service: Dict[str, Any]
    tool_services: Dict[str, Dict[str, Any]]
    llm: Dict[str, Any]
    memory_service: Dict[str, Any]
    session: Dict[str, Any]


class ConfigLoader:
    """Loads and parses YAML configuration."""

    @staticmethod
    def load_config(config_path: str) -> SystemConfig:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Parse agent configurations
        agents = []
        for agent_data in config_data['agents']:
            agent = AgentConfig(
                name=agent_data['name'],
                role=agent_data['role'],
                tools=agent_data.get('tools', []),
                oauth_scopes=agent_data.get('oauth_scopes', []),
                system_prompt=agent_data['system_prompt'],
                is_saboteur=agent_data.get('is_saboteur', False)
            )
            agents.append(agent)

        return SystemConfig(
            agents=agents,
            oauth_service=config_data['oauth_service'],
            tool_services=config_data['tool_services'],
            llm=config_data['llm'],
            memory_service=config_data['memory_service'],
            session=config_data['session']
        )


class OAuthClient:
    """Handles OAuth token management."""

    def __init__(self, oauth_config: Dict[str, Any]):
        self.base_url = oauth_config['base_url']
        self.tokens: Dict[str, str] = {}

    def get_token(self, client_id: str, scopes: List[str]) -> Optional[str]:
        """Get OAuth token for agent with specified scopes."""
        if not scopes:
            return None

        scope_key = f"{client_id}:{','.join(sorted(scopes))}"

        # Check if we already have a token
        if scope_key in self.tokens:
            return self.tokens[scope_key]

        # Request new token
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": "secret",
                    "scope": " ".join(scopes)
                }
            )

            if response.status_code == 200:
                token = response.json()['access_token']
                self.tokens[scope_key] = token
                return token
            else:
                print(f"Failed to get OAuth token: {response.status_code}")
                return None
        except Exception as e:
            print(f"OAuth error: {e}")
            return None


class ToolClient:
    """Handles tool invocations with OAuth."""

    def __init__(self, tool_services: Dict[str, Dict[str, Any]]):
        self.services = tool_services

    def call_tool(self, tool_name: str, token: Optional[str], **kwargs) -> Any:
        """Call a tool service with OAuth token."""
        if tool_name not in self.services:
            return f"Tool {tool_name} not configured"

        service = self.services[tool_name]
        url = f"http://{service['host']}:{service['port']}{service['endpoint']}"

        headers = {}
        if token:
            headers['Authorization'] = f"Bearer {token}"

        try:
            response = requests.post(url, json=kwargs, headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                return f"Tool error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Tool error: {e}"


class DynamicAgent:
    """Agent created from configuration."""

    def __init__(
        self,
        config: AgentConfig,
        llm_client: OpenAI,
        llm_config: Dict[str, Any],
        oauth_client: OAuthClient,
        tool_client: ToolClient
    ):
        self.config = config
        self.llm_client = llm_client
        self.llm_config = llm_config
        self.oauth_client = oauth_client
        self.tool_client = tool_client
        self.oauth_token: Optional[str] = None

        # Get OAuth token if scopes are configured
        if self.config.oauth_scopes:
            self.oauth_token = self.oauth_client.get_token(
                self.config.name,
                self.config.oauth_scopes
            )

    def respond(self, context: List[Dict[str, str]]) -> str:
        """Generate response based on conversation context."""
        # Build messages with system prompt
        messages = [{"role": "system", "content": self.config.system_prompt}]

        # Add conversation context
        for msg in context:
            messages.append({
                "role": "user",
                "content": f"[{msg['agent']}]: {msg['message']}"
            })

        # Add tool availability info
        if self.config.tools:
            tool_info = f"\n\nAvailable tools: {', '.join(self.config.tools)}"
            messages.append({
                "role": "system",
                "content": tool_info
            })

        # Get LLM response
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_config['model'],
                messages=messages,
                temperature=self.llm_config.get('temperature', 0.7),
                max_tokens=self.llm_config.get('max_tokens', 500)
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {e}"

    def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Use a tool if agent has permission."""
        # Check if agent has this tool
        tool_scope = f"{tool_name}:use"
        if tool_scope not in self.config.oauth_scopes:
            return f"Agent {self.config.name} does not have permission for {tool_name}"

        return self.tool_client.call_tool(tool_name, self.oauth_token, **kwargs)


class DynamicAgentSystem:
    """Orchestrates multiple dynamically configured agents."""

    def __init__(self, config_path: str):
        # Load configuration
        self.config = ConfigLoader.load_config(config_path)

        # Initialize LLM client
        self.llm_client = OpenAI(
            base_url=self.config.llm['base_url'],
            api_key=self.config.llm['api_key']
        )

        # Initialize OAuth client
        self.oauth_client = OAuthClient(self.config.oauth_service)

        # Initialize tool client
        self.tool_client = ToolClient(self.config.tool_services)

        # Create agents
        self.agents: Dict[str, DynamicAgent] = {}
        for agent_config in self.config.agents:
            agent = DynamicAgent(
                agent_config,
                self.llm_client,
                self.config.llm,
                self.oauth_client,
                self.tool_client
            )
            self.agents[agent_config.name] = agent

        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []

    def run_conversation(self, num_turns: int = None):
        """Run multi-agent conversation."""
        if num_turns is None:
            num_turns = self.config.session['max_turns']

        turn_order = self.config.session['turn_order']

        print(f"\n🎭 Starting Dynamic Agent System")
        print(f"📋 Agents: {', '.join([a.config.role for a in self.agents.values()])}")
        print(f"🔧 Tool Services: {', '.join(self.config.tool_services.keys())}")
        print(f"🔄 Turn Order: {' → '.join(turn_order)}\n")

        for turn in range(num_turns):
            for agent_name in turn_order:
                agent = self.agents[agent_name]

                # Get recent context (last 5 messages)
                context = self.conversation_history[-5:]

                # Agent responds
                response = agent.respond(context)

                # Log message
                message = {
                    "turn": turn + 1,
                    "agent": agent_name,
                    "role": agent.config.role,
                    "message": response
                }
                self.conversation_history.append(message)

                # Display
                print(f"[Turn {turn + 1}] {agent.config.role} ({agent_name}):")
                print(f"  {response}\n")

        print(f"\n✅ Conversation complete: {len(self.conversation_history)} messages")

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about all configured agents."""
        info = {}
        for name, agent in self.agents.items():
            info[name] = {
                "role": agent.config.role,
                "tools": agent.config.tools,
                "scopes": agent.config.oauth_scopes,
                "has_token": agent.oauth_token is not None
            }
        return info

    def save_conversation(self, filepath: str):
        """Save conversation history to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
        print(f"💾 Conversation saved to {filepath}")


def main():
    """Demo: Dynamic Agent System."""

    print("=" * 60)
    print("Day 15: Dynamic Agent System")
    print("Configuration-Driven Multi-Agent AI")
    print("=" * 60)

    # Load system from YAML config
    system = DynamicAgentSystem("day_15/agents_config.yaml")

    # Show agent info
    print("\n📊 Agent Configuration:")
    agent_info = system.get_agent_info()
    for name, info in agent_info.items():
        print(f"\n  {name.upper()} ({info['role']}):")
        print(f"    Tools: {info['tools'] if info['tools'] else 'None'}")
        print(f"    Scopes: {info['scopes'] if info['scopes'] else 'None'}")
        print(f"    OAuth Token: {'✅' if info['has_token'] else '❌'}")

    # Run conversation
    print("\n" + "=" * 60)
    system.run_conversation(num_turns=3)

    # Save conversation
    system.save_conversation("day_15/conversation_log.json")


if __name__ == "__main__":
    main()
