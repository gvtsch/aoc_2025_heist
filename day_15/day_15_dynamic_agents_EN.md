# Day 15: Dynamic Agent System - Configuration over Hardcoding

On Day 15, it's time to let our multi-agent system grow up. So far, we've hardcoded four agents in the code. Planner, Hacker, Safecracker, and Mole, all hardwired with their respective roles, tools, and permissions. It works, no question. But it doesn't scale well, isn't flexible, and doesn't exactly make A/B testing easier.

Imagine you want to add a fifth agent. Or test different system prompts for various agents. Or try different tool combinations. With hardcoded agents, that means code changes, new commits, and deployments every time. That's annoying and error-prone.

It gets even worse when we want to test different team constellations. Four agents work well, but what about three? Or six? Which agent should be the saboteur? The mole is obvious, but what if the hacker sabotages? Every variation requires code changes again.

And then there's the OAuth problem. Every agent needs its permissions, its scopes, its tools. If you want to change tool distribution, you have to dig deep into the code. That's not agile development anymore, that's waterfall.

The good news... there's a solution 😀 **Configuration over Code**. Agents should be loaded from a configuration file, not defined in code. Team changes should require editing a YAML file, not a code commit. And that's exactly what we're building today.

## The Idea: Agents as Configuration

The concept is simple but brings many advantages. Instead of defining agents in code, we write a YAML file with all agent definitions. Each agent gets its own configuration. For example, Planner and Hacker become:

```yaml
agents:
  - name: "planner"
    role: "Strategic Heist Planner"
    tools: []
    oauth_scopes: []
    system_prompt: "You are a strategic heist planner..."
    is_saboteur: false

  - name: "hacker"
    role: "Technical Security Expert"
    tools: ["file_reader:use"]
    oauth_scopes: ["simulation:read", "file_reader:use"]
    system_prompt: "You are a technical security expert..."
    is_saboteur: false
```

The system reads this config at startup and automatically creates all agents with their respective properties. And if you want a new or additional agent, you simply add a new entry. And if you want to change tool permissions, well, you just change the corresponding `tools` entry. The same applies to different system prompts, etc., etc.

This brings a few advantages:
* **Flexibility**: We can add or remove any number of agents without changing code.
* **A/B Testing**: Different config files for different experiments. We can test new agents or prompts without touching the code.
* **Version Control**: All agent changes are traceable in Git through config diffs. Admittedly, they would be too if I changed them in code, but it doesn't make things clearer.
* **Environment Separation**: We can dynamically switch between a development config with three agents and a "production" config with the full team.

Ultimately, this is the difference between a simple, rigid prototype and a flexible platform.

## Implementation

The implementation consists of multiple layers. First, we need a **ConfigLoader** that parses YAML and converts it into clean Python objects. Then a **DynamicAgent** that's created entirely from the config. And finally, a **DynamicAgentSystem** that orchestrates everything.

Let's start with the data structures. We use Python's `dataclasses` for clean, type-safe configuration. `Dataclasses` enable clear separation of data and logic, which facilitates dynamic agent creation from YAML configurations. There are even automatically generated methods like `init`, `repr`, and `eq` and other standard methods. I don't have to implement these methods error-free myself anymore 😄

```python
@dataclass
class AgentConfig:
    name: str
    role: str
    tools: List[str]
    oauth_scopes: List[str]
    system_prompt: str
    is_saboteur: bool

@dataclass
class SystemConfig:
    agents: List[AgentConfig]
    oauth_service: Dict[str, Any]
    tool_services: Dict[str, Dict[str, Any]]
    llm: Dict[str, Any]
    memory_service: Dict[str, Any]
    session: Dict[str, Any]
```

The `ConfigLoader` reads the YAML file and creates these structures.

```python
class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> SystemConfig:
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
            session=config_data['session']
        )
```

This looks more elaborate than it actually is and is just boilerplate code. One of the big advantages: We validate the config at load time. Faulty YAML files are detected immediately, not at runtime when an agent tries to respond for the first time.

## Dynamic Agents

The interesting part comes with agent creation. A `DynamicAgent` is built entirely from its `AgentConfig`. And here a custom-programmed class comes into play.

```python
class DynamicAgent:
    def __init__(
        self,
        config: AgentConfig,
        llm_client: OpenAI,
        oauth_client: OAuthClient,
        tool_client: ToolClient
    ):
        self.config = config
        self.llm_client = llm_client
        self.oauth_client = oauth_client
        self.tool_client = tool_client
        self.conversation_history: List[Dict[str, str]] = []
        self.oauth_token: Optional[str] = None

        # Get OAuth token if scopes are configured
        if self.config.oauth_scopes:
            self.oauth_token = self.oauth_client.get_token(
                self.config.name,
                self.config.oauth_scopes
            )
```

The agent gets its config complemented by three clients: LLM, OAuth, and Tools. If the config defines OAuth scopes, the agent automatically fetches a token. No more manual auth management, everything happens transparently based on configuration.

