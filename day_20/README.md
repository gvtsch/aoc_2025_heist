
# Day 20: Interactive Heist Command Center

**Interaktives Dashboard für Echtzeit-Steuerung und Überwachung von Heist-Sessions.**

**Standalone:** Keine Abhängigkeit zu Day 18/19, alle Komponenten lokal:
- `config.yaml` – Server-Konfiguration
- `session_analytics.py` – Analytics-Backend
- `heist_controller.py` – Session- und Command-Management
- `interactive_dashboard_server.py` – FastAPI-Server
- `interactive_dashboard.html` – Web-UI
- `integrated_agent_with_controller.py` – Controller-fähige Agenten
- `run_controlled_heist.py` – Demo-Skript
- `agents_config.yaml` – Agenten-Konfiguration

---

## 🚀 Schritt-für-Schritt: Manueller Lauf

1. **Dashboard-Server starten**
  ```bash
  ./day_20/start_interactive_dashboard.sh
  # oder
  python3 day_20/interactive_dashboard_server.py
  ```
  → Server läuft auf Port 8008

2. **Dashboard im Browser öffnen**
  http://localhost:8008

3. **Neue Heist-Session starten**
  - Per API-Aufruf (z.B. mit curl/Postman):
    ```bash
    curl -X POST http://localhost:8008/api/heist/start \
     -H "Content-Type: application/json" \
     -d '{
      "session_id": "heist_001",
      "agents": ["planner", "hacker", "safecracker", "mole"],
      "config": {"difficulty": "hard"}
     }'
    ```
  - Im Dashboard erscheinen die Daten nach kurzer Zeit automatisch.

4. **Session steuern & beobachten**
  - Pause/Resume, Kommandos an Agenten, Bank-Layout, Activity Log, Mole Detection etc. direkt im Dashboard nutzen.

5. **Agenten/Simulation starten** (optional)
  - Für echte Agenten-Logik: Separat eigene Agenten-Prozesse starten (z.B. mit `run_controlled_heist.py` oder eigenen Skripten).

---

## 🧪 Demo-Lauf (vollautomatisch)

```bash
python3 day_20/run_controlled_heist.py --demo
```
Zeigt: Pause/Resume, Kommandos, State-Sync mit echten Agenten.

---


## Features

- ⏸️ Heist Pause/Resume & Status
- 📡 Kommandos an Agenten senden
- 🏦 Interaktives Bank-Layout
- 🕵️ Mole Detection Game
- 📋 Echtzeit-Activity-Log
- 📊 Analytics & Tool-Statistiken


## Server-Start & Stop

Start (Standard-Konfiguration):
```bash
./day_20/start_interactive_dashboard.sh
```
Stoppen:
```bash
./day_20/stop_interactive_dashboard.sh
```
Individuelle Konfiguration:
```bash
python3 day_20/interactive_dashboard_server.py --config my_config.yaml
```

## Configuration

All settings are in [config.yaml](config.yaml):

### Database Path

```yaml
database:
  path: "heist_analytics.db"  # Same database as Day 19
```

### Server Settings

```yaml
server:
  host: "0.0.0.0"
  port: 8008  # Different from Day 19 (8007)
  title: "Interactive Heist Command Center"
  reload: false
```

### Interactive Features

```yaml
features:
  heist_control: true      # Enable pause/resume controls
  agent_commands: true     # Enable command injection
  bank_layout: true        # Enable interactive bank layout
  mole_detection: true     # Enable mole detection game
  activity_log: true       # Enable activity logging
```

## API Endpoints

### Analytics Endpoints (from Day 19)

```
GET  /api/sessions              - List all sessions
GET  /api/session/{id}          - Session details
GET  /api/tool-stats            - Tool statistics
GET  /api/agent-activity/{id}   - Agent activity
GET  /api/stats/summary         - Summary statistics
```

### Control Endpoints (NEW in Day 20)

```
POST /api/heist/start           - Start new heist session
POST /api/heist/{id}/pause      - Pause running heist
POST /api/heist/{id}/resume     - Resume paused heist
POST /api/heist/{id}/command    - Send command to agent
GET  /api/heist/{id}/commands   - Get pending commands
GET  /api/heist/{id}/status     - Get session status
GET  /api/heist/active          - List active sessions
```

### Mole Detection Endpoints

```
POST /api/heist/{id}/detect-mole  - Mark agent as suspected mole
GET  /api/heist/{id}/mole-status  - Get mole detection status
```

### WebSocket

