---
title: "Day 18: Session Analytics"
date: 2025-12-18
tags:
  - python
  - aoc
  - adventofcode
  - aiagents
  - analytics
toc: true
---

All documents for this post can be found in my [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_18).

Day 18 turns collected data into actionable insights. Since Day 16 we've been logging every message, every tool call, and every agent interaction in SQLite. Since Day 17 we're tracking dynamically discovered tools. But so far we've only been collecting data, never analyzing it. At least I haven't... 😄 That changes today.

## The Problem

We now have sessions in the database. Different tool configurations, different agent setups, and different runs. But how do we compare them? Which configuration works better? Which agent uses which tools most frequently? Who interacts with whom?

The data is there. We just need the tools to analyze it.

## Session Analytics

The solution is an analytics layer on top of the SQLite database. An API that compares sessions, summarizes tool usage, and visualizes agent interactions.

### What We Could Analyze

* **Session Comparison**: Put different runs side by side. Which had more turns? Which was more successful?
* **Tool Usage Patterns**: Which tools are used how often? What's the success rate? Which agent uses which tool?
* **Agent Activity**: How active is each agent? Who talks the most? Who the least?
* **Interaction Matrix**: Who follows whom in the conversation? Which agent pairs interact most frequently?
* **Success Metrics**: Completion rate across all sessions. Average turns per session. Tool success rates.
* ...

Do you have any other ideas for useful analyses or metrics?

Let's move on to the implementation.

## SessionAnalytics Class

The `SessionAnalytics` class encapsulates all database queries:

```python
class SessionAnalytics:
    def __init__(self, db_path: str = "heist_audit.db"):
        self.db_path = db_path

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with basic info."""
        # Returns session_id, start_time, end_time, total_turns, status

    def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific session."""
        # Returns messages, tool_usage, metadata

    def get_tool_statistics(self, session_id: Optional[str] = None):
        """Get tool usage statistics."""
        # Returns per-tool: total_calls, successful_calls, success_rate

    def get_agent_activity(self, session_id: Optional[str] = None):
        """Get agent activity and interaction patterns."""
        # Returns message counts, interaction matrix

    def compare_sessions(self, session_ids: List[str]):
        """Compare multiple sessions side-by-side."""
        # Returns comparative metrics
```

Each method encapsulates an SQL query. Clean Separation of Concerns: the class knows SQL, the rest of the system doesn't.

I think I've mentioned Separation of Concerns several times now without describing it in detail. So here's a quick detour:
> **Separation of Concerns**
> Each component does one thing (well), not everything at once. Day 18 for example:
> `analytics_api.py` -> HTTP endpoints (communication)
> `session_analytics.py` -> Data logic (computations)
> `init_database.py` -> DB setup (structure)
> Each component has its task and only needs to worry about that.

Let's move on to the next methods, which also each have only one job 😉

### Tool Statistics

The tool statistics show how frequently each tool is used and how successfully:

```python
def get_tool_statistics(self, session_id: Optional[str] = None):
    cursor.execute("""
        SELECT
            tool_name,
            operation,
            COUNT(*) as total_calls,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
            AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
        FROM tool_usage
        WHERE session_id = ? OR ? IS NULL
        GROUP BY tool_name, operation
        ORDER BY total_calls DESC
    """, (session_id, session_id))
```

For each tool in the selected session we get information about:
- **total_calls**: How often was it called?
- **successful_calls**: How many calls were successful?
- **success_rate**: Success rate (0.0 to 1.0)

If `session_id` is None, we aggregate across all sessions. This shows global patterns.

### Agent Interaction Matrix

The Interaction Matrix shows who talks to whom. We'll solve this with a self-join. I didn't know about this before, so let's take a closer look.

#### Why Do We Need a Self-Join?

First, our `messages` table:

| turn_id | agent_name | message |
|---------|------------|---------|
| 1 | Planner | "Let's plan" |
| 2 | Hacker | "I'll hack" |
| 3 | Planner | "Good idea" |
| 4 | Driver | "I'm ready" |

We want to know "Who follows whom?", but each row only contains **one** agent. To see that **Hacker** follows **Planner**, we need to look at **two rows simultaneously**:
- Row 1 (Planner)
- Row 2 (Hacker)

SQL has **no "next row" function**. That's not particularly helpful when you want to know exactly that 😉

When SQL processes a row, it **cannot access the next row**. We can't program anything like this:

```sql
SELECT
    agent_name,           -- Current row
    NEXT_ROW.agent_name   -- ❌ There's no NEXT_ROW function
FROM messages
```

Such a function simply doesn't exist 🤷‍♂️.

**Without a join**, SQL only sees one row at a time:

```
SQL processing row 1:
turn_id | agent_name
--------|------------
1       | Planner    <- SQL is here and can't access row 2
```

**With a join**, we bring two rows into one combined row:

```
SQL processing combined row:
m1.turn_id | m1.agent_name | m2.turn_id | m2.agent_name
-----------|---------------|------------|---------------
1          | Planner       | 2          | Hacker         ✅ Both in ONE row!
```

Now we read the table **twice** - once for "current agent", once for "next agent":

```sql
FROM messages m1      -- First reading: "Current speaker"
JOIN messages m2      -- Second reading: "Next speaker"
ON m1.turn_id = m2.turn_id - 1  -- Connect turn N with turn N+1
```

In detail and in the implemented code, it looks like this:

```python
cursor.execute("""
    SELECT
        m1.agent_name as from_agent,    # Agent who speaks
        m2.agent_name as to_agent,      # Agent who speaks next
        COUNT(*) as interaction_count   # How often does this happen?
    FROM messages m1                    # First copy of the table
    JOIN messages m2 ON                 # Connect second copy with:
        m1.session_id = m2.session_id   # Same session AND
        AND m1.turn_id = m2.turn_id - 1 # m1 is exactly 1 turn BEFORE m2
    WHERE m1.session_id = ?             # Only for this session
    GROUP BY m1.agent_name, m2.agent_name  # Group by agent pairs
    ORDER BY interaction_count DESC     # Most frequent first
""", (session_id,))
```

Step by step in my words:
1. **FROM messages m1** - Take the messages table, call it "m1"
2. **JOIN messages m2** - Take the same table again, call it "m2"
3. **ON m1.turn_id = m2.turn_id - 1** - Connect where turn_id of m1 is exactly 1 less than m2
4. **GROUP BY m1.agent_name, m2.agent_name** - Count for each agent pair
5. **COUNT(*)** - How often does this pair occur?

And what's this all for? The Interaction Matrix shows:

1. **Dominance**: Who initiates conversations?
   - If "Planner -> X" is frequent, the Planner dominates
2. **Bottlenecks**: Are there agents who rarely respond?
   - If "X -> Communicator" is rare, they're being ignored
3. **Collaboration Patterns**: Which agents work together?
   - High counts between two agents = close collaboration
4. **Conversation Flow**: Is it circular or linear?
   - Linear: A -> B -> C -> End
   - Circular: A -> B -> C -> A -> B -> C

And so on... At least that's my idea. What I'll actually do with it, I don't know exactly yet. Some features in this project exist purely to learn a concept or tool 😄

### Session Comparison

Another important analytics function is session comparison. With this we can put different runs directly side by side and systematically compare them:

```python
def compare_sessions(self, session_ids: List[str]):
    comparisons = {
        "sessions": [],
        "tool_comparison": {},
        "agent_comparison": {}
    }

    # Basic session info
    for session_id in session_ids:
        details = self.get_session_details(session_id)
        comparisons["sessions"].append({
            "session_id": session_id,
            "total_turns": details["total_turns"],
            "message_count": details["message_count"],
            "status": details["status"]
        })

    # Tool usage comparison
    for session_id in session_ids:
        tool_stats = self.get_tool_statistics(session_id)
        comparisons["tool_comparison"][session_id] = tool_stats["tool_statistics"]

    # Agent activity comparison
    for session_id in session_ids:
        agent_activity = self.get_agent_activity(session_id)
        comparisons["agent_comparison"][session_id] = agent_activity["agent_activity"]

    return comparisons
```

This gives us sessions side by side. We immediately see:
- Which session had more turns
- Which tools were used in Session A but not in Session B
- Which agents were differently active in different sessions

This is valuable for A/B testing. When we test different tool sets (from Day 17), the comparison shows us which setup performs better.

### Success Metrics

The last important analytics function aggregates metrics across all sessions:

```python
def get_success_metrics(self):
    # Total sessions
    cursor.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cursor.fetchone()[0]

    # Completed sessions
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'completed'")
    completed_sessions = cursor.fetchone()[0]

    # Average turns
    cursor.execute("SELECT AVG(total_turns) FROM sessions WHERE total_turns > 0")
    avg_turns = cursor.fetchone()[0] or 0

    # Tool success rates
    cursor.execute("""
        SELECT
            tool_name,
            AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
            COUNT(*) as total_uses
        FROM tool_usage
        GROUP BY tool_name
        ORDER BY success_rate DESC
    """)

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "completion_rate": completed_sessions / total_sessions,
        "average_turns_per_session": round(avg_turns, 1),
        "tool_success_rates": [...]
    }
```

This gives us system-level metrics:
- **Completion Rate**: How many sessions run to completion?
- **Average Turns**: How long is a typical session?
- **Tool Success Rates**: Which tools work reliably?

These metrics show trends over time. If we improve the system, the completion rate should increase.

With this we've implemented all analytics functions at the SQLite level:
- **Tool Statistics**: Which tools are being used
- **Agent Interaction Matrix**: Who talks to whom (Self-Join!)
- **Session Comparison**: Compare runs
- **Success Metrics**: System-wide metrics

Now let's make them accessible via HTTP.

## REST API

And here comes the already familiar FastAPI. While writing this, I realize I haven't yet explained how REST API and FastAPI relate to each other. The terms are used quite frequently.

REST is an architectural style (how you design an API), while FastAPI is a Python framework (the implementation). In other words: REST is the blueprint for a house and FastAPI is the toolbox. In our case we're building a REST API with GET/POST/... and using the FastAPI framework to do it.

This makes the data available via HTTP, which opens many doors for dashboards, CLI tools, or other services that want to analyze the session data.

```python
from fastapi import FastAPI, HTTPException, Query
from day_18.session_analytics import SessionAnalytics

app = FastAPI(title="Heist Session Analytics API")
analytics = SessionAnalytics()

@app.get("/api/sessions")
async def get_sessions():
    """List all sessions."""
    sessions = analytics.list_sessions()
    return {"total": len(sessions), "sessions": sessions}

@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Get session details."""
    details = analytics.get_session_details(session_id)
    if "error" in details:
        raise HTTPException(status_code=404, detail=details["error"])
    return details

@app.get("/api/tool-stats")
async def get_tool_statistics(session_id: Optional[str] = Query(None)):
    """Tool usage statistics."""
    return analytics.get_tool_statistics(session_id)

@app.get("/api/agent-activity")
async def get_agent_activity(session_id: Optional[str] = Query(None)):
    """Agent activity patterns."""
    return analytics.get_agent_activity(session_id)

@app.get("/api/compare")
async def compare_sessions(session_ids: List[str] = Query(...)):
    """Compare multiple sessions."""
    if len(session_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 sessions")
    return analytics.compare_sessions(session_ids)

@app.get("/api/metrics")
async def get_success_metrics():
    """Overall success metrics."""
    return analytics.get_success_metrics()
```

The API runs on port 8007. All endpoints are GET (read-only), which means the database is not modified. There's a quickstart guide at the end :]

### Query Parameters

Some endpoints accept optional parameters:

**Session filter:**

```bash
GET /api/tool-stats?session_id=heist_20251218_140000
```

The above filters statistics to a specific session.

**Session comparison:**

```bash
GET /api/compare?session_ids=heist_001&session_ids=heist_002&session_ids=heist_003
```

This compares multiple sessions. The `session_ids` parameter can be repeated. With that we've covered all analytics endpoints.

## Practical Application: A/B Testing

The true power of the analytics API shows itself in systematic experimentation. Here's a hypothetical example of how you could compare different tool configurations:

**Scenario**: You want to test whether more tools lead to better results.

**Setup A**: Standard tools (calculator, file_reader)
**Setup B**: Extended tools (calculator, file_reader, database_query, simulation_data)

You run 5 sessions per setup and then query the API:

```bash
GET /api/compare?session_ids=setup_a_1&session_ids=setup_a_2&session_ids=setup_a_3&session_ids=setup_a_4&session_ids=setup_a_5&session_ids=setup_b_1&session_ids=setup_b_2&session_ids=setup_b_3&session_ids=setup_b_4&session_ids=setup_b_5
```

**Hypothetical results could show:**
- Setup B has more turns on average (agents use the extra tools)
- Setup B has a higher completion rate (more tools = more possibilities)
- `database_query` is used most frequently by the Hacker
- The Interaction Matrix shows: With more tools, agents talk to each other more often

This would be true data-driven decision making - not based on gut feeling, but on metrics.

Such systematic comparisons are especially valuable when experimenting with agent configurations, tool sets, or prompting strategies. Instead of guessing "could Setup B be better?", you have concrete numbers: "Setup B has a 23% higher completion rate with an average of 12 more turns."

## Integration with Existing System

An important aspect of Day 18 is how it integrates into the overall system... or rather **doesn't** integrate. The Analytics API is deliberately **completely decoupled** from the rest of the system.

### Read-Only Architecture

The Analytics API has only **read access** to the database:

```python
# All queries are SELECT
cursor.execute("SELECT * FROM sessions WHERE ...")
cursor.execute("SELECT COUNT(*) FROM tool_usage WHERE ...")
```

This restriction to read-only has three important consequences:

**No risk to running sessions**

Since the API only reads, it can't break anything. Even if the Analytics API crashes, fails, or executes faulty queries... the database remains unchanged. The Heist system can continue running and saving sessions meanwhile, without the Analytics API interfering.
In contrast: If a service with write access crashes while executing a transaction, the database could be left in an inconsistent state. With read-only, this risk doesn't exist.

**No side effects**

Each API call changes exactly... nothing. This has an important advantage: You can execute queries as often as you want without worry.

```bash
# Execute these calls 100 times in a row? No problem!
curl http://localhost:8007/api/sessions
curl http://localhost:8007/api/sessions
curl http://localhost:8007/api/sessions
# ... always the same result, no unwanted changes
```

In contrast to a write API, where each call changes something:
```bash
# ❌ CAUTION with write APIs:
POST /api/sessions/create  # Creates session A
POST /api/sessions/create  # Creates session B (not intended!)
POST /api/sessions/create  # Creates session C (also not intended!)
```

**Predictable and reproducible**

The same call always returns the same result (as long as no new sessions are added). If you call `/api/sessions` today and get 10 sessions, and call it again tomorrow (without new sessions), you'll get exactly the same 10 sessions again.
This makes debugging easy: You can repeat an API call that delivers an unexpected result as often as you want without the result changing. The behavior is deterministic.
In API development this is called **idempotent** (I learned this too, yay!), a property that's especially important for GET requests. The HTTP specification even says: "GET requests MUST be safe and idempotent."

### Independent Lifecycle

The Analytics API has a completely independent lifecycle. It's not tied to the runtime of the Heist system and can be operated completely independently. This shows in four aspects:

**Parallel to the Heist system**

You can run both services simultaneously:
```bash
# Terminal 1: Heist system
./day_16/start_services.sh

# Terminal 2: Analytics API
./day_18/start_analytics.sh

# Both run independently, only sharing the database
```

**Start/stop anytime**

Unlike the Heist system, which shouldn't be interrupted during a session, you can start and stop the Analytics API at will:

```bash
./start_analytics.sh   # Start
# Make queries...
CTRL+C                 # Stop
# Heist system continues running, Analytics stopped
./start_analytics.sh   # Start again - everything works
```

This is possible because the API is stateless.

**Own port, no conflicts**

Port 8007 is dedicated to Analytics. The Heist system uses the following services:
- Port 1234 - LM Studio
- Port 8001 - OAuth Service
- Port 8005 - Memory Service
- Port 8006 - Discovery Server

No overlaps. You could even run multiple Analytics API instances on different ports.

**Minimal dependencies**

The only dependency is SQLite, a file-based database without its own server. No external database, no message queues, and no Redis cache. Just Python, FastAPI, and SQLite.

This makes deployment simple. You copy the `day_18/` folder along with `heist_audit.db` to another server, start `./start_analytics.sh` and you're done. No complex infrastructure necessary.

You could even run the API on a separate server with read-only access to a replicated database. Or only start it on demand when you want to analyze data.

### Separation of Concerns in Action

The Analytics layer knows **only** the database structure:

```python
class SessionAnalytics:
    def __init__(self, db_path: str = "heist_audit.db"):
        self.db_path = db_path  # That's all!
```

It knows nothing about:
- ❌ Agents and their implementation
- ❌ LLM APIs or prompts
- ❌ OAuth authentication
- ❌ Discovery servers
- ❌ Memory services

It only knows:
- ✅ Tables: `sessions`, `messages`, `tool_usage`
- ✅ Columns: `session_id`, `tool_name`, `success_rate`
- ✅ SQL queries

This is Separation of Concerns. We could completely rewrite the Heist system. As long as the database structure remains the same, the Analytics API continues to work.

This decoupling brings several advantages:

* **Stability**: Analytics API can't crash if the Heist system has problems
* **Performance**: Queries don't block the main system
* **Maintainability**: Changes to Analytics don't affect the Heist system
* **Reusability**: The API could analyze other sessions too, not just from the Heist system

This is a pattern that has proven itself in many production systems: **Operational Database** (for running sessions) separate from **Analytics Database** (for analysis).

## Demo

After going through the architecture and implementation, let's look at how the API actually runs and what it returns.

### Starting the Server

The API is started with a simple script:

```bash
cd day_18
./start_analytics.sh
```

The server starts on port 8007 and shows all available endpoints:

```bash
================================================================================
Starting Day 18: Analytics API Server
================================================================================

📊 Endpoints available:
   GET  http://localhost:8007/         - API Info
   GET  http://localhost:8007/health   - Health Check
   GET  http://localhost:8007/api/sessions
   GET  http://localhost:8007/api/sessions/{id}
   GET  http://localhost:8007/api/tool-stats
   GET  http://localhost:8007/api/agent-activity
   GET  http://localhost:8007/api/compare?session_ids=...
   GET  http://localhost:8007/api/timeline/{id}
   GET  http://localhost:8007/api/metrics

================================================================================

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8007
```

### Example: Fetching Success Metrics

We query the system-wide metrics:

```bash
curl http://localhost:8007/api/metrics | python3 -m json.tool
```

The API responds with a structured JSON object:

```json
{
  "total_sessions": 3,
  "completed_sessions": 3,
  "completion_rate": 1.0,
  "average_turns_per_session": 45.0,
  "tool_success_rates": [
    {"tool_name": "search_memory", "success_rate": 1.0, "total_uses": 3},
    {"tool_name": "execute_action", "success_rate": 1.0, "total_uses": 3},
    {"tool_name": "create_plan", "success_rate": 1.0, "total_uses": 3},
    {"tool_name": "communicate", "success_rate": 1.0, "total_uses": 3},
    {"tool_name": "analyze", "success_rate": 1.0, "total_uses": 3}
  ]
}
```

And what does this mean?

* **100% Completion Rate** - All 3 sessions were successfully completed
* **Average 45 Turns** - A typical session takes about 45 interactions
* **Perfect Tool Success Rates** - All tools work reliably (1.0 = 100%)
* **Even Tool Usage** - Each tool was used exactly 3 times (once per session)

Such metrics give a quick overview of system health. In a production system we'd look for trends. Is the completion rate increasing? Which tools have low success rates and need improvement? Etc...

### Example: Comparing Sessions

Another practical example, comparing two sessions directly:

```bash
curl 'http://localhost:8007/api/compare?session_ids=demo_session_001&session_ids=demo_session_002' | python3 -m json.tool
```

The response shows a side-by-side comparison:

```json
{
  "sessions": [
    {
      "session_id": "demo_session_001",
      "total_turns": 45,
      "message_count": 3,
      "status": "completed"
    },
    {
      "session_id": "demo_session_002",
      "total_turns": 38,
      "message_count": 3,
      "status": "completed"
    }
  ],
  "tool_comparison": {
    "demo_session_001": [...],
    "demo_session_002": [...]
  },
  "agent_comparison": {
    "demo_session_001": [...],
    "demo_session_002": [...]
  }
}
```

Session 001 had 45 turns, session 002 only 38, even though both are completed. Why? With the detailed data in `tool_comparison` and `agent_comparison` you can analyze which tools were used differently.

This kind of comparison is worth its weight in gold when experimenting with different configurations.

## Summary

Day 18 closes an important gap. We've been collecting data since Day 16, but never systematically analyzed it. That changes today. Even though this is just a constructed problem and solution to learn concepts and methods 😃

### What Did We Build?

**The Analytics Layer**

We built a complete analytics infrastructure on top of the existing SQLite database:

* **SessionAnalytics Class** - Encapsulates all SQL queries and aggregation logic
  * Tool Statistics: Which tools are used, how successful are they?
  * Agent Interaction Matrix: Who talks to whom? (with Self-Join deep-dive)
  * Session Comparison: Compare runs directly
  * Success Metrics: System-wide metrics

* **REST API with FastAPI** - Makes the analytics available via HTTP
  * 7 GET endpoints for different analyses
  * Read-only: No side effects, safe
  * Port 8007: Independent of the Heist system
  * Stateless: Can be started/stopped anytime

### Why Is This Important?

**Data-Driven Decisions**

Without analytics we're flying blind. With Day 18 we can objectively measure and make data-driven decisions:
* Which tool configuration works better?
* Which agents are bottlenecks?
* Is the success rate increasing over time?

**Enabling A/B Testing**

Session comparison makes systematic experimentation possible. You can test different setups and decide based on real data, not gut feeling.

**Separation of Concerns**

The Analytics API is a prime example of clean architecture (nice that I'm saying that myself 😅):
* Completely decoupled from the Heist system
* Only knows the database structure
* Read-only: No risk to running sessions
* Can run on a separate server

### What's Next?

With Day 18 we've laid the foundation for data-driven work. In the next days we could tackle the following topics:
* Visualization of metrics (Grafana, custom dashboard)
* Alerting on low success rates
* Trend analysis over time
* Machine learning on session data

We now have the tools to understand what's happening in our system. No more guessing, just data.

---

## Usage

### Quick Start

```bash
# 1. Navigate to day_18 directory
cd day_18

# 2. Start Analytics API
./start_analytics.sh

# In a NEW terminal:

# 3. Health check
curl http://localhost:8007/health | python3 -m json.tool

# 4. List all sessions
curl http://localhost:8007/api/sessions | python3 -m json.tool

# 5. Session details
curl http://localhost:8007/api/sessions/demo_session_003 | python3 -m json.tool

# 6. Tool statistics
curl http://localhost:8007/api/tool-stats | python3 -m json.tool

# 7. Agent activity
curl http://localhost:8007/api/agent-activity | python3 -m json.tool

# 8. Compare sessions
curl "http://localhost:8007/api/compare?session_ids=demo_session_001&session_ids=demo_session_002" | python3 -m json.tool

# 9. Success metrics
curl http://localhost:8007/api/metrics | python3 -m json.tool

# Stop server: CTRL+C in the terminal where the server is running
```

**Tip:** Use `| python3 -m json.tool` at the end of each curl command for formatted JSON output!

The database already contains 3 demo sessions (`demo_session_001`, `demo_session_002`, `demo_session_003`) that you can use immediately for testing - see the examples in the "Demo" chapter.
