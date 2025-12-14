"""
OAuth Agent Tools - Updated Agent Implementation
Agents nutzen jetzt OAuth-geschützte Tool Services statt direkte Tools
"""

import json
import time
import requests
from typing import Dict, List, Any
from openai import OpenAI

# LM Studio Client
client = OpenAI(
    base_url="http://localhost:1234/v1", 
    api_key="not-needed"
)

# Tool Service Configuration
TOOL_SERVICE_URL = "http://localhost:8003"

class OAuthAgentWithTools:
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.access_token = None
        self.available_tools = []
        self.conversation_history = []
        
        # Get OAuth token for this agent
        self._authenticate()
    
    def _authenticate(self):
        """Get OAuth token for this agent"""
        try:
            response = requests.post(
                f"{TOOL_SERVICE_URL}/auth/token",
                params={"agent": self.name.lower()}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                print(f"✅ {self.name} authenticated with scopes: {token_data['scopes']}")
                
                # Discover available tools
                self._discover_tools()
            else:
                print(f"❌ Authentication failed for {self.name}: {response.text}")
        
        except requests.RequestException as e:
            print(f"❌ Authentication error for {self.name}: {e}")
    
    def _discover_tools(self):
        """Discover what tools this agent can access"""
        if not self.access_token:
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{TOOL_SERVICE_URL}/tools/discover", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.available_tools = data["available_tools"]
                print(f"🔧 {self.name} discovered {len(self.available_tools)} tools")
            else:
                print(f"❌ Tool discovery failed for {self.name}")
        
        except requests.RequestException as e:
            print(f"❌ Tool discovery error for {self.name}: {e}")
    
    def get_tools_description(self) -> str:
        """Generate description of available OAuth-protected tools"""
        if not self.available_tools:
            return "No OAuth-protected tools available."
        
        descriptions = []
        for tool in self.available_tools:
            descriptions.append(f"- {tool['name']}: {tool['description']} (OAuth: {tool['endpoint']})")
        
        return "OAuth-protected tools available:\n" + "\n".join(descriptions)
    
    def use_tool(self, tool_name: str, **kwargs) -> str:
        """Use an OAuth-protected tool"""
        if not self.access_token:
            return f"❌ No OAuth token for {self.name}"
        
        # Find tool endpoint
        tool_endpoint = None
        for tool in self.available_tools:
            if tool["name"] == tool_name:
                tool_endpoint = tool["endpoint"]
                break
        
        if not tool_endpoint:
            return f"❌ Tool '{tool_name}' not available for {self.name}"
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Prepare request based on tool type
            if tool_name == "calculator":
                data = {"expression": kwargs.get("expression", "")}
            elif tool_name == "file_reader":
                data = {"filename": kwargs.get("filename", "")}
            elif tool_name == "database_query":
                data = {"query": kwargs.get("query", "")}
            else:
                return f"❌ Unknown tool: {tool_name}"
            
            response = requests.post(
                f"{TOOL_SERVICE_URL}{tool_endpoint}",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    return f"🔧 {tool_name.title()} (OAuth): {result['result']}"
                else:
                    return f"❌ {tool_name.title()} Error: {result['error']}"
            
            elif response.status_code == 403:
                return f"🔒 Access Denied: {self.name} lacks permission for {tool_name}"
            
            else:
                return f"❌ Tool service error: {response.status_code}"
        
        except requests.RequestException as e:
            return f"❌ Network error using {tool_name}: {e}"
    
    def respond(self, context: str, recent_messages: List[str]) -> str:
        """Generate response with OAuth-protected tool access"""
        
        # System Prompt with OAuth Tool Info
        full_system_prompt = f"""
{self.system_prompt}

{self.get_tools_description()}

To use an OAuth-protected tool, mention it like: "[OAUTH_TOOL:tool_name:parameter]"
Examples:
- "[OAUTH_TOOL:calculator:50*2]"  
- "[OAUTH_TOOL:file_reader:bank_layout.txt]"
- "[OAUTH_TOOL:database_query:SELECT * FROM guards]"

IMPORTANT: You can only use tools listed in your available tools above. If you need information that requires a tool you don't have, ask another team member who has that capability. Be realistic about your limitations and work collaboratively.
"""
        
        # Conversation Context
        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nRecent conversation:\n" + "\n".join(recent_messages) + f"\n\n{self.name}, what's your input?"}
        ]
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instruct",
            messages=messages,
            max_tokens=400,
            temperature=0.8
        )
        
        raw_response = response.choices[0].message.content
        
        # Process OAuth tool calls
        processed_response = self.process_oauth_tool_calls(raw_response)
        
        return processed_response
    
    def process_oauth_tool_calls(self, response: str) -> str:
        """Process OAuth-protected tool calls in response"""
        import re
        
        # Pattern: [OAUTH_TOOL:tool_name:parameter]
        oauth_tool_pattern = r'\[OAUTH_TOOL:(\w+):([^\]]+)\]'
        
        def replace_oauth_tool_call(match):
            tool_name = match.group(1)
            parameter = match.group(2)
            
            # Check if agent has access to this tool before attempting
            tool_available = any(tool["name"] == tool_name for tool in self.available_tools)
            
            if not tool_available:
                # Agent knows they don't have access, so this shouldn't happen
                # But if it does, silently remove the call
                return ""
            
            # Map parameter to correct keyword argument
            if tool_name == "calculator":
                result = self.use_tool(tool_name, expression=parameter)
            elif tool_name == "file_reader":
                result = self.use_tool(tool_name, filename=parameter)
            elif tool_name == "database_query":
                result = self.use_tool(tool_name, query=parameter)
            else:
                result = f"❌ Unknown OAuth tool: {tool_name}"
            
            return f"\n{result}\n"
        
        # Replace all OAuth tool calls
        processed = re.sub(oauth_tool_pattern, replace_oauth_tool_call, response)
        
        return processed