```
WS /ws                          - Real-time bidirectional updates
```

## Architecture

### Backend Components

**HeistController** (`heist_controller.py`):
- Manages active heist sessions
- Handles pause/resume states
- Queues agent commands
- Tracks session status

**SessionAnalytics** (`session_analytics.py`):
- Local copy from Day 19
- Reads from `heist_analytics.db`
- Provides session statistics

**Interactive Dashboard Server** (`interactive_dashboard_server.py`):
- FastAPI server with CORS
- Control endpoints
- WebSocket broadcasting
- Config-driven setup

### Frontend Components

**Interactive Dashboard** (`interactive_dashboard.html`):
- Heist Control Panel
- Agent Command Center
- Bank Layout Visualization
- Activity Log
- Mole Detection UI
- Real-time WebSocket updates


## API-Beispiele

Session starten:
```bash
curl -X POST http://localhost:8008/api/heist/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "heist_001", "agents": ["planner", "hacker", "safecracker", "mole"], "config": {"difficulty": "hard"}}'
```
Session pausieren:
```bash
curl -X POST http://localhost:8008/api/heist/heist_001/pause
```
Kommando an Agenten:
```bash
curl -X POST http://localhost:8008/api/heist/heist_001/command \
  -H "Content-Type: application/json" \
  -d '{"agent": "hacker", "command": "Disable security camera 3 immediately"}'
```
Aktive Sessions abfragen:
```bash
curl http://localhost:8008/api/heist/active
```

## Standalone Structure

Day 20 is completely self-contained:

```
day_20/
├── config.yaml                      # Server configuration
├── session_analytics.py             # Local copy from Day 19
├── heist_controller.py              # Session control logic
├── interactive_dashboard_server.py  # FastAPI backend
├── interactive_dashboard.html       # Interactive UI
├── start_interactive_dashboard.sh   # Start script
├── stop_interactive_dashboard.sh    # Stop script
└── README.md                        # This file
```

**No external dependencies** on Day 18 or Day 19 - everything needed is local.

## Differences from Day 19

| Feature | Day 19 | Day 20 |
|---------|--------|--------|
| **Mode** | Read-only visualization | Interactive control |
| **Port** | 8007 | 8008 |
| **Control** | No controls | Pause/Resume/Command |
| **Dependencies** | Uses day_18 imports | Fully standalone |
| **WebSocket** | One-way (server→client) | Bidirectional |
| **Bank Layout** | No | Interactive visualization |
| **Commands** | No | Agent command injection |
| **Config** | config.yaml | config.yaml (extended) |

## Agent Integration

### IntegratedAgentWithController

Day 20 includes a **fully implemented** agent class that integrates with the HeistController:

```python
from integrated_agent_with_controller import IntegratedAgentWithController
from heist_controller import get_controller

# Start session in controller
controller = get_controller()
controller.start_session(
    session_id="heist_001",
    agents=["planner", "hacker", "safecracker"],
    config={}
)

# Create controller-aware agent
agent = IntegratedAgentWithController(
    config=agent_config,
    llm_client=llm_client,
    # ... other params
    session_id="heist_001"
)

# Agent automatically checks pause/commands
response = agent.respond(context, turn_id=1)
```

### Run the Demo

See the full integration in action:

```bash
# Run controlled heist demo
python3 day_20/run_controlled_heist.py --demo
```

This demo shows:
- ⏸️ Pause/Resume functionality
- 📡 Command injection to agents
- 🔄 Real-time controller integration

The demo automatically:
1. Creates 4 controller-aware agents
2. Runs 5 turns of heist planning
3. Pauses on turn 3
4. Sends a command to the hacker
5. Resumes execution


## Troubleshooting

- **Port 8008 belegt:**
  ```bash
  lsof -ti:8008 | xargs kill -9
  ```
- **Datenbank fehlt:**
  ```bash
  cp day_19/heist_analytics.db day_20/
  ```
- **WebSocket-Probleme:**
  - Server läuft?
  - Port 8008 offen?
  - Browser aktuell?
- **Kommandos werden nicht ausgeführt:**
  - Agenten müssen separat laufen und Kommandos abholen.


## Ausblick

- **Tag 21:** Mole Game (Sabotage, User-Guessing, Game-Logik)
- **Tag 22:** AI Detection (Pattern Recognition, ML, Anomaly Detection)


## API-Dokumentation & Health

- Swagger/OpenAPI: http://localhost:8008/docs
- Health-Check: `curl http://localhost:8008/health`