The `respond()` method is part of the `DynamicAgent` class and uses the config for system prompts and tool information:

```python
def respond(self, context: List[Dict[str, str]]) -> str:
    messages = [{"role": "system", "content": self.config.system_prompt}]

    for msg in context:
        messages.append({
            "role": "user",
            "content": f"[{msg['agent']}]: {msg['message']}"
        })

    if self.config.tools:
        tool_info = f"\n\nAvailable tools: {', '.join(self.config.tools)}"
        messages.append({"role": "system", "content": tool_info})

    response = self.llm_client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content
```

The agent is dumb in the best sense. It knows nothing about its role, its tools, or its permissions. It reads everything from the config. This makes it extremely flexible because the same agent class can represent any agent.

If you stumbled over the `messages` list after we already implemented shared message storage... The `messages` list is just temporary formatting for the LLM API call, not persistent storage. The agent itself has no conversation history of its own – the central history resides in the `DynamicAgentSystem` with information compression (last 5 messages).

## System Orchestration

The `DynamicAgentSystem` finally brings everything together. It loads the config, initializes the clients, and creates all agents:

```python
class DynamicAgentSystem:
    def __init__(self, config_path: str):
        self.config = ConfigLoader.load_config(config_path)

        # Initialize LLM client
        self.llm_client = OpenAI(
            base_url=self.config.llm['base_url'],
            api_key=self.config.llm['api_key']
        )

        # Initialize OAuth and Tool clients
        self.oauth_client = OAuthClient(self.config.oauth_service)
        self.tool_client = ToolClient(self.config.tool_services)

        # Create agents dynamically
        self.agents: Dict[str, DynamicAgent] = {}
        for agent_config in self.config.agents:
            agent = DynamicAgent(
                agent_config,
                self.llm_client,
                self.oauth_client,
                self.tool_client
            )
            self.agents[agent_config.name] = agent

        self.conversation_history: List[Dict[str, str]] = []
```

The conversation logic remains identical to before. Agents respond one after another, messages are logged, history is stored. The only difference: The agents now come from config instead of being hardcoded.

```python
def run_conversation(self, num_turns: int = None):
    if num_turns is None:
        num_turns = self.config.session['max_turns']

    turn_order = self.config.session['turn_order']

    for turn in range(num_turns):
        for agent_name in turn_order:
            agent = self.agents[agent_name]
            context = self.conversation_history[-5:]
            response = agent.respond(context)

            message = {
                "turn": turn + 1,
                "agent": agent_name,
                "role": agent.config.role,
                "message": response
            }
            self.conversation_history.append(message)
```

## What Makes It So Beneficial?

One of the true advantages lies in the possibilities that configuration opens up. Here are concrete scenarios that now become trivial.

### Scenario 1: A/B Testing System Prompts

If you want to find out what results differently configured agents lead to, you can simply create two config files:

```yaml
# config_aggressive.yaml
- name: "planner"
  system_prompt: "Be aggressive and take calculated risks..."

# config_conservative.yaml
- name: "planner"
  system_prompt: "Be extremely cautious and risk-averse..."
```

Then just run both and compare results. No code change, just a config switch.

### Scenario 2: Tool Permission Experiments

What happens when the hacker has all tools versus specialized roles?

```yaml
# config_hacker_all_tools.yaml
- name: "hacker"
  tools: ["file_reader:use", "calculator:use", "database_query:use"]

# config_specialized.yaml
- name: "hacker"
  tools: ["file_reader:use"]
- name: "safecracker"
  tools: ["calculator:use"]
```

Does centralized tool concentration lead to better plans or worse coordination? And again: Just run and test.

### Scenario 3: Variable Team Sizes

My favorite example. Want to add more agents to the team? You can simply define more in the config without changing the actual code.

```yaml
# minimal_team.yaml - Only Planner + Hacker
agents:
  - name: "planner"
    # ...
  - name: "hacker"
    # ...

# full_team.yaml - All four Agents
agents:
  - name: "planner"
  - name: "hacker"
  - name: "safecracker"
  - name: "mole"
```

### Scenario 4: Saboteur Variations

Or specifically for our example: Which agent as saboteur is most likely to break the heist?

```yaml
# mole_saboteur.yaml
- name: "mole"
  is_saboteur: true

# hacker_saboteur.yaml
- name: "hacker"
  is_saboteur: true
```

Is the obvious insider (Mole) easier to detect than a technical expert (Hacker)?

All these experiments are now config changes, not code changes. This involves much less work and is also significantly less error-prone.

## Benefits in Professional Environments: Environment Separation

In professional setups, you need different configs for different environments. This now works elegantly:

```bash
agents_config_dev.yaml      # Small team, fast iteration
agents_config_staging.yaml  # Complete team, pre-prod tests
agents_config_prod.yaml     # Production setup with all features
```

And deployment becomes:

```python
# Development
system = DynamicAgentSystem("agents_config_dev.yaml")

# Production
system = DynamicAgentSystem("agents_config_prod.yaml")
```

No more code branches needed for different environments. One codebase with different configs. And all config changes are traceable in Git:

```bash
$ git diff agents_config.yaml
- system_prompt: "Be aggressive and take risks..."
+ system_prompt: "Be cautious and thorough..."
```

You immediately see what changed. Code reviews become easier because agent changes are separated from logic changes.

## Integration

The Dynamic Agent System isn't an isolated feature. Over the past days, we've implemented several features. Slightly modified, many things reappear:

**Day 8-9 (OAuth):** Scopes now come from the config. Each agent automatically gets its token based on `oauth_scopes`.

**Day 13 (Agent Tools):** Tools are loaded from the `tools` list. No more manual tool assignment.

**Day 14 (OAuth Tools):** Tool permissions are enforced through `oauth_scopes`. Security already in the config.

**Day 12 (Memory Service):** The memory service URL comes from the `memory_service` config. Different environments can use different services.

This is now the point where individual features become a coherent system. Not through more code, but through better architecture.

## Service Architecture

An important difference from previous days is that the Dynamic Agent System requires multiple simultaneously running services. Before, we mostly had individual services, now we're dealing with a microservice architecture.

```
Dynamic Agent System
├── OAuth Service (8001)    → Token management for all agents
├── Calculator (8002)       → Tool for Safecracker
├── File Reader (8003)      → Tool for Hacker
├── Database Query (8004)   → Tool for Mole
└── LLM Studio (1234)       → Gemma Model
```

Through the separation, each service has a clear responsibility (**Separation of Concerns**). They can be scaled arbitrarily and independently from each other. Each service can be updated individually, and problems can be isolated to individual services.

And because there are now several steps to start all required services, I also created a script that automates this.

## Helper Scripts

To simplify starting and stopping, there are now helper scripts:

```bash
# Start all services
./day_15/start_services.sh

# Run Agent System
python day_15/dynamic_agent_system.py

# Stop all services
./day_15/stop_services.sh
```

The `start_services.sh` script first cleans up old processes on the ports. Then it starts the four services in the background, shows PIDs and status, and redirects logs to the `/tmp` folder.

The `stop_services.sh` script finds all processes on ports 8001-8004 and terminates them with `kill -9`.

Unlike previous days where we only had to start one service process, we now need **at least 5 running processes** simultaneously (OAuth, the three tools, and LLM Studio). This is more realistic for professional environments but also more complex to manage.

The service URLs and ports are all defined in `agents_config.yaml`:

```yaml
oauth_service:
  base_url: "http://localhost:8001"

tool_services:
  calculator:
    host: "localhost"
    port: 8002
    endpoint: "/tools/calculator"
  # ... more tools
```

Different environments (Dev/Staging/Prod) can use different service URLs without code changes.

## Outlook

The Dynamic Agent System is the foundation for the coming days. Tomorrow we'll tackle **Service Integration**, where we bring together all services (OAuth, Tools, Memory, SQLite). Then the config becomes even more important because we'll centrally manage service URLs, credentials, and connection settings.

After that comes **Session Management** with cross-session state management. The session config in our YAML will then become the central control instrument.

And in the end, we'll have a system where you can orchestrate complex multi-agent scenarios through pure config changes. Without code changes, without deployments, without risk.

## Summary

Today we transformed our multi-agent system from hardcoded to configuration-driven. This sounds like a small step but is fundamental.

**What did we gain?**
- Unlimited agents without code changes
- A/B testing through config switching
- Environment separation (Dev/Staging/Prod)
- Git-based change tracking
- From 4 to N agents without refactoring

**What does it cost?**
- A bit more boilerplate during setup
- YAML syntax instead of Python (but that's a feature)
- A few additional abstraction layers
- **Multiple services simultaneously**: Instead of one service process, we now need 5 (OAuth, three tools, and LLM)
- Service management: starting, stopping, monitoring multiple processes

The cost-benefit ratio is still clear. The flexibility and realistic microservice architecture are worth the additional complexity. The helper scripts (`start_services.sh`, `stop_services.sh`) make management manageable.

**The most important insight:** A good config system turns a rigid prototype into a flexible platform. Not through more features, but through better architecture.

Tomorrow we'll build on this and integrate all services. But the foundation is now in place.

## Usage

> **Quick Start**
> ```bash
> # 1. Start services (OAuth + 3 Tools)
> ./day_15/start_services.sh
>
> # 2. Start LM Studio with Gemma (Port 1234)
> # Manually in LM Studio GUI
>
> # 3. Run Agent System
> python day_15/dynamic_agent_system.py
>
> # 4. Stop services
> ./day_15/stop_services.sh
> ```
> **Important:** Day 15 requires **5 running services** simultaneously (OAuth, Calculator, File Reader, Database, LLM)
