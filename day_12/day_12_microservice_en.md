On day twelve, things get exciting again... We're turning our memory system into a real microservice! And to do this, we'll use the **Model Context Protocol (MCP)**, which was originally implemented by Anthropic and is the quasi-standard for LLM tools.

I actually spent more time on this than I would have liked. A lot of new stuff :)

**What's the Problem?**

Until now, each agent had its own memory. This leads to **code duplication** because a separate memory has to be programmed for each agent. It might even lead to **inconsistencies** if different memory strategies are implemented. This can certainly be intentional and is still possible with MCP. However, it becomes difficult or tedious at the latest when it comes to **scaling**. What if we're no longer talking about three or four agents, but 20?

On day three, we first brought the memory to life, and each agent had its own list. On day seven, we also defined a common list or a shared memory for all agents. The implementations looked like this:

```python
class AgentWithMemory: 
    def __init__(self, persona: str):
        self.persona = persona
        self.conversation_history = []  
        
class MultiAgentSystem:  
    def __init__(self):
        self.conversation = []
```

And now we're trying to improve this and address the disadvantages mentioned above by using MCP. We are building a central memory service that implements the **Model Context Protocol**.

## What is MCP, anyway?

The **Model Context Protocol (MCP)** is Anthropic's standard for LLM tools. Instead of every developer inventing their own API endpoints, MCP provides clear rules:

- **Uniform Endpoint Names** (`/tools/...`)
- **Standardized Data Structures** (Request/Response Models)
- **Tool Discovery** (Agents find tools automatically)
- **Community Compatibility** (works with all MCP clients)

These points might sound theoretical and contrived at first. But in practice, this is a big deal. Imagine you want to connect your agent to various services and have to write or call an API for each one... That could become quite complex.

Currently, every developer invents their own API endpoints. Company A's memory service uses `POST /api/v1/memories/store`, while Company B uses `POST /memory/save`. Company C, in turn, has implemented `POST /agent/store-message`, and at Company D, it's called `POST /chat/add-turn`. They all do the same thing, but everyone speaks a different language.

This means your agent has to be reprogrammed for each service. Want to use three different services? Then you have to write three different API integrations. With 20 services, that's 20 different integrations. You see where this is going...

With MCP, it's different. Here, all services follow the same standard. Storing memory is always `POST /tools/store_memory`, retrieving the latest messages is always `POST /tools/get_recent_turns`, and compression runs via `POST /tools/get_compressed_memory`. No matter the service, no matter the provider. The advantage is obvious, isn't it?!

Without MCP, your agent has to learn different APIs. It needs separate connections for the memory service, another for the search service, and yet another for calculations. Each with its own methods, its own data structures, its own error codes.

With MCP, on the other hand, your agent automatically discovers all available tools. It speaks a single, standardized language and can immediately use any MCP-compatible service.
If a new service comes online, for example, the agent recognizes it automatically and can use it right away, without us having to change a single line of code.

Let me try an analogy.
MCP works like USB for computers. You used to have different ports for your mouse, keyboard, printer, and external hard drives (if you were lucky enough to have that pleasure :)).
Today, all devices have a USB port, and we plug them into the corresponding slot, and everything just works. In the same way, MCP turns API chaos into a unified standard for LLM tools.

Let's get to our implementation and our service.

## Our Services

Our service provides three standardized tools:

### 1. Store Memory
```python
@app.post("/tools/store_memory")
async def tool_store_memory(request: StoreMemoryRequest):
    # Agent sends: "Planner said: We go at 2 AM"
    # Service saves it with a timestamp and session ID
```

### 2. Get Recent Messages
```python
@app.post("/tools/get_recent_turns")
async def tool_get_recent_turns(request: GetRecentTurnsRequest):
    # Agent asks: "Give me the last 5 messages"
    # Service filters by agent + session and returns them
```

### 3. Get Compressed Summary
```python  
@app.post("/tools/get_compressed_memory")
async def tool_get_compressed_memory(request: GetCompressedMemoryRequest):
    # Agent asks: "Summarize the old history in 50 tokens"  
    # Service uses hierarchical compression (see Day 11: Memory Compression)
```

The MCP standard requires clean data structures. We define these with Pydantic:

```python
class StoreMemoryRequest(BaseModel):
    agent_id: str
    turn_id: int
    message: str
    game_session_id: Optional[str] = None
    phase: Optional[str] = None

class StoreMemoryResponse(BaseModel):
    memory_id: int
    stored: bool

class GetRecentTurnsRequest(BaseModel):
    agent_id: str
    limit: int = 5
    game_session_id: Optional[str] = None
```

This provides **automatic validation**, **API documentation**, and **type safety**. You benefit from this in many ways.

And what does this look like in practice?

An agent wants to save a message:

```python
# Agent as an MCP client
store_request = {
    "agent_id": "planner",
    "turn_id": 42, 
    "message": "We abort if police response < 15min",
    "game_session_id": "heist-2024",
    "phase": "planning"
}

response = client.post("/tools/store_memory", json=store_request)
# Response: {"memory_id": 1, "stored": True}
```

Later, the same agent wants its history:

```python
# Agent retrieves its memory
get_request = {
    "agent_id": "planner",
    "limit": 5,
    "game_session_id": "heist-2024"
}

response = client.post("/tools/get_recent_turns", json=get_request)
# Response: {"agent_id": "planner", "turns": [...], "turn_count": 1}
```

## Tool Discovery - The Cool Thing About MCP

The agent doesn't need to know which tools are available! It just asks:

```python
response = client.get("/")  # MCP Tool Discovery
info = response.json()
print(f"Service: {info['service']}")
print(f"Version: {info['version']}")
print(f"Available Tools: {len(info['tools'])}")
#...
discovered_tools = info['tools']
print(f"🔍 Agent discovered {len(discovered_tools)} tools automatically:")
for tool in discovered_tools:
    print(f"  POST /tools/{tool:<20} → Auto-discovered MCP tool") 
```

The lines above (which I've trimmed down a bit from the version in the repo) produce this output:

```bash
Service: Memory Server (MCP)
Version: 1.0.0
Available Tools: 3

3️⃣ MCP Tools (automatically discovered!)
------------------------------------------------------------
🔍 Agent discovered 3 tools automatically:
  POST /tools/store_memory         → Auto-discovered MCP tool
  POST /tools/get_recent_turns     → Auto-discovered MCP tool
  POST /tools/get_compressed_memory → Auto-discovered MCP tool

📋 Standard Service Endpoints:
  GET    /                              → MCP Tool Discovery
  GET    /health                        → Health Check
```

And there they are, the discovered services. The agent learns at runtime what it can do! Sounds practical, doesn't it?

But we can learn even more from or about our service.
For example, every professional service needs a health check:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "memory-server", 
        "timestamp": datetime.now().isoformat()
    }
```

This allows load balancers and monitoring tools to check if the service is running.

And there's surely much more that can be done. I'm just getting into this topic myself and still have a lot to learn!

## Why is this better?

Let's summarize the advantages again, now that we've seen how to implement it. The central MCP Memory Service gives us three crucial benefits.

**Scaling becomes child's play.** Previously, each agent ran its own memory instance. That means 10 agents, 10 memory objects in memory, 10 times the same logic loaded. With the central service, we have 10 agents but only one memory service. This not only makes the system more resource-efficient but also much easier to monitor and debug.

**Consistency by design.** All agents automatically use the same memory compression, the same data structures, and the same error handling. No more deviations, no more different implementations. What works for Agent A is guaranteed to work for Agent B and C.

**Maintenance becomes a dream.** Discovered a memory bug? One fix, done. Developed a new memory feature? One deployment, all agents benefit immediately. Need performance tuning? Optimize one service instead of going through ten different implementations. This saves time, nerves, and drastically reduces the error rate.

Let's continue with our implementation. On to the LLM integration. For once, I'll post again how we can talk to LM-Studio and our model ;)

## LLM Integration for Memory Compression

For memory compression, we use LM Studio - just like in the previous days:

```python
# LM Studio Integration
from openai import OpenAI

llm_client = OpenAI(
    base_url="http://localhost:1234/v1", 
    api_key="lm-studio"
)

def compress_with_llm(messages, agent_id, max_tokens, phases):
    prompt = f"""Create a precise summary of the following agent messages:
    
AGENT: {agent_id}
MESSAGES ({len(messages)} total): {messages}

TASK: Summarize the most important points in a MAXIMUM of {max_tokens} words."""
    
    response = llm_client.chat.completions.create(
        model="mistralai/ministral-3b", 
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens * 2,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()
```

The LLM provides intelligent structuring, recognizes important details, and formats the output. Depending on the token limit, it automatically adjusts the style, from compact bullet points to detailed planning sketches. We'll observe this in the example later.

## Demo: Service in Action

Our `day_12_microservice.py` shows the complete MCP workflow in practice. The demo script systematically runs through all the important functions of the service.

First, it checks the service's health with a health check, then it uses **MCP Tool Discovery** to automatically find out which tools are available. So the agent doesn't need to know what the service can do - it discovers it at runtime. We've already looked at this in more detail above.

After that, the script simulates a planning process. It stores a series of related messages: security analysis, timing details, equipment lists, escape routes, and risk assessments. This creates a real conversation history, just as it would arise from the collaboration of multiple agents.

```python
test_messages = [
    "Security analysis: Two guards at main entrance, one at back.",
    "Timing critical: Bank closes at 6 PM, security system activates at 6:15 PM.",
    "Equipment check: Need 3 lockpicks, 2 radios, 1 thermal scanner.",
    # ... more planning messages
]
```

The interesting part comes with the **hierarchical memory compression** (from Day 11): The script tests different token limits and `recent_count` values. The last 2-3 messages remain complete, while older messages are compressed. This way, no current information is lost, but token consumption remains under control. We're already familiar with this.

In the smaller of the two tests, this leads to the following result, for example:

```bash
Hierarchical Compression Tests:

📚 30 tokens, recent_count=2:
📝 Compressed: Planning a heist. Security: 2 guards in front, 1 in back. Time-critical: Bank closes at 6:00 PM, alarm from 6:15 PM. Required equipment: 3 lockpicks, 2
🔥 Recent (2):
  - Risk assessment: Police response time approximatel...
  - Contingency plan: If detected, abort via emergency...
💾 Total tokens: 43
```

## Summary and Outlook

With our MCP Memory Service, we've taken an important step. Instead of distributed agent memories, we now have a central, standardized solution. This brings us a real microservice architecture: one service, one responsibility, a clean API, horizontally scalable!

The foundation is in place, but some features are still missing for production use:

```python
# Next steps for Production:
- Authentication (API Keys, OAuth)
- Rate Limiting (no more than X requests/minute)  
- Metrics (Prometheus Integration)
- Structured Logging (JSON Logs)
- Circuit Breaker (fallback in case of overload)
- Load Balancing (multiple service instances)
```

But the most important advantage is already there: **Standardization through MCP**. Our service speaks the same language as all other MCP services. This means agents can automatically discover and use it without special integration.

And this is just the beginning. With MCP, we can build an entire ecosystem of services: Memory, Search, Calculations, Data Processing - all with the same standardized interface. The agent discovers them automatically and can use them immediately.

This is the future of LLM architectures: modular, interchangeable services that work together like Lego bricks!
