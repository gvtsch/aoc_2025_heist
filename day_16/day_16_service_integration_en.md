---
title: "Day 16: Service Integration"
date: 2025-12-16
tags:
  - python
  - aoc
  - adventofcode
  - aiagents
toc: true
---

You can find all files in my [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_16).

Day 16 brings everything together. We now have individual building blocks: OAuth for security, Tools for specialization, Memory Service for context management, SQLite for persistence, and Dynamic Agents from configuration files. Everything works in isolation. But that's not enough for us. We want an integrated system where all components work together.

## The Problem

Building individual services is one thing. Bringing them together is another. Each service has its own API, its own error modes, and its own performance characteristics. The OAuth Service might be down while the Memory Service is running. Tools can time out while the database is writing. One agent gets its token, but the next one fails, and so on.

This is the difference between microservices on paper and microservices in production. On paper, everyone talks neatly to one another. In reality, there are network issues, service failures, race conditions, inconsistencies...

Today, we're building the system that can handle this reality. Hopefully 🙏 For this, we need:
- **Service Health Checks** before starting: Upon startup, we check whether OAuth, Memory Service, and Tools are reachable. This way, we know if something is missing before we begin and not just when a crash occurs.
- **Graceful handling** of service failures: Instead of crashing hard, the error is logged, and the system continues to run. For example, the system continues even with a single timeout.
- **Consistent data distribution** across all services: Every message is now synchronously passed to the Memory Service and the SQLite database to avoid inconsistencies.
- A **Session ID** that flows through all systems: An ID (e.g., `heist_20250116_143052`) is passed with every service call. This Days all data as belonging together.
- **Complete Audit Trails** in SQLite: Everything is logged. Which agent said what, when, and which tool it used. This allows for later debugging via SQL query instead of guesswork 😉

This may sound good in theory, but what does it mean in practice? Let's look at a single agent turn in detail.

Imagine a typical agent turn. The Planner responds to a question. What all needs to happen?

**Step 1: Get OAuth Token**
```python
token = oauth_client.get_token("planner", ["simulation:read"])
```

What if the OAuth Service is down?

**Step 2: Generate LLM Response**
```python
response = llm_client.chat.completions.create(...)
```

What if LM-Studio or Ollama crashes?

**Step 3: Store in Memory Service**
```python
memory_client.store_memory(agent_id, turn_id, message, session_id)
```

What if the Memory Service times out?

**Step 4: Persist in SQLite**
```python
db.store_message(session_id, turn_id, agent, role, message)
```

What happens if the disk is full or there are other write conflicts?

Any of these four example errors can lead to a system crash. Or you end up with an inconsistent state with inconsistent data. To avoid this, we implement the `IntegratedAgent`, which coordinates all services and handles errors.

## Integrated Agent Architecture

The solution for service coordination is the `IntegratedAgent`. When created, it is passed all service clients (LLM, OAuth, Tools, Memory, and Database) and a Session ID. Its main task is to coordinate all services and handle errors during every agent turn.

The `respond()` method shows how this works:

```python
def respond(self, context: List[Dict[str, str]], turn_id: int) -> str:
    # 1. Build LLM messages
    messages = [{"role": "system", "content": self.config.system_prompt}]
    for msg in context:
        messages.append({
            "role": "user",
            "content": f"[{msg['agent']}]: {msg['message']}"
        })

    # 2. Get LLM response
    try:
        response = self.llm_client.chat.completions.create(
            model="llama-3.1-8b-instruct",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        message = response.choices[0].message.content

        # 3. Store in Memory Service
        self.memory_client.store_memory(
            self.config.name,
            turn_id,
            message,
            self.session_id
        )

        # 4. Store in SQLite
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
        # Still persist the error!
        self.db_manager.store_message(
            self.session_id,
            turn_id,
            self.config.name,
            self.config.role,
            error_msg
        )
        return error_msg
```

The agent goes through all steps sequentially: generating the LLM response, updating the Memory Service, and persistently storing the data in SQLite. In case of errors, there is a fallback. The error message is also stored in SQLite.

This isn't perfect (we could include retries, circuit breakers, etc.), but it's much better than "hoping nothing goes wrong." 😄

## Database Schema

Now that the `IntegratedAgent` coordinates all services, we need a clear structure for persistent storage. **SQLite** is our Single Source of Truth. Everything that happens in the system ends up here. But "storing everything" is not a schema and could quickly get out of hand. We need a structure that can track sessions, messages, and tool usage.

This will become the central Audit Log for everything that happens. An Audit Log is a monitoring protocol and contains a chronological record of all activities and events within a software system, an application, etc.

This is important because it allows us to debug more effectively. It also serves compliance. In real systems, you must be able to prove what happened.

In our case, it will log the following:

* Which agent wrote which message and when?
* Which tool was called with which parameters?
* Which session ran from when to when?
* Were there errors, and if so, where or what kind?

We will track three different data types in tables. First, the **sessions** Table:

**Sessions Table:**
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    num_turns INTEGER,
    status TEXT
)
```

A **Session** corresponds to an entire heist run. The table tracks when the simulation started, when it ended, how many turns occurred, and whether the session is still active.

Next is the **Messages** Table, which shows us who said what, when.

**Messages Table:**
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    turn_id INTEGER,
    agent_name TEXT,
    agent_role TEXT,
    message TEXT,
    timestamp TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
```

Every single agent message is stored in this table.

The third and final table is the **Tool usage** Table.

**Tool Usage Table:**
```sql
CREATE TABLE tool_usage (
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
```

This table tells us who used which tool with which parameters and whether it worked.

## Database Manager

Now we have the schema, but the agents shouldn't have to deal with SQL statements. The `DatabaseManager` encapsulates all DB operations and provides a clean API.

**Important Methods** of the `DatabaseManager`:
- `create_session(session_id)` - Creates a new session
- `store_message(session_id, turn_id, agent, role, message)` - Stores agent messages
- `store_tool_usage(session_id, turn_id, agent, tool, params, result)` - Logs tool calls
- `end_session(session_id, num_turns)` - Closes the session

Here is the example `store_message()` method.

```python
def store_message(self, session_id: str, turn_id: int,
                 agent_name: str, agent_role: str, message: str):
    cursor = self.connection.cursor()
    cursor.execute("""
        INSERT INTO messages (session_id, turn_id, agent_name,
                             agent_role, message, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, turn_id, agent_name, agent_role,
          message, datetime.now().isoformat()))
    self.connection.commit()
```

The agent simply calls `store_message()`, and the manager handles SQL, timestamps, and commits.

## Memory Service

In addition to SQLite as the persistent database, we also need a **Memory Service** for fast context access during runtime. SQLite is perfect for audit trails and long-term persistence, but for quick in-memory operations during a session, we need something lightweight.

The Memory Service runs on port 8005 and offers two central functions:

**1. Store Memory:**
```python
@app.post("/tools/store_memory")
async def store_memory(request: StoreMemoryRequest):
    # Speichert Agent-Messages in einer In-Memory-Datenstruktur
    memory_entry = {
        "turn_id": request.turn_id,
        "message": request.message,
        "timestamp": datetime.now().isoformat()
    }
    memory_store[agent_id][session_id].append(memory_entry)
```

**2. Retrieve Compressed Memory:**
```python
@app.post("/tools/get_compressed_memory")
async def get_compressed_memory(request: GetCompressedMemoryRequest):
    # Holt die letzten N Messages für einen Agent
    recent_memories = memories[-recent_count:]
    summary = "\n".join([f"Turn {m['turn_id']}: {m['message'][:100]}..."
                         for m in recent_memories])
    return {"summary": summary}
```

The Memory Service is intentionally kept simple: it stores everything in a Python Dictionary (`memory_store`). This is perfectly sufficient for our demo. In production, Redis or similar would be used.

**Important:** The Memory Service complements SQLite but does not replace it. SQLite remains the Single Source of Truth. The Memory Service is only for fast runtime access.

## The Orchestrator

We now have all the individual parts together. The `IntegratedAgent` coordinates services, the `DatabaseManager` stores data persistently, the `ServiceHealthChecker` checks services, and the `Memory Service` provides fast context access. Someone still needs to bring all of this together and orchestrate it. This is where the `Orchestrator` comes in.

The `Orchestrator` is the central coordinator (implemented in the file `integrated_system.py`) and goes through the following steps:

1. **Load Config:** Reads the system configuration with all agent definitions and service URLs
2. **Create Session:** Generates a unique Session ID (e.g., `heist_20250116_143052`) and creates it in the database
3. **Check Services:** Checks if OAuth, Memory Service, and all Tools are reachable (Fail Fast!)
4. **Initialize Clients:** Creates LLM, OAuth, Tool, Memory, and Database Clients
5. **Create Agents**: Instantiates all agents with their service dependencies and the Session ID
6. **Execute Conversation**: Lets the agents talk to each other in defined turns
7. **End Session**: Closes the session in the database

The `Orchestrator` is essentially the `main()` function of our entire service ecosystem.

Let's look at the most important parts in detail.

### Service Health Checks

Before we begin the actual orchestration, we must ensure that all services are reachable. We want to Fail Fast, not Fail Late. If the OAuth Service is down, we want to know it at system startup, not after the first agent tries to fetch a token and fails.

The `ServiceHealthChecker` checks if services are reachable:

```python
class ServiceHealthChecker:
    @staticmethod
    def check_service(url: str, service_name: str) -> bool:
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
```

The Service Health Check is executed at startup via the `_check_services()` method:

```python
def _check_services(self):
    checker = ServiceHealthChecker()

    # OAuth service
    checker.check_service(
        self.config.oauth_service['base_url'],
        "OAuth Service"
    )

    # Memory service
    checker.check_service(
        self.config.memory_service['base_url'],
        "Memory Service"
    )

    # Tool services
    for tool_name, service_config in self.config.tool_services.items():
        url = f"http://{service_config['host']}:{service_config['port']}"
        checker.check_service(url, f"Tool Service ({tool_name})")
```

