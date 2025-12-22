---
title: "Day 20: Interactive Dashboard"
date: 2025-12-20
tags:
  - python
  - aoc
  - adventofcode
  - aiagents
  - interactive
  - dashboard
toc: true
---

All documents for this post can be found in my [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_20).

Yesterday we visualized the project. Today we're turning the dashboard into a real command center – with bidirectional communication, live control, and command injection.

## The Problem

The dashboard from Day 19 is read-only. We can see what's happening, but we can't intervene.

An agent makes a questionable decision? We just watch. Want to pause the heist? Can't do it. Send a new instruction to an agent? Not possible.

For a real command center, we need controls – pause, send commands, intervene live.

## The Solution

Bidirectional communication. The server accepts not only GET requests (fetching data) but also POST commands (control). The frontend sends actions, the server executes them, the agents react, the server notifies all clients via WebSocket.

In professional multi-agent systems, this is standard: trading bots pause during market anomalies, customer service agents receive real-time instructions for unexpected scenarios, production workflows can be interrupted when errors occur.

For implementation, we need three new components.

### New Components

* **HeistController**: Backend class that manages running sessions. Enables pause/resume, command injection, status tracking.
* **Interactive Dashboard Server**: Extends the Day 19 server with control endpoints: POST endpoints for pause, resume, commands.
* **Interactive Frontend**: Extends Day 19's UI with control panels and command forms.

```
User Actions (Frontend)
        ↓
Control Endpoints (FastAPI)
        ↓
HeistController (State Management)
        ↓
Agent System (Execution)
        ↓
WebSocket Updates → Dashboard
```

This is bidirectional communication. User -> Server -> Agents and Agents -> Server -> User.

## HeistController

The HeistController is the central class for session management. It uses `HeistStatus` to represent a session's state (e.g., `HeistStatus.RUNNING.value` -> `"running"`).

```python
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

class HeistStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class HeistController:
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.command_queue: Dict[str, List[Dict]] = {}
        self.pause_flags: Dict[str, bool] = {}
```

The controller has three data structures:

* **active_sessions**: Dict of all running sessions with status (as string value from HeistStatus), agents, config.
* **command_queue**: Queue of commands sent to agents but not yet executed.
* **pause_flags**: Flags indicating whether a session is paused.

The controller's most important methods are **Start Session**, **Pause and Resume**, and **Command Injection**.

### Start Session

A new session is initialized with status RUNNING, an agent list, and a configuration. The command queue and pause flag are set to empty/false.

```python
def start_session(self, session_id: str, agents: List[str], config: Dict) -> Dict:
    self.active_sessions[session_id] = {
        "session_id": session_id,
        "status": HeistStatus.RUNNING.value,
        "agents": agents,
        "config": config,
        "start_time": datetime.now().isoformat(),
        "current_turn": 0,
        "mole": None,  # Will be randomly chosen in Day 21
        "detected_mole": None
    }
    self.command_queue[session_id] = []
    self.pause_flags[session_id] = False

    return {
        "success": True,
        "session_id": session_id,
        "message": f"Heist session {session_id} started",
        "agents": agents
    }
```

### Pause and Resume

Pause sets the status to PAUSED and the flag to true. Resume sets it back to RUNNING and false. The agent system regularly checks `is_paused()` and blocks when true.

```python
def pause_session(self, session_id: str) -> Dict:
    if self.active_sessions[session_id]["status"] != HeistStatus.RUNNING.value:
        return {"success": False, "error": "Session is not running"}

    self.active_sessions[session_id]["status"] = HeistStatus.PAUSED.value
    self.pause_flags[session_id] = True

    return {
        "success": True,
        "session_id": session_id,
        "message": "Heist paused",
        "status": HeistStatus.PAUSED.value
    }

def resume_session(self, session_id: str) -> Dict:
    if self.active_sessions[session_id]["status"] != HeistStatus.PAUSED.value:
        return {"success": False, "error": "Session is not paused"}

    self.active_sessions[session_id]["status"] = HeistStatus.RUNNING.value
    self.pause_flags[session_id] = False

    return {
        "success": True,
        "session_id": session_id,
        "message": "Heist resumed",
        "status": HeistStatus.RUNNING.value
    }
```

