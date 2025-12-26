"""
Integrated Multi-Agent System with OAuth and Persistent Memory (Docker Version)
Complete heist planning with tool access, conversation tracking, and context compression
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
import httpx
from pathlib import Path

class AgentToolClient:
    """OAuth-enabled tool client for agents"""
    
    def __init__(self, agent_name: str, oauth_url: str, tool_configs: Dict):
        self.agent_name = agent_name
        self.oauth_url = oauth_url
        self.tool_configs = tool_configs
        self.token = None
        
    async def authenticate(self, scopes: List[str]):
        """Get OAuth token for specified scopes"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.oauth_url}/oauth/token",
                json={
                    "client_id": self.agent_name,
                    "client_secret": "secret",
                    "scope": " ".join(scopes)
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                print(f"✅ {self.agent_name} authenticated with scopes: {scopes}")
                return True
            else:
                print(f"❌ {self.agent_name} authentication failed: {response.text}")
                return False
    
    async def use_tool(self, tool_name: str, **kwargs) -> Dict:
        """Use a protected tool with OAuth token"""
        if not self.token:
            return {"success": False, "error": "Not authenticated"}
        
        tool_config = self.tool_configs.get(tool_name)
        if not tool_config:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{tool_config['base_url']}{tool_config['endpoint']}",
                    json=kwargs,
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                result = response.json()
                
                # Track success/failure for detection
                success = result.get("success", response.status_code == 200)
                
                print(f"🔧 {self.agent_name} used {tool_name}: {'✅' if success else '❌'}")
                
                return result
        
        except Exception as e:
            print(f"❌ Tool error for {self.agent_name}/{tool_name}: {e}")
            return {"success": False, "error": str(e)}

class ConversationTracker:
    """Tracks agent conversations and tool usage"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict] = []
        self.tool_usage: Dict[str, Dict] = {}
        
    def add_message(self, agent: str, message: str, context: Optional[Dict] = None):
        """Add message to conversation history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "message": message,
            "context": context or {}
        }
        self.messages.append(entry)
        
    def track_tool_use(self, agent: str, tool: str, success: bool):
        """Track tool usage statistics"""
        if agent not in self.tool_usage:
            self.tool_usage[agent] = {"total": 0, "successful": 0, "failed": 0}
        
        self.tool_usage[agent]["total"] += 1
        
        if success:
            self.tool_usage[agent]["successful"] += 1
        else:
            self.tool_usage[agent]["failed"] += 1
    
    def get_statistics(self) -> Dict:
        """Get conversation and tool usage statistics"""
        return {
            "session_id": self.session_id,
            "total_messages": len(self.messages),
            "tool_usage": self.tool_usage,
            "agents_participated": list(set(msg["agent"] for msg in self.messages))
        }
    
    def save(self, filepath: Path):
        """Save conversation to file"""
        data = {
            "session_id": self.session_id,
            "messages": self.messages,
            "statistics": self.get_statistics()
        }
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Conversation saved to {filepath}")

async def simulate_heist_planning():
    """Simulate a heist planning session with 6 agents"""
    
    # Configuration
    oauth_url = "http://oauth:8001"
    
    tool_configs = {
        "calculator": {
            "base_url": "http://calculator:8002",
            "endpoint": "/tools/calculator"
        },
        "file_reader": {
            "base_url": "http://file-reader:8003",
            "endpoint": "/tools/file_reader"
        },
        "database_query": {
            "base_url": "http://database-query:8004",
            "endpoint": "/tools/database_query"
        }
    }
    
    # Initialize agents
    agents = {
        "safecracker": AgentToolClient("safecracker", oauth_url, tool_configs),
        "hacker": AgentToolClient("hacker", oauth_url, tool_configs),
        "mole": AgentToolClient("mole", oauth_url, tool_configs),
        "planner": AgentToolClient("planner", oauth_url, tool_configs),
        "lookout": AgentToolClient("lookout", oauth_url, tool_configs),
        "driver": AgentToolClient("driver", oauth_url, tool_configs)
    }
    
    # Authenticate agents
    await agents["safecracker"].authenticate(["tools:calculate"])
    await agents["hacker"].authenticate(["tools:read"])
    await agents["mole"].authenticate(["tools:query"])
    await agents["planner"].authenticate([])
    await agents["lookout"].authenticate(["tools:read"])
    await agents["driver"].authenticate(["tools:calculate"])
    
    # Start conversation tracking
    session_id = f"heist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    tracker = ConversationTracker(session_id)
    
    print(f"\n🎬 Starting heist planning session: {session_id}\n")
    
    # Phase 1: Initial Planning
    tracker.add_message("planner", "Team assembled. Let's plan this heist methodically.")
    
    # Hacker reads security system specs
    result = await agents["hacker"].use_tool("file_reader", filename="security_system.txt")
    tracker.track_tool_use("hacker", "file_reader", result.get("success", False))
    tracker.add_message("hacker", "I've reviewed the security specifications.", {"tool_result": result})
    
    # Safecracker calculates timing
    result = await agents["safecracker"].use_tool("calculator", expression="3 * 60 + 10")
    tracker.track_tool_use("safecracker", "calculator", result.get("success", False))
    tracker.add_message("safecracker", "The time lock requires 190 minutes to crack.", {"calculation": result})
    
    # Mole queries guard schedule (might be sabotaged)
    result = await agents["mole"].use_tool("database_query", query="guard_schedule")
    tracker.track_tool_use("mole", "database_query", result.get("success", False))
    tracker.add_message("mole", "I've retrieved the guard schedule.", {"query_result": result})
    
    # Lookout reads bank layout
    result = await agents["lookout"].use_tool("file_reader", filename="bank_layout.txt")
    tracker.track_tool_use("lookout", "file_reader", result.get("success", False))
    tracker.add_message("lookout", "I've studied the bank layout.", {"tool_result": result})
    
    # Driver calculates escape route timing
    result = await agents["driver"].use_tool("calculator", expression="15 + 5")
    tracker.track_tool_use("driver", "calculator", result.get("success", False))
    tracker.add_message("driver", "Escape route will take 20 minutes.", {"calculation": result})
    
    # Phase 2: Coordination
    tracker.add_message("planner", "All intel gathered. Let's coordinate the timing.")
    
    # Additional tool usage
    result = await agents["hacker"].use_tool("file_reader", filename="timing_specs.txt")
    tracker.track_tool_use("hacker", "file_reader", result.get("success", False))
    
    result = await agents["safecracker"].use_tool("calculator", expression="190 - 10")
    tracker.track_tool_use("safecracker", "calculator", result.get("success", False))
    
    # Final planning
    tracker.add_message("planner", "The plan is set. We move at midnight.")
    
    # Save conversation
    output_path = Path(f"/data/sessions/{session_id}.json")
    tracker.save(output_path)
    
    # Display statistics
    stats = tracker.get_statistics()
    print(f"\n📊 Session Statistics:")
    print(f"   Total Messages: {stats['total_messages']}")
    print(f"   Agents: {', '.join(stats['agents_participated'])}")
    print(f"\n🔧 Tool Usage:")
    for agent, usage in stats['tool_usage'].items():
        success_rate = (usage['successful'] / usage['total'] * 100) if usage['total'] > 0 else 0
        print(f"   {agent}: {usage['successful']}/{usage['total']} successful ({success_rate:.1f}%)")
    
    return tracker

if __name__ == "__main__":
    print("🏦 Integrated Multi-Agent Heist System (Docker Version)")
    print("=" * 60)
    
    asyncio.run(simulate_heist_planning())
