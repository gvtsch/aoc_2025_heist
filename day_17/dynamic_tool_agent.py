"""
Day 17: Dynamic Tool Agent
Agent that discovers tools at runtime instead of using hardcoded tool lists.
Builds on Day 16 IntegratedAgent architecture.
"""

import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DiscoveredTool:
    """Represents a tool discovered from the discovery server."""
    name: str
    endpoint: str
    scopes: List[str]
    description: str
    parameters: Dict[str, Any]
    returns: str
    host: str
    port: int

    def get_url(self) -> str:
        """Get full URL for this tool."""
        return f"http://{self.host}:{self.port}{self.endpoint}"


class DynamicToolAgent:
    """
    Agent with dynamic tool discovery capabilities.
    Extends the Day 16 IntegratedAgent concept with runtime tool discovery.
    """

    def __init__(
        self,
        name: str,
        oauth_token: Optional[str],
        discovery_url: str = "http://localhost:8006"
    ):
        self.name = name
        self.oauth_token = oauth_token
        self.discovery_url = discovery_url
        self.available_tools: List[DiscoveredTool] = []
        self.tool_usage_count: Dict[str, int] = {}

        # Discover tools on initialization
        self._discover_tools()

    def _discover_tools(self):
        """Discover available tools from the discovery server."""
        try:
            headers = {}
            if self.oauth_token:
                headers["Authorization"] = f"Bearer {self.oauth_token}"

            response = requests.get(self.discovery_url, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # Parse discovered tools
                self.available_tools = [
                    DiscoveredTool(**tool_data)
                    for tool_data in data.get("tools", [])
                ]

                print(f"[{self.name}] 🔍 Discovered {len(self.available_tools)} tools:")
                for tool in self.available_tools:
                    print(f"   ✓ {tool.name}: {tool.description}")
                    self.tool_usage_count[tool.name] = 0
            else:
                print(f"[{self.name}] ⚠️  Tool discovery failed: {response.status_code}")

        except Exception as e:
            print(f"[{self.name}] ❌ Tool discovery error: {e}")

    def rediscover_tools(self):
        """
        Rediscover tools from the server.
        Useful when new tools are registered or permissions change.
        """
        print(f"[{self.name}] 🔄 Rediscovering tools...")
        old_count = len(self.available_tools)
        self._discover_tools()
        new_count = len(self.available_tools)

        if new_count > old_count:
            print(f"[{self.name}] ✨ Found {new_count - old_count} new tools!")
        elif new_count < old_count:
            print(f"[{self.name}] ⚠️  Lost access to {old_count - new_count} tools")
        else:
            print(f"[{self.name}] ✅ Tool set unchanged")

    def get_tool(self, tool_name: str) -> Optional[DiscoveredTool]:
        """Get a specific tool by name."""
        for tool in self.available_tools:
            if tool.name == tool_name:
                return tool
        return None

    def has_tool(self, tool_name: str) -> bool:
        """Check if agent has access to a specific tool."""
        return any(tool.name == tool_name for tool in self.available_tools)

    def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Use a discovered tool.
        Returns tool result or error.
        """
        tool = self.get_tool(tool_name)

        if not tool:
            return {
                "error": f"Tool '{tool_name}' not available",
                "available_tools": [t.name for t in self.available_tools]
            }

        try:
            headers = {}
            if self.oauth_token:
                headers["Authorization"] = f"Bearer {self.oauth_token}"

            url = tool.get_url()

            response = requests.post(
                url,
                json=kwargs,
                headers=headers,
                timeout=5
            )

            # Track usage
            self.tool_usage_count[tool_name] += 1

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Tool returned {response.status_code}",
                    "detail": response.text
                }

        except Exception as e:
            return {"error": f"Tool execution failed: {e}"}

    def list_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.available_tools]

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "returns": tool.returns,
            "scopes_required": tool.scopes,
            "usage_count": self.tool_usage_count.get(tool_name, 0)
        }

    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage."""
        total_usage = sum(self.tool_usage_count.values())

        return {
            "agent": self.name,
            "total_tools_available": len(self.available_tools),
            "total_tool_calls": total_usage,
            "usage_by_tool": dict(self.tool_usage_count),
            "most_used_tool": max(
                self.tool_usage_count.items(),
                key=lambda x: x[1]
            )[0] if total_usage > 0 else None
        }

    def generate_tool_prompt_context(self) -> str:
        """
        Generate a prompt context string describing available tools.
        Can be included in LLM system prompts.
        """
        if not self.available_tools:
            return "No tools available."

        tool_descriptions = []
        for tool in self.available_tools:
            params = ", ".join(tool.parameters.keys())
            tool_descriptions.append(
                f"- {tool.name}({params}): {tool.description}"
            )

        return "Available tools:\n" + "\n".join(tool_descriptions)


def main():
    """Demo: Dynamic Tool Discovery."""

    print("=" * 80)
    print("Day 17: Dynamic Tool Discovery Demo")
    print("=" * 80)

    # Simulate different agents with different OAuth tokens
    print("\n🤖 Creating agents with different permissions...\n")

    # Agent without token (sees all tools for discovery)
    agent_no_auth = DynamicToolAgent(
        name="Explorer",
        oauth_token=None,
        discovery_url="http://localhost:8006"
    )

    print("\n" + "-" * 80 + "\n")

    # Simulated OAuth token with specific scopes
    # In real scenario, this would come from OAuth service
    print("💡 In production, agents would get real OAuth tokens")
    print("   For demo, we show the concept:\n")

    print("📊 Tool Discovery Stats:")
    print(f"   Total tools discovered: {len(agent_no_auth.available_tools)}")
    print(f"   Tool names: {', '.join(agent_no_auth.list_tools())}")

    print("\n🔍 Detailed Tool Information:")
    for tool_name in agent_no_auth.list_tools():
        info = agent_no_auth.get_tool_info(tool_name)
        if info:
            print(f"\n   {info['name']}:")
            print(f"      Description: {info['description']}")
            print(f"      Required scopes: {', '.join(info['scopes_required'])}")
            print(f"      Parameters: {list(info['parameters'].keys())}")

    print("\n✨ Key Features:")
    print("   ✓ Tools discovered at runtime")
    print("   ✓ Scope-based filtering")
    print("   ✓ Dynamic tool registration possible")
    print("   ✓ Agents can rediscover tools anytime")

    print("\n💡 Integration with Day 16:")
    print("   - Use DynamicToolAgent instead of hardcoded tools")
    print("   - Pass OAuth token from Day 16's OAuth client")
    print("   - Tools filtered automatically by agent permissions")
    print("   - Tool usage tracked in SQLite (from Day 16)")


if __name__ == "__main__":
    main()