This enables active intervention through, for example, **Command Injection**.

### Command Injection

Commands are placed in the queue. Agents check before each turn if commands are pending for them. If yes, they're injected into the LLM context as "Override Instruction from Command Center".

```python
def send_command(self, session_id: str, agent: str, command: str) -> Dict:
    command_obj = {
        "agent": agent,
        "command": command,
        "timestamp": datetime.now().isoformat(),
        "executed": False
    }

    if session_id not in self.command_queue:
        self.command_queue[session_id] = []

    self.command_queue[session_id].append(command_obj)

    return {
        "success": True,
        "session_id": session_id,
        "message": f"Command sent to {agent}",
        "command": command
    }

def get_pending_commands(self, session_id: str, agent: Optional[str] = None) -> List[Dict]:
    if session_id not in self.command_queue:
        return []

    commands = self.command_queue[session_id]

    if agent:
        commands = [c for c in commands if c["agent"] == agent and not c["executed"]]

    return commands
```

This enables the mentioned corrections during a running heist. If the hacker forgets to disable cameras, a command can be sent: "Disable camera 3 immediately".

Let's now look more closely at how this command injection works in practice.

## Command Injection During Execution

An interactive dashboard allows us to intervene directly in ongoing sessions. How does this work?

### 1. Command Injection

Via the dashboard or API, we can send commands to individual agents. These commands are inserted into the running session's command queue and wait there for execution. The `HeistController` checks each turn if new commands are in the queue and forwards them to the corresponding agents.

### 2. Real-time Feedback

As soon as a command is executed, the system notifies the dashboard via WebSockets. All changes like status updates or log entries are immediately displayed in the dashboard without delay. All connected clients see the same updates in real-time.

### 3. Example: Sending a Command

A command can be sent via the API as follows:

```bash
curl -X POST http://localhost:8008/api/heist/<session_id>/command \
-H "Content-Type: application/json" \
-d '{"agent": "hacker", "command": "Disable camera"}'
```

### 4. Effects

The difference between normal execution and command-controlled execution is clearly visible: Without a command, an agent executes its intended default action, for example "Hack door A". With a sent command, however, the agent prioritizes the new instruction and instead executes, for example, "Hack door B".

### 5. Testing

To experience the functionality yourself, use the demo script `demo_live_control_verbose.py`. Start a session with `run_controlled_heist.py` in one terminal and send commands via the demo script in a second terminal. You can then watch live as the agents react to the new instructions and adjust their behavior accordingly. A detailed guide can be found below in the "Live Control Demo" section.

Of course, command injection also works directly through the dashboard in the browser. But for that, we first need the corresponding server with its endpoints.

## Interactive Dashboard Server

The server extends yesterday's endpoints with control functions. It still uses SessionAnalytics for read operations and the HeistController for write operations.

**Note:** Day 20 contains a local copy of `session_analytics.py` to create a fully standalone deployment unit. This allows `day_20` to be used as an independent package without dependencies on `day_18`. In a production environment, this would be done via separate microservices.

```python
from fastapi import FastAPI, WebSocket
from day_20.session_analytics import SessionAnalytics  # Local copy for standalone deployment
from day_20.heist_controller import HeistController, get_controller

app = FastAPI(title="Interactive Heist Command Center")
analytics = SessionAnalytics()
controller = get_controller()
```

### Control Endpoints

The server provides three central POST endpoints to actively control sessions: Start, Pause/Resume, and Command Injection.

**Start Heist:**
```python
@app.post("/api/heist/start")
async def start_heist(request: SessionStartRequest):
    result = controller.start_session(
        session_id=request.session_id,
        agents=request.agents,
        config=request.config
    )

    await manager.broadcast({
        "type": "heist_started",
        "session_id": request.session_id,
        "agents": request.agents,
        "timestamp": datetime.now().isoformat()
    })

    return result
```