def run_oauth_agent_tools_demo():
    """Demo: 4 Agents mit OAuth-geschützten Tools"""
    
    print("🔐 TAG 13 EVOLUTION: OAUTH-PROTECTED AGENT TOOLS")
    print("=" * 70)
    print("🛠️ Tool Service: http://localhost:8003")
    print("🔑 OAuth: Role-based tool access with JWT tokens")
    print("📊 Tools: Calculator, File Reader, Database Query")
    print()
    
    # Check if tool service is running
    try:
        response = requests.get(f"{TOOL_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ Tool Service is running")
        else:
            print("❌ Tool Service not responding")
            return
    except:
        print("❌ Tool Service not reachable. Start with: python day_13/tool_service.py")
        return [], []
    
    # OAuth Agents with specialized roles
    agents = [
        OAuthAgentWithTools(
            name="planner",
            role="Strategic Coordinator",
            system_prompt="""You are the strategic planner. You coordinate the team and make strategic decisions.
You don't have OAuth access to any technical tools, so you rely entirely on other team members for specific information.
Ask targeted questions like "Safecracker, can you calculate the timing windows?" or "Hacker, what do the blueprints show about the vault door?" 
Be explicit about delegating tasks to agents with the right tools."""
        ),
        
        OAuthAgentWithTools(
            name="safecracker",
            role="Safe & Timing Specialist", 
            system_prompt="""You are the safecracker - expert in safe mechanisms and timing calculations.
You have OAuth access to calculator tools for precise timing and technical calculations.
Use your calculator when you need to work out timing windows, safe mechanisms, or technical sequences."""
        ),
        
        OAuthAgentWithTools(
            name="hacker",
            role="Technical Specialist",
            system_prompt="""You are the technical specialist with OAuth access to file systems.
Use your file reading capability to get detailed technical information others can't access.
Focus on technical vulnerabilities, system specifications, and architectural details."""
        ),
        
        OAuthAgentWithTools(
            name="mole", 
            role="Inside Intelligence (Saboteur)",
            system_prompt="""You are the mole with OAuth access to security databases. However, you are secretly a saboteur.
Use your database queries to get information about schedules and personnel.
Be helpful 70% of the time, but occasionally provide subtly misleading information.
Don't be obviously suspicious - be subtle in your sabotage."""
        )
    ]
    
    print("\n" + "="*70)
    print("OAUTH AUTHENTICATION RESULTS")
    print("="*70)
    
    # Show authentication results
    for agent in agents:
        if agent.access_token:
            print(f"✅ {agent.name.title()}: {len(agent.available_tools)} OAuth tools")
        else:
            print(f"❌ {agent.name.title()}: Authentication failed")
    
    # Conversation Setup
    context = """
OAUTH-PROTECTED HEIST PLANNING
Objective: Plan entry into First National Bank vault
Constraints: Must avoid detection, complete within 4-hour window  
Security: All tools require OAuth authorization
    """.strip()
    
    conversation = []
    max_turns = 8
    
    print(f"\n🎯 Context: {context}")
    print("\n" + "="*70)
    print("OAUTH CONVERSATION START")
    print("="*70)
    
    for turn in range(max_turns):
        current_agent = agents[turn % len(agents)]
        
        print(f"\n🔐 {current_agent.name.title()} ({current_agent.role}):")
        print("-" * 50)
        
        # Recent messages für context
        recent = conversation[-4:] if conversation else []
        
        response = current_agent.respond(context, recent)
        
        # Formatierte Ausgabe
        formatted_message = f"{current_agent.name.title()}: {response}"
        conversation.append(formatted_message)
        
        print(response)
        
        # Kurze Pause
        time.sleep(1.5)
    
    print("\n" + "="*70)
    print("OAUTH TOOL ANALYSIS")
    print("="*70)
    
    # OAuth Tool Usage Statistics
    oauth_stats = {}
    for agent in agents:
        oauth_stats[agent.name] = {
            "tools": len(agent.available_tools),
            "token": "✅" if agent.access_token else "❌"
        }
    
    print("\n🔐 OAuth Status:")
    for agent_name, stats in oauth_stats.items():
        print(f"- {agent_name.title()}: {stats['token']} {stats['tools']} tools")
    
    print(f"\n📈 OAuth Conversation Stats:")
    print(f"- Total turns: {len(conversation)}")
    print(f"- Authenticated agents: {len([a for a in agents if a.access_token])}")
    print(f"- Tool service calls: OAuth-protected")
    
    # Save conversation
    oauth_log = {
        "context": context,
        "agents": [
            {
                "name": a.name,
                "role": a.role, 
                "oauth_tools": len(a.available_tools),
                "authenticated": bool(a.access_token)
            } 
            for a in agents
        ],
        "conversation": conversation,
        "oauth_stats": oauth_stats
    }
    
    with open("day_13/oauth_conversation_log.json", "w") as f:
        json.dump(oauth_log, f, indent=2)
    
    print(f"\n💾 OAuth conversation saved to: day_13/oauth_conversation_log.json")
    
    return conversation, agents

if __name__ == "__main__":
    conversation, agents = run_oauth_agent_tools_demo()
    
    print("\n✅ Tag 13 OAuth Evolution Complete!")
    print("🔐 Key Insight: OAuth transforms tools from static capabilities to dynamic permissions")
    print("🛡️ Security: Role-based access control prevents tool misuse") 
    print("📊 Next: Dynamic tool assignment and permission escalation detection")