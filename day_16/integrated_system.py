"""
Day 16: Service Integration
Bringing together all services: OAuth + Tools + Memory + SQLite + Dynamic Agents
"""

import sqlite3
import requests
import yaml
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dataclasses import dataclass
from datetime import datetime
import json
import time


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
    database: Dict[str, Any]


class ConfigLoader:
    """Loads and parses YAML configuration."""

    @staticmethod
    def load_config(config_path: str) -> SystemConfig:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

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
            session=config_data['session'],
            database=config_data.get('database', {'path': 'day_16/heist_session.db'})
        )


class DatabaseManager:
    """Manages SQLite database for persistent storage."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                num_turns INTEGER,
                status TEXT
            )
        """)

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                turn_id INTEGER,
                agent_name TEXT,
                agent_role TEXT,
                message TEXT,
                timestamp TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Tool usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                turn_id INTEGER,
                agent_name TEXT,
                tool_name TEXT,
                tool_params TEXT,
                tool_result TEXT,
                timestamp TEXT,
                success INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        self.connection.commit()

    def create_session(self, session_id: str) -> bool:
        """Create a new session."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, start_time, status)
                VALUES (?, ?, ?)
            """, (session_id, datetime.now().isoformat(), "active"))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False

    def store_message(self, session_id: str, turn_id: int, agent_name: str,
                     agent_role: str, message: str):
        """Store a conversation message."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO messages (session_id, turn_id, agent_name, agent_role, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, turn_id, agent_name, agent_role, message, datetime.now().isoformat()))
        self.connection.commit()

    def store_tool_usage(self, session_id: str, turn_id: int, agent_name: str,
                        tool_name: str, params: str, result: str, success: bool):
        """Store tool usage record."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO tool_usage (session_id, turn_id, agent_name, tool_name,
                                   tool_params, tool_result, timestamp, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, turn_id, agent_name, tool_name, params, result,
              datetime.now().isoformat(), 1 if success else 0))
        self.connection.commit()

    def end_session(self, session_id: str, num_turns: int):
        """Mark session as complete."""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, num_turns = ?, status = 'completed'
            WHERE session_id = ?
        """, (datetime.now().isoformat(), num_turns, session_id))
        self.connection.commit()

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages from a session."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT turn_id, agent_name, agent_role, message, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY turn_id
        """, (session_id,))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                "turn_id": row[0],
                "agent_name": row[1],
                "agent_role": row[2],
                "message": row[3],
                "timestamp": row[4]
            })
        return messages

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


class ServiceHealthChecker:
    """Checks health of all external services."""

    @staticmethod
    def check_service(url: str, service_name: str) -> bool:
        """Check if a service is reachable."""
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ {service_name} is healthy")
                return True
            else:
                print(f"⚠️  {service_name} returned {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ {service_name} is unreachable: {e}")
            return False


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

        if scope_key in self.tokens:
            return self.tokens[scope_key]

        try:
            response = requests.post(
                f"{self.base_url}/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": "secret",
                    "scope": " ".join(scopes)
                },
                timeout=5
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


class MemoryServiceClient:
    """Client for Memory Service (MCP)."""

    def __init__(self, memory_config: Dict[str, Any]):
        self.base_url = memory_config['base_url']

    def store_memory(self, agent_id: str, turn_id: int, message: str,
                    session_id: str) -> bool:
        """Store a memory in the memory service."""
        try:
            response = requests.post(
                f"{self.base_url}/tools/store_memory",
                json={
                    "agent_id": agent_id,
                    "turn_id": turn_id,
                    "message": message,
                    "game_session_id": session_id
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Memory service error: {e}")
            return False

    def get_compressed_memory(self, agent_id: str, session_id: str,
                             max_tokens: int = 100) -> Optional[str]:
        """Get compressed memory summary."""
        try:
            response = requests.post(
                f"{self.base_url}/tools/get_compressed_memory",
                json={
                    "agent_id": agent_id,
                    "game_session_id": session_id,
                    "max_tokens": max_tokens,
                    "recent_count": 3
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('compressed_summary', '')
            return None
        except Exception as e:
            print(f"Memory compression error: {e}")
            return None


class ToolClient:
    """Handles tool invocations with OAuth."""

    def __init__(self, tool_services: Dict[str, Dict[str, Any]]):
        self.services = tool_services

    def call_tool(self, tool_name: str, token: Optional[str], **kwargs) -> Any:
        """Call a tool service with OAuth token."""
        if tool_name not in self.services:
            return {"error": f"Tool {tool_name} not configured"}

        service = self.services[tool_name]
        url = f"http://{service['host']}:{service['port']}{service['endpoint']}"

        headers = {}
        if token:
            headers['Authorization'] = f"Bearer {token}"

        try:
            response = requests.post(url, json=kwargs, headers=headers, timeout=5)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Tool error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Tool error: {e}"}


class IntegratedAgent:
    """Agent with full service integration."""

    def __init__(
        self,
        config: AgentConfig,
        llm_client: OpenAI,
        oauth_client: OAuthClient,
        tool_client: ToolClient,
        memory_client: MemoryServiceClient,
        db_manager: DatabaseManager,
        session_id: str
    ):
        self.config = config
        self.llm_client = llm_client
        self.oauth_client = oauth_client
        self.tool_client = tool_client
        self.memory_client = memory_client
        self.db_manager = db_manager
        self.session_id = session_id
        self.oauth_token: Optional[str] = None

        # Get OAuth token if scopes configured
        if self.config.oauth_scopes:
            self.oauth_token = self.oauth_client.get_token(
                self.config.name,
                self.config.oauth_scopes
            )

    def respond(self, context: List[Dict[str, str]], turn_id: int) -> str:
        """Generate response with full service integration."""
        # Build messages with system prompt
        messages = [{"role": "system", "content": self.config.system_prompt}]

        # Add conversation context
        for msg in context:
            messages.append({
                "role": "user",
                "content": f"[{msg['agent']}]: {msg['message']}"
            })

        # Add tool availability
        if self.config.tools:
            tool_info = f"\n\nAvailable tools: {', '.join(self.config.tools)}"
            messages.append({"role": "system", "content": tool_info})

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


class Orchestrator:
    """Fully integrated multi-agent system with all services."""

    def __init__(self, config_path: str):
        # Load configuration
        self.config = ConfigLoader.load_config(config_path)

        # Generate session ID
        self.session_id = f"heist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"\n{'='*60}")
        print(f"Day 16: Integrated Multi-Agent System")
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

        print("🛠️  Initializing tool client...")
        self.tool_client = ToolClient(self.config.tool_services)

        print("💾 Initializing memory service client...")
        self.memory_client = MemoryServiceClient(self.config.memory_service)

        # Create agents
        print("\n👥 Creating agents...")
        self.agents: Dict[str, IntegratedAgent] = {}
        for agent_config in self.config.agents:
            agent = IntegratedAgent(
                agent_config,
                self.llm_client,
                self.oauth_client,
                self.tool_client,
                self.memory_client,
                self.db_manager,
                self.session_id
            )
            self.agents[agent_config.name] = agent
            print(f"   ✓ {agent_config.role} ({agent_config.name})")

        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []

        print(f"\n✅ System initialized successfully!")

    def _check_services(self):
        """Check health of all services."""
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

        # Tool services
        for tool_name, service_config in self.config.tool_services.items():
            url = f"http://{service_config['host']}:{service_config['port']}"
            checker.check_service(url, f"Tool Service ({tool_name})")

    def run_conversation(self, num_turns: int = None):
        """Run integrated multi-agent conversation."""
        if num_turns is None:
            num_turns = self.config.session['max_turns']

        turn_order = self.config.session['turn_order']

        print(f"\n{'='*60}")
        print(f"Starting Conversation ({num_turns} turns)")
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

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the session."""
        messages = self.db_manager.get_session_messages(self.session_id)

        return {
            "session_id": self.session_id,
            "total_messages": len(messages),
            "agents": list(self.agents.keys()),
            "database_path": self.config.database['path']
        }

    def save_conversation(self, filepath: str):
        """Save conversation to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
        print(f"💾 Conversation saved to {filepath}")

    def cleanup(self):
        """Cleanup resources."""
        self.db_manager.close()


def main():
    """Demo: Integrated Multi-Agent System."""

    # Create orchestrator
    system = Orchestrator("day_15/agents_config.yaml")

    # Run conversation
    system.run_conversation(num_turns=2)

    # Get summary
    summary = system.get_session_summary()
    print("\n📊 Session Summary:")
    print(f"   Session ID: {summary['session_id']}")
    print(f"   Total Messages: {summary['total_messages']}")
    print(f"   Agents: {', '.join(summary['agents'])}")
    print(f"   Database: {summary['database_path']}")

    # Save conversation
    system.save_conversation("day_16/conversation_log.json")

    # Cleanup
    system.cleanup()


if __name__ == "__main__":
    main()