**Pause/Resume:**
```python
@app.post("/api/heist/{session_id}/pause")
async def pause_heist(session_id: str):
    result = controller.pause_session(session_id)

    if result["success"]:
        await manager.broadcast({
            "type": "heist_paused",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

    return result

@app.post("/api/heist/{session_id}/resume")
async def resume_heist(session_id: str):
    result = controller.resume_session(session_id)

    if result["success"]:
        await manager.broadcast({
            "type": "heist_resumed",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

    return result
```

**Send Command:**
```python
@app.post("/api/heist/{session_id}/command")
async def send_agent_command(session_id: str, request: CommandRequest):
    result = controller.send_command(
        session_id=session_id,
        agent=request.agent,
        command=request.command
    )

    if result["success"]:
        await manager.broadcast({
            "type": "command_sent",
            "session_id": session_id,
            "agent": request.agent,
            "command": request.command,
            "timestamp": datetime.now().isoformat()
        })

    return result
```

All control actions broadcast events via WebSocket. All connected clients see in real-time what's happening.

### Status Endpoints

Besides control endpoints, there are also GET endpoints to query the current state of sessions. These allow the frontend to continuously fetch status updates.

**Get Session Status:**
```python
@app.get("/api/heist/{session_id}/status")
async def get_heist_status(session_id: str):
    status = controller.get_session_status(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status
```

**Get Active Heists:**
```python
@app.get("/api/heist/active")
async def get_active_heists():
    active = controller.get_all_active_sessions()
    return {
        "active_sessions": active,
        "count": len(active)
    }
```

**Get Pending Commands:**
```python
@app.get("/api/heist/{session_id}/commands")
async def get_pending_commands(session_id: str, agent: Optional[str] = None):
    commands = controller.get_pending_commands(session_id, agent)
    return {
        "session_id": session_id,
        "agent": agent,
        "commands": commands,
        "count": len(commands)
    }
```

These endpoints allow the frontend to continuously fetch status updates.

## Interactive Frontend

The frontend extends the dashboard with control panels. And yes, it's also vibecoded 😉 But I'm learning from it!

### Heist Control Panel

The Heist Control Panel is the control center. But to seriously talk about a control center in a project of this size is almost ironic 😄 It offers three central functions: Pause, Resume, and Status Refresh. The Pause button immediately stops all running agents, the Resume button continues execution, and the Refresh button updates the displayed session status. The panel also always shows which session is currently active.

```html
<div class="card">
    <h2>🎛️ Heist Control</h2>
    <div class="control-panel">
        <button id="pauseBtn" onclick="pauseHeist()" class="pause">⏸️ Pause Heist</button>
        <button id="resumeBtn" onclick="resumeHeist()" class="secondary">▶️ Resume Heist</button>
        <button onclick="refreshStatus()" class="secondary">🔄 Refresh Status</button>
    </div>
    <div>
        <strong>Current Session:</strong> <span id="currentSession">No active session</span>
    </div>
</div>
```

The JavaScript implementation sends POST requests to the corresponding endpoints and updates the UI based on the server response.

```javascript
async function pauseHeist() {
    const response = await fetch(`/api/heist/${currentSessionId}/pause`, {
        method: 'POST'
    });
    const data = await response.json();

    if (data.success) {
        addLog('Heist paused successfully', 'success');
        document.getElementById('pauseBtn').style.display = 'none';
        document.getElementById('resumeBtn').style.display = 'inline-block';
        updateStatusBadges('paused');
    }
}
```

The flow is simple. As soon as the user clicks the Pause button, the frontend sends a POST request to the server. The HeistController receives this request, sets the session status to PAUSED, and activates the corresponding pause flag. The server then broadcasts the event via WebSocket to all connected clients. The dashboard receives the message, updates the buttons (Pause is hidden, Resume becomes visible) and displays the new status badge. Through WebSocket communication, all connected clients see the status change immediately and in real-time.

### Agent Command Center

The Agent Command Center allows direct communication with individual agents during execution. A target agent is selected via a dropdown menu, the command is entered in a text field, and with a click, the command is sent to the server for execution. The command is queued and injected as an override instruction into the agent's LLM context at the next turn.

```html
<div class="card">
    <h2>📡 Send Agent Command</h2>
    <div class="command-form">
        <select id="agentSelect">
            <option value="planner">🎯 Planner</option>
            <option value="hacker">💻 Hacker</option>
            <option value="safecracker">🔓 Safecracker</option>
            <option value="mole">🕵️ Mole</option>
        </select>
        <input type="text" id="commandInput" placeholder="Enter command...">
        <button onclick="sendCommand()">📤 Send</button>
    </div>
</div>
```

The JavaScript function collects the inputs, creates a JSON object, and sends it via POST request to the server:

```javascript
async function sendCommand() {
    const agent = document.getElementById('agentSelect').value;
    const command = document.getElementById('commandInput').value;

    const response = await fetch(`/api/heist/${currentSessionId}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent, command })
    });
    const data = await response.json();

    if (data.success) {
        addLog(`✅ Command sent to ${agent}: ${command}`, 'success');
        commandCount++;
    }
}
```

The flow: User selects an agent, types a command, and clicks Send. The POST request is sent, the command lands in the queue, and the agent retrieves it at the next turn. Confirmation is immediately displayed in the Activity Log.

### Activity Log

The Activity Log is the central chronicle of all dashboard events. Every user action, every status change, and every system notification is logged here with a timestamp. The log shows the newest entries at the top and automatically keeps only the last 50 entries to ensure performance. Different event types are color-coded: successes in green, warnings in orange, and errors in red.

The HTML element is intentionally minimalistic and serves as a container for dynamically created log entries:

```html
<div class="card">
    <h2>📋 Activity Log</h2>
    <div id="activityLog">
        <div class="log-entry log-info">System initialized...</div>
    </div>
</div>
```

The JavaScript function `addLog()` handles creation and management of log entries. It inserts each new entry at the beginning of the log, adds a timestamp, and assigns a CSS class based on the event type.

```javascript
function addLog(message, type = 'info') {
    const log = document.getElementById('activityLog');
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    log.insertBefore(entry, log.firstChild);

    // Keep only last 50 entries
    while (log.children.length > 50) {
        log.removeChild(log.lastChild);
    }
}
```

Every user interaction is immediately logged. Commands sent to agents, pause and resume actions, session status changes, and all WebSocket events. The log is used by all other UI components and provides a complete timeline of all dashboard activities. Through chronological order with timestamps, the course of a heist can be traced completely.

### WebSocket Integration

WebSocket integration is the nervous system (again very grandiose for our small project 😉) of the dashboard and enables bidirectional real-time communication between server and all connected clients. While REST endpoints are responsible for explicit user actions, WebSocket ensures that all clients are automatically informed about every change in the system. Without WebSocket, the dashboard would have to continuously poll, which would be inefficient and lead to delays.

The central message handler function processes incoming server broadcasts and updates the UI accordingly. Each event type triggers specific UI updates.

```javascript
function handleWebSocketMessage(data) {
    if (data.type === 'heist_started') {
        addLog(`Heist ${data.session_id} started`, 'success');
        currentSessionId = data.session_id;
        updateStatus();
    } else if (data.type === 'heist_paused') {
        addLog('Heist paused', 'warning');
        updateStatus();
    } else if (data.type === 'heist_resumed') {
        addLog('Heist resumed', 'success');
        updateStatus();
    } else if (data.type === 'command_sent') {
        addLog(`Command sent to ${data.agent}: ${data.command}`, 'info');
    } else if (data.type === 'mole_detected') {
        addLog(`Agent ${data.agent} marked as suspect`, 'warning');
    }
}
```

The different event types have different functions. `heist_started` initializes a new session and sets the current session ID in the dashboard. `heist_paused` and `heist_resumed` trigger status updates and change the visibility of control buttons. `command_sent` displays the command confirmation in the Activity Log. `mole_detected` is used for the Mole Detection Game in Day 21.

All WebSocket events follow the same flow. The server broadcasts an event to all connected clients, the client receives the event via the WebSocket connection, the handler function evaluates the event type, the corresponding UI components are updated, and the Activity Log receives a new entry. This way, all users who have the dashboard open see exactly the same updates at the same time. When a user pauses a session, all other users immediately see the "Heist paused" badge and the corresponding log entries.

## Integration with Agent System

Integrating the HeistController with the agent system is the crucial step that turns passive infrastructure into an interactive system. Without this integration, pause flags and commands would be stored in the controller, but the agents wouldn't know about them and would simply continue running. The `IntegratedAgentWithController` class bridges this gap by extending the agents from Day 16 with "controller awareness".

The class overrides the `respond()` method and inserts three critical checks before the actual LLM response.

```python
from day_16.integrated_system import IntegratedAgent
from heist_controller import get_controller

class IntegratedAgentWithController(IntegratedAgent):
    """Extends IntegratedAgent with HeistController integration."""

    def respond(self, context: List[Dict[str, str]], turn_id: int) -> str:
        """Generate response with HeistController integration."""
        controller = get_controller()

        # 1. CHECK PAUSE STATUS
        if controller.is_paused(self.session_id):
            pause_msg = f"[PAUSED] {self.config.name} is waiting for resume..."
            print(f"⏸️  {pause_msg}")
            return pause_msg

        # 2. CHECK FOR PENDING COMMANDS
        pending = controller.get_pending_commands(
            self.session_id,
            self.config.name
        )

        if pending and len(pending) > 0:
            command = pending[0]
            print(f"📡 [{self.config.name}] Received command: {command['command']}")

            # Inject command as high-priority system message
            context = context.copy()
            context.append({
                "agent": "COMMAND_CENTER",
                "message": f"⚠️ OVERRIDE INSTRUCTION: {command['command']}"
            })

            # Mark as executed - find index in full queue
            all_commands = controller.command_queue[self.session_id]
            for idx, cmd in enumerate(all_commands):
                if cmd is command:
                    controller.mark_command_executed(self.session_id, idx)
                    break

        # 3. UPDATE TURN IN CONTROLLER
        controller.update_turn(self.session_id, turn_id)

        # 4. GENERATE NORMAL RESPONSE (using parent class)
        return super().respond(context, turn_id)
```

The four steps in detail:
* **Step 1** checks if the session is paused. If yes, a pause message is immediately returned without consulting the LLM. The agent effectively blocks until Resume is called.
* **Step 2** retrieves all pending commands for this specific agent. If commands are present, the first command is inserted into the context as a highest-priority system message. The `OVERRIDE INSTRUCTION` prefix signals to the LLM that this command takes precedence over all other instructions.
* **Step 3** updates the turn counter in the controller so the dashboard can always display current progress.
* **Step 4** calls the normal `respond()` method of the parent class, which sends the modified context (with injected command) to the LLM.

The result is an agent that seamlessly integrates into the interactive dashboard.

### Using the Controller Integration

Using controller-integrated agents differs little from the standard agents from Day 16. The only difference is that each agent is assigned a `session_id` that connects it to the HeistController.

```python
from integrated_agent_with_controller import IntegratedAgentWithController
from heist_controller import get_controller

# Initialize controller and start session
controller = get_controller()
controller.start_session(
    session_id="heist_001",
    agents=["planner", "hacker", "safecracker"],
    config={}
)

# Create controller-aware agents
agent = IntegratedAgentWithController(
    config=agent_config,
    llm_client=llm_client,
    # ... other params
    session_id="heist_001"
)

# Response now checks pause/commands automatically
response = agent.respond(context, turn_id=1)
```

The important difference lies in runtime behavior. While a normal agent always executes its turn, the controller-integrated agent first checks pause status and command queue. These checks are transparent to the calling code but happen automatically in the background with every `respond()` call.

The demo script `run_controlled_heist.py` shows the complete integration in action. It starts a session with four controller-aware agents and enables live control via the API.

```bash
python3 day_20/run_controlled_heist.py --demo
```

The flow for each agent turn is the same. Before each response call, the agent first checks the pause flag. If the session is paused, it immediately returns a pause message and skips LLM generation completely. If not paused, it checks the command queue for pending commands. If commands are present, it injects them as override instructions into the context and marks them as executed. Only after these checks is the LLM called, which then processes the (possibly modified) context. The agent responds according to the injected commands or executes its standard logic if no commands were present.

This architecture enables interventions during execution. Commands can be sent at any time during execution and immediately affect the target agent's next turn. Pause actions stop the entire session immediately, without code changes or restarts being necessary.

## Usage

I'd like to briefly address usage without explaining everything in detail again.

### Starting the Server

```bash
./day_20/start_interactive_dashboard.sh
```

The server starts on port 8008:

```
🎮 Interactive Heist Command Center
Starting server on http://localhost:8008
Dashboard: http://localhost:8008
API Docs: http://localhost:8008/docs

🎯 New Features:
  • Heist Pause/Resume Control
  • Send Commands to Agents
  • Real-time Status Updates
  • Mole Detection Game
```

### Opening the Dashboard

Navigate to `http://localhost:8008`. The dashboard shows all control features. API documentation can be found at `http://localhost:8008/docs`.

### Pausing the Heist

1. Click "⏸️ Pause Heist"
2. UI shows "Heist Paused" badge (orange)
3. Resume button appears

To continue: Click "▶️ Resume Heist"

### Sending Commands

1. Select agent from dropdown
2. Type command (e.g., "Disable security camera 3")
3. Click "📤 Send"
4. Activity Log shows confirmation
5. Agent receives command at next turn as `OVERRIDE INSTRUCTION`

**Tip:** Formulate commands clearly and concretely. "Scan room for guards" is better than "Do something". No-brainer 😄

## Testing

There are multiple levels of testing:

**API Tests** (`test_interactive_dashboard.py`): Tests all server endpoints without real agents - Health Check, Session Management, Command Injection, Pause/Resume, and Mole Detection. 11 tests in a few seconds.

**Live Control Demo** (`demo_live_control_verbose.py`): Shows interaction with real LLM-controlled agents. Commands are injected as `OVERRIDE INSTRUCTION` into the LLM context and influence behavior in real-time.

**Mole Game Integration** (`test_mole_game_integration.py`): End-to-end test of the Mole Detection Game with random mole selection and evaluation.

For a detailed step-by-step guide, see [Testing Guide](day_20_testing_guide.md).

## Summary

Day 20 transforms the passive dashboard from Day 19 into an interactive "Command Center". The new architecture is based on bidirectional communication between user, server, and agents and enables active interventions during runtime.

The HeistController manages all running sessions and tracks their status (RUNNING, PAUSED, COMPLETED, FAILED). It manages command queues for individual agents and enables pause and resume functions. The Interactive Dashboard Server extends the API with POST endpoints for control operations, such as pausing heists, resuming, and sending commands. All actions are broadcast to all clients via WebSockets.

The frontend now offers three control panels. Heist Control (Pause/Resume), Agent Command Center (send commands during execution), and Activity Log (chronological logging of all actions). The IntegratedAgentWithController class automatically checks pause status and command queue before each response. Commands are injected as override instructions into the LLM context.

Another step forward. A few steps still to go.

## Quick-Start

Quick start for the impatient:

```bash
# 1. Start server
./day_20/start_interactive_dashboard.sh
# Or directly: python3 day_20/interactive_dashboard_server.py

# 2. Open dashboard
open http://localhost:8008

# 3. Start controlled heist demo (in separate terminal)
python3 day_20/run_controlled_heist.py --demo
```

Now you can in the dashboard:
- Watch the heist live
- Pause/resume session
- Send commands to agents
- Play the mole detection

For detailed instructions see [QUICKSTART.md](QUICKSTART.md) and [Testing Guide](day_20_testing_guide.md).