The output might look like this:

```bash
🏥 Checking service health...
✅ OAuth Service is healthy
✅ Memory Service is healthy
❌ Tool Service (calculator) is unreachable: Connection refused
⚠️  System starting with degraded services
```

You immediately see which services are running and which are not. This saves time.

### Session Management

The core of the integration is the Session ID. An ID that is generated at system startup and passed through all services:

```python
def __init__(self, config_path: str):
    # Generate session ID
    self.session_id = f"heist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create session in database
    self.db_manager.create_session(self.session_id)

    # Pass session_id to all agents
    for agent_config in self.config.agents:
        agent = IntegratedAgent(
            agent_config,
            self.llm_client,
            self.oauth_client,
            self.tool_client,
            self.memory_client,
            self.db_manager,
            self.session_id  # <- Session ID durchgereicht
        )
```

We must be able to distinguish between different sessions. If we start the system again tomorrow, that's a new session. The messages should not be mixed with today's.

With Session IDs, we can:
- Track multiple heist runs in parallel
- Analyze historical sessions
- Compare A/B tests of different agent configurations
- Isolate debug logs for a specific session

The Session ID flows into all service calls:

```python
# Memory Service
memory_client.store_memory(agent_id, turn_id, message, self.session_id)

# SQLite
db_manager.store_message(self.session_id, turn_id, agent, role, message)

# Tool Usage
db_manager.store_tool_usage(self.session_id, turn_id, agent, tool, params, result)
```

This creates a consistent Audit Trail across all services.

### Orchestrator Implementation

The `Orchestrator` brings everything together:

```python
class Orchestrator:
    def __init__(self, config_path: str):
        # Load config
        self.config = ConfigLoader.load_config(config_path)

        # Generate session ID
        self.session_id = f"heist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize database
        self.db_manager = DatabaseManager(self.config.database['path'])
        self.db_manager.create_session(self.session_id)

        # Check service health
        self._check_services()

        # Initialize clients
        self.llm_client = OpenAI(...)
        self.oauth_client = OAuthClient(...)
        self.tool_client = ToolClient(...)
        self.memory_client = MemoryServiceClient(...)

        # Create agents
        self.agents = {}
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
```

The Conversation Logic is simple because the complexity has been shifted to the agents:

```python
def run_conversation(self, num_turns: int = None):
    turn_counter = 0

    for turn in range(num_turns):
        for agent_name in turn_order:
            turn_counter += 1
            agent = self.agents[agent_name]

            context = self.conversation_history[-5:]
            response = agent.respond(context, turn_counter)

            message = {
                "turn": turn_counter,
                "agent": agent_name,
                "role": agent.config.role,
                "message": response
            }
            self.conversation_history.append(message)

    # End session
    self.db_manager.end_session(self.session_id, turn_counter)
```

The Run Logic no longer knows any service details. No OAuth handling, no memory management, no database persistence. Everything is encapsulated within the IntegratedAgents. Keyword: Separation of Concerns.

## What does this give us?

Finding errors becomes easier. Instead of "What happened?", we now write `SELECT * FROM messages WHERE session_id = X`. Every message is in SQLite. Every tool call. Every agent turn. With Session ID, timestamp, and agent name.

Services can fail. The system still continues to run. The checks at startup immediately show us what's missing. Every agent turn catches errors. The system degrades instead of crashing.

The state becomes consistent. One Session ID across all services. Everything is written synchronously to the memory and the database. No race conditions.

This is no longer "demo code that hopefully works." This is robust integration with monitoring, logging, and error handling.

## The Costs or DisadvanDayes

More services mean more dependencies. OAuth Service, Memory Service, SQLite, and LM Studio all must be running. If one fails, the system can block.

More Latency. An agent turn now involves an LLM Call, a Memory Service Call, and an SQLite Write. This adds up.

More Error Modes. Network Timeouts. Service Crashes. Database Locks. More things can go wrong.

For a professional application, this is the right trade-off. For a quick prototype, it might be overkill 😄 We are now clearly on the "robust" side.

## Outlook

The system is functional. But not perfect. For a real application, we would still need:

- Retry Logic with Exponential Backoff
- Circuit Breakers for failing Services
- Async Operations for parallel Writes
- Distributed Tracing with OpenTelemetry

But these are optimizations. The foundation is laid.

## Summary

We have merged individual services into an integrated system. This is the difference between "microservices that work in a vacuum" and "microservices that work together."

What we have built:
- `IntegratedAgent` that coordinates all services
- `DatabaseManager` for complete Audit Trails
- `ServiceHealthChecker` for Fail Fast behavior
- Session Management for consistent state tracking
- Error Handling for robust service integration

All services talk to each other. This is the moment when individual components become a real system.

## Usage

Quick Start

> # 1. Start Services
> ./day_16/start_services.sh
>
> # 2. Start LM Studio with Gemma (Port 1234)
> # Manually in LM Studio GUI
> 
> # 3. Execute Agent System
> python day_16/integrated_services.py
>
> # 4. Stop Services
> ./day_16/stop_services.sh