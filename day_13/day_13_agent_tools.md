# Tag 13: Agent Tools - Specialized Agent Capabilities

Today's challenge moves beyond simple conversation to **specialized agent capabilities**. Up to now, our agents were essentially equal. They all had the same basic abilities to chat and remember. But real teams aren't like that, hopefully. The safecracker knows things about time locks that the planner doesn't. The hacker has access to building blueprints that others can't read. The mole can query security schedules in ways that outsiders can't.

This is where (Agent) Tools come in. Instead of every agent being a generic chatbot, we're giving them specialized capabilities that make them genuinely different from each other. The safecracker gets a calculator for safe timing and mechanism calculations. The hacker gets file access tools to read technical blueprints. The mole gets database query capabilities to check guard rotations.

But here's the key question. How do we actually enforce these specializations? How do we make sure the safecracker can't just decide to read files, or the hacker can't access the database? This is where our OAuth security model comes back into play.

There's an important difference from our earlier OAuth implementation (days eight to ten). Previously, we used OAuth to control **API access**. This determined which agents could call which services. Now we're going to use OAuth to control **tool capabilities**. This determines which computational tools each agent can use within conversations. It's the difference between "Can you access the simulation service?" versus "Can you perform mathematical calculations?" The OAuth security model remains the same, but we're applying it to a different layer of specialization.

**Why does that even matter?** In most multi-agent demonstrations, the differentiation between agents is purely cosmetic. I'm talking of different system prompts that make them talk differently, but still having fundamentally the same underlying capabilities. 

Real specialization comes from **access to different tools and data sources**. This is what transforms an LLM chatbot into an actual agent. A financial analyst doesn't just "think differently" about numbers. They have access to Bloomberg terminals, financial databases, and calculation tools that others don't. A security expert doesn't just "talk about security". They can run port scans, analyze network traffic, and access security systems and so on.

This creates natural **information asymmetries and dependencies**. When only the hacker can read the building blueprints, the other agents have to trust their interpretation. When only the insider can check the guard schedule, they become the bottleneck for timing decisions. This is closer to how real teams actually function.

Let's start with implementing this. The approach is straightforward ...

## Implementation Strategy

Like in the days before, you can find the files in my repository.

We're implementing tools using a decorator pattern (@tool) that makes capabilities explicit.

```python
@tool("calculator")
def calculate(expression: str) -> str:
    """Evaluates mathematical expressions"""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool("file_reader")
def read_file(filename: str) -> str:
    """Reads technical documents and blueprints"""
    blueprints = {
        "bank_layout.txt": "Main vault: Steel door, 3-hour time lock...",
        "security_system.txt": "Motion sensors: Zones A-F, backup power...",
    }
    return blueprints.get(filename, "File not found")
```

Each agent gets a different set of tools based on their role.
- **Safecracker Agent**: Calculator for timing calculations, safe mechanisms (I have no idea, if that's needed to crack a safe 😄)
- **Hacker Agent**: File access for blueprints, technical documents
- **Mole Agent**: Database queries for schedules, personnel info (but sabotages subtly)
- **Planner Agent**: No tools (coordinates others, pure strategy)

### OAuth-Protected Tool Implementation

But here's the critical question: How do we actually enforce that only the safecracker can use the calculator, and only the hacker can read files? We could build complex permission checking into every tool function, but that would make the code messy and error-prone.

Instead, we use FastAPI's dependency injection system that handles all the security automatically. The security magic happens through a dependency factory function:

```python
def require_scope(required_scope: str):
    """Decorator to require specific OAuth scope"""
    def scope_checker(auth_info: dict = Depends(validate_token)):
        if required_scope not in auth_info["scopes"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_scope}"
            )
        return auth_info
    return scope_checker
```

This dependency factory creates **functional authorization**. Instead of checking "Can you access this service?", it checks "Can you perform this specific function?". Each tool endpoint uses it:

```python
@app.post("/tools/calculator")
def calculator_tool(
    request: CalculatorRequest,
    auth_info: dict = Depends(require_scope("calculator:use"))
):
```

The Safecracker gets a JWT token with `["calculator:use"]` scope. The Planner gets `[]` (no tools). When the Planner tries to use the calculator, the dependency injection blocks access before the function even runs. Clean, automatic, and invisible to the agent code.

Each tool implementation follows the same pattern. Here's the calculator as example:

```python
@app.post("/tools/calculator", response_model=ToolResponse)
def calculator_tool(
    request: CalculatorRequest,
    auth_info: dict = Depends(require_scope("calculator:use"))
):
    try:
        # Basic safety check
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in request.expression):
            raise ValueError("Only basic math operations allowed")
        
        result = eval(request.expression)
        
        return ToolResponse(
            success=True,
            result=f"Calculation: {request.expression} = {result}",
            tool_used="calculator",
            agent=auth_info["agent"]
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            error=f"Calculation error: {str(e)}",
            tool_used="calculator", 
            agent=auth_info["agent"]
        )
```

**What makes this implementation interesting?** The `response_model=ToolResponse` ensures every response has the same structure with `success`, `result`, `error`, `tool_used`, and `agent` fields. This creates a built-in audit trail since every response includes `agent=auth_info["agent"]` so we know who used what. Input validation only allows safe mathematical expressions, preventing arbitrary code execution. Consistent error handling wraps success and failure in structured responses. And the tool logic doesn't need to worry about authentication since OAuth is handled transparently by the dependency injection.

The same pattern applies to file_reader and database_query tools. Each gets its own scope (`file_reader:use`, `database_query:use`) and the dependency injection handles all security automatically.

## OAuth Agent Workflow

Now let's look at how these individual components work together in the complete agent workflow. The real complexity emerges when agents authenticate, discover their tools, and start using them in actual conversations.

The complete flow shows how OAuth agents work with tools:

```mermaid
sequenceDiagram
    participant System as System
    participant ToolService as Tool Service
    participant Agent as Agent
    participant Tools as OAuth Tools
    
    Note over System, Tools: 1. Service Health Check
    System->>ToolService: Check if tool service is running
    ToolService-->>System: Service available
    
    Note over System, Tools: 2. Agent Creation & Auto-Authentication
    System->>Agent: Create agent with role
    Agent->>ToolService: Authenticate with credentials
    ToolService-->>Agent: JWT token with role-specific scopes
    Note right of Agent: Safecracker: ["calculator:use"]<br/>Hacker: ["file_reader:use"]<br/>Mole: ["database_query:use"]<br/>Planner: []
    
    Note over System, Tools: 3. Dynamic Tool Discovery
    Agent->>ToolService: Query available tools
    ToolService-->>Agent: Return tools based on JWT scopes
    
    Note over System, Tools: 4. Natural Language Tool Integration
    Agent->>Agent: Generate response with [OAUTH_TOOL:tool_name:param]
    System->>System: Regex parser converts to tool calls
    
    Note over System, Tools: 5. Tool Execution with Permission Enforcement
    System->>Tools: Execute tool call with JWT token
    alt Authorized
        Tools-->>System: Tool result with audit info
    else Unauthorized
        Tools-->>System: (attempted tool_name access - unauthorized)
    end
    
    Note over System, Tools: 6. Conversation Flow with OAuth Audit
    System->>System: Log all tool calls with agent identity
    System->>Agent: Continue conversation with tool results
```

**1. Service Health Check**
Before agents start, the system checks if the tool service is running. No tool service means no OAuth-protected tools.

**2. Agent Creation & Auto-Authentication** 
Each agent automatically authenticates with the tool service and gets JWT tokens with specific scopes:
```python
# safecracker gets: ["calculator:use"]
# hacker gets: ["file_reader:use"] 
# mole gets: ["database_query:use"]
# planner gets: [] (no tools)
```

**3. Dynamic Tool Discovery**
After authentication, each agent queries the tool service for available tools. This is dynamic based on JWT scopes.

**4. Natural Language Tool Integration**
Agents use `[OAUTH_TOOL:tool_name:parameter]` syntax in their responses. A regex parser automatically converts these into real tool calls.

**5. Silent Permission Enforcement**
Unauthorized access is handled elegantly. Instead of error messages, there are subtle notations: `(attempted file_reader access - unauthorized)`.

**6. Conversation Flow with OAuth Audit**
8 turns with 4 agents, all tool calls logged with agent identity for complete audit trails.

## OAuth Implementation Results

The OAuth-protected conversation (`day_13_oauth_tools.py` + `tool_service.py`) demonstrates sophisticated behavioral patterns. You can read the results in the repository as well as the code producing this result. Here is the summary:

All agents authenticated successfully with JWT tokens across 8 turns with 4 agents. Role-based permissions were strictly enforced with the Planner having 0 tools, while the Safecracker, Hacker, and Mole each had access to exactly 1 specialized tool. The agents received scoped access tokens including `calculator:use`, `file_reader:use`, and `database_query:use` based on their roles.

The system demonstrates realistic delegation patterns throughout the conversation:
```bash
Planner: "Hacker, I need you to analyze the blueprints of the vault. Can you use [your file access] to get a comprehensive understanding..."
Planner: "Safecracker, can you estimate the time required to open the vault door?"
Planner: "Mole, could you analyze the security schedules? I need to know when guards are on duty..."
Safecracker: Calculator (OAuth): Calculation: 60/2 = 30.0 ✅ (refining timing estimates)
Hacker: File_Reader (OAuth): File 'vault_blueprint.pdf' not found. Available files: bank_layout.txt, security_system.txt, timing_specs.txt ✅
```

The OAuth system creates natural conversation flow. Agents understand their tool limitations and explicitly delegate tasks to specialists instead of attempting unauthorized access. This produces much more realistic multi-agent coordination.

Looking at the individual agent behaviors reveals how role-based coordination actually works in practice. The **Planner** demonstrates authentic coordination by explicitly delegating tasks based on tool capabilities. Instead of attempting unauthorized access, the Planner asks "Hacker, I need you to analyze the blueprints" and "Safecracker, can you estimate the time required" showing realistic awareness of team specializations.

The **Safecracker** provides detailed timing analysis using calculator access. For example, calculating `60/2 = 30.0` for refined timing estimates and explaining multiple scenarios with mathematical precision based on vault complexity assumptions.

The **Hacker** systematically analyzes available technical files after discovering that specific blueprints aren't available. The agent focuses on security_system.txt, timing_specs.txt, and bank_layout.txt to extract actionable technical intelligence about vulnerabilities and system architecture.

The **Mole** introduces subtle sabotage through legitimate database access. Instead of failed attempts, the agent highlights "redundant entries" and "inconsistencies in how personnel are listed" while appearing helpful and thorough in their database queries.

These individual specializations create natural information dependencies throughout the conversation. The conversation demonstrates authentic team coordination patterns. Each agent recognizes their limitations and actively delegates to appropriate specialists. The Planner becomes a true coordinator who synthesizes information from three domain experts, creating realistic interdependencies where no single agent has complete operational capability.

### Tool Specialization in Practice

The OAuth conversation demonstrates how tool-based specialization creates authentic agent differentiation. Each agent becomes genuinely unique through their capabilities rather than just their personality.

The **Calculator Tool** enables the Safecracker to provide precise mathematical analysis: *"I'm using the calculator to estimate that a robust combination lock... will likely require at least 45-90 minutes to crack."* The tool transforms vague estimates into specific calculations with `Calculator (OAuth): Calculation: 60/2 = 30.0` showing real computational work.

The **File Reader Tool** gives the Hacker exclusive access to technical intelligence: *`File_Reader (OAuth): File 'vault_blueprint.pdf' not found. Available files: bank_layout.txt, security_system.txt, timing_specs.txt`* This creates information asymmetries where only the Hacker knows what files exist and what they contain.

The **Database Query Tool** makes the Mole the team's intelligence analyst: *"I can access information about personnel schedules and security protocols through the following queries..."* The agent becomes essential for operational timing and security assessments that others cannot perform.

The OAuth system creates **functional specialization** where agents become genuinely different rather than just talking differently. Each tool creates unique capabilities that transform conversation dynamics. The Planner must coordinate specialists rather than attempting everything alone. The specialists become essential bottlenecks for their domains.

An interesting side effect emerges with the Mole's behavior. Having legitimate database access enables sophisticated deception: *"If that doesn't work (and it might be a good excuse to subtly delay things), I'll request the security_system.txt files..."* The agent uses its authorized tools to introduce delays and uncertainty while maintaining plausible cover. This shows how tool-based specialization can enable both collaboration and deception through the same mechanisms.

## Fazit

Real agent differentiation comes from **what they can do**, not just **how they talk**. Tools create natural information dependencies that drive authentic coordination patterns. The OAuth audit trail captures every tool interaction, providing complete operational transparency while maintaining seamless conversation flow.

The OAuth security model creates realistic multi-agent dynamics through role-based capabilities rather than behavioral restrictions. Agents naturally develop interdependencies when they understand their limitations, leading to authentic team coordination patterns. This foundation enables more sophisticated multi-agent systems where specialization creates value rather than frustration.