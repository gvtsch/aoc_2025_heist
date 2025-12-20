---
title: "Day 19: Dashboard Visualization"
date: 2025-12-19
tags:
  - python
  - aoc
  - adventofcode
  - aiagents
  - dashboard
  - visualization
toc: true
---

Alle Dokumente zu diesem Beitrag sind in meinem [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_19) zu finden.

Tag 19 macht unsere Daten sichtbar. Seit Tag 16 loggen wir Sessions in SQLite. Seit gestern analysieren wir sie mit einer REST API. Aber bisher haben wir nur JSON-Responses gesehen. Das ändert sich heute. Wir bauen ein standalone Dashboard das Sessions visualisiert, Agent-Activity zeigt, Tool-Usage darstellt und Real-time Updates über WebSocket empfängt.

Was ist denn nun **Websocket**?
> Websocket ist ein bidirektionales Kommunikationsprotokoll über eine persistente TCP-Verbindung. Anders als HTTP (Request-Response) ermöglicht es Echtzeit-Datenaustausch in beide Richtungen. Der Server kann jederzeit Daten an den Client pushen, ohne dass der Client anfragen muss. Perfekt für Live-Updates, Chat oder Dashboards.

![alt text](Dashboard.png)

## Das Problem

Die Analytics API liefert Daten. Aber JSON ist nicht besonders intuitiv. Wer will schon Arrays von Message-Objekten durchscrollen um zu verstehen welcher Agent am aktivsten war? Wer will Tool-Statistiken als Zahlenkolonnen lesen? Manchmal macht das sicher auch Spaß, aber ... 🤷‍♂️

Wir "brauchen" eine Visualisierung. Charts die Patterns zeigen. Timelines die Aktivitäten darstellen und Dashboards die auf einen Blick Insights liefern.

## Die Lösung

Wir bauen ein Dashboard-System, das auf dem Analytics-Format von Tag 18 aufbaut. Das Backend nutzt FastAPI und liefert sowohl HTML-Seiten als auch WebSocket-Verbindungen für Echtzeit-Updates aus. Die Visualisierungen werden mit Chart.js gerendert. Das Frontend ruft die Daten von den Analytics-Endpoints ab und präsentiert sie in einer interaktiven Benutzeroberfläche.

Das Dashboard selbst liegt komplett im `day_19/` Verzeichnis. Allerdings benötigt der Heist-Runner die Agent-Infrastruktur von Tag 17 sowie die Services von Tag 16 (OAuth, Memory Service, Tool Discovery). Das Dashboard kann auch ohne laufende Heist-Sessions genutzt werden - es visualisiert dann bereits gespeicherte Daten aus der Analytics-Datenbank.

Das Dashboard ist übrigens vollständig vibecoded. Mit HTML hatte ich bisher null Berührungspunkte 😄

### Architektur und Abhängigkeiten

Tag 19 besteht aus vier Hauptkomponenten:

* **Analytics Orchestrator**: Der Orchestrator (`orchestrator_analytics.py`) nutzt das Datenbank-Schema aus Tag 18 mit aggregierter `tool_usage` Tabelle. Er importiert Agent-Klassen aus Tag 17 (`DiscoveryIntegratedAgent`, `ConfigLoader`, etc.) und benötigt die laufenden Services von Tag 16/17 (OAuth, Memory, Tool Discovery).
* **Session Analytics**: Lokale Kopie von `session_analytics.py` mit angepassten Defaults für `heist_analytics.db`.
* **Dashboard Server**: FastAPI-Server auf Port 8007 mit YAML-Konfiguration (`config.yaml`). Dieser ist unabhängig von den anderen Services und liest nur aus der Datenbank.
* **Frontend**: Single-Page Application mit Cyberpunk 2077-inspiriertem Design. 100% Videcoded.

Das Dashboard selbst ist Read-Only und benötigt keine laufenden Services. Es liest nur aus der Datenbank. Der Heist-Runner hingegen benötigt die Tag 16/17 Infrastruktur, um neue Sessions zu generieren.

Noch eine Anmerkung zum Dashboard. Es gibt einen Threat-Detection Abschnitt. Der ist aktuell nur in der UI vorhande, funktional aber noch nicht umgesetzt.

## Database Schema

Tag 19 nutzt das **Tag 18 Analytics-Format** mit aggregierter Tool-Usage:

```sql
-- Aggregierte Tool-Usage (kein turn_id)
CREATE TABLE tool_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    operation TEXT DEFAULT 'execute',
    usage_count INTEGER DEFAULT 0,
    success_rate REAL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**Unterschied zu Tag 16/17:**
- Tag 16/17: Nutzt `DatabaseManager` mit individual tool_usage entries (mit `turn_id`)
- Tag 18/19: Nutzt neuen `AnalyticsDatabaseManager` mit aggregierten Statistics (ohne `turn_id`)

### AnalyticsDatabaseManager (Neu in Tag 19)

Tag 19 führt einen komplett neuen Database Manager ein, der speziell für das Analytics-Schema von Tag 18 entwickelt wurde. Im Gegensatz zum `DatabaseManager` aus Tag 16 aggregiert dieser Manager Tool-Usage-Daten:

```python
class AnalyticsDatabaseManager:
    """
    Neuer Database Manager für Tag 18/19 Analytics-Schema.
    Unterscheidet sich vom Tag 16 DatabaseManager durch:
    - Aggregierte tool_usage Tabelle (kein turn_id)
    - Separate tool_calls Tabelle für individuelle Aufrufe
    - Zusätzliche agents und actions Tabellen
    """

    def store_tool_usage(self, session_id: str, turn_id: int, agent_name: str,
                        tool_name: str, params: str, result: str, success: bool):
        """Compatibility method for Day 16/17 agents."""
        # Delegate to store_tool_call, ignoring turn_id and detailed params
        self.store_tool_call(session_id, agent_name, tool_name, success)

    def finalize_tool_usage(self, session_id: str):
        """Write aggregated stats at end of session."""
        for tool_name, stats in self.tool_usage_cache[session_id].items():
            usage_count = stats['count']
            success_rate = stats['success'] / usage_count if usage_count > 0 else 0.0
            # INSERT aggregated data...
```

Der `AnalyticsDatabaseManager` wurde bewusst neu benannt (statt einfach `DatabaseManager`), um Verwechslungen mit dem Tag 16 Manager zu vermeiden.

## Konfiguration

Tag 19 nutzt zwei YAML-Configs:

### Dashboard-Konfiguration

`config.yaml` für Dashboard-spezifische Settings:

```yaml
# Database Configuration
database:
  path: "heist_analytics.db"  # Local analytics DB

# Dashboard Server Configuration
server:
  host: "0.0.0.0"
  port: 8007
  title: "Heist Analytics Dashboard"
  reload: false

# Chart Configuration
charts:
  agent_colors:
    planner: "#00ffff"     # Cyan
    hacker: "#00ff00"       # Neon Green
    safecracker: "#ffff00"  # Yellow
    mole: "#ff00ff"         # Magenta
```

### Agenten-Konfiguration

`agents_config.yaml` für Heist-Runner:

```yaml
# LLM Configuration
llm:
  base_url: "http://localhost:1234/v1"
  model: "google/gemma-3n-e4b"
  temperature: 0.7
  max_tokens: 1000

# Database Configuration
database:
  path: "heist_analytics.db"  # Same as dashboard

# Session Configuration
session:
  max_turns: 10
  turn_order: ["planner", "hacker", "safecracker", "mole"]
```

Beide Configs zeigen auf die gleiche `heist_analytics.db` im `day_19/` Verzeichnis.

## CLI-Integration

Es wird etwas dynamischer, in dem wir nun eine Command-Line-Interface-Integration einführen.

### Heist Runner

Tag 19 hat einen eigenen Heist-Runner mit CLI-Argumenten. Das heißt, dass wir beim starten des Skripts Parameter übergeben können, um den Lauf zu verändern, ohne etwas an der Konfiguration ändern zu müssen.

```python
# run_heist.py
def main():
    parser = argparse.ArgumentParser(
        description='Run Heist Session with Multi-Agent System'
    )
    parser.add_argument('--config', '-c', type=str, default="agents_config.yaml")
    parser.add_argument('--discovery-url', '-d', type=str, default="http://localhost:8006")
    parser.add_argument('--turns', '-t', type=int, default=5)
    parser.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()

    system = OrchestratorWithAnalytics(
        config_path=args.config,
        discovery_url=args.discovery_url
    )
    system.run_conversation(num_turns=args.turns)
```

### Bash-Script für einfachere Nutzung

Zusätzlich zum Python-Script gibt es ein Bash-Wrapper-Script (`run_heist.sh`), das die Nutzung vereinfacht. Statt immer `python3 run_heist.py --config ... --turns ...` einzugeben, kann man beispielsweise einfach `./run_heist.sh --turns 5` nutzen. Das durfte ich mir in der Form auch neu beibringen. Wieder etwas gelernt 😃 Deswegen versuche ich das folgend etwas detaillierter aufzuschlüsseln.

```bash
# run_heist.sh

# Standard-Werte definieren (werden verwendet wenn keine Parameter übergeben werden)
CONFIG="agents_config.yaml"
TURNS=5
DISCOVERY_URL="http://localhost:8006"

# Schleife durchläuft alle übergebenen Parameter ($# = Anzahl der Parameter)
while [[ $# -gt 0 ]]; do
    case $1 in  # $1 ist der aktuelle Parameter
        -c|--config)
            CONFIG="$2"      # $2 ist der Wert nach dem Parameter
            shift 2          # Verschiebe um 2 Positionen (Parameter + Wert)
            ;;
        -t|--turns)
            TURNS="$2"
            shift 2
            ;;
        -d|--discovery-url)
            DISCOVERY_URL="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="-v"     # Flag ohne Wert
            shift            # Verschiebe um 1 Position
            ;;
        *)
            echo "Unknown option: $1"
            exit 1           # Beende Script mit Fehler
            ;;
    esac
done

# Wechsle ins Verzeichnis wo das Script liegt
cd "$(dirname "$0")"

# Rufe Python-Script mit den gesammelten Parametern auf
python3 run_heist.py --config "$CONFIG" --turns "$TURNS" --discovery-url "$DISCOVERY_URL" $VERBOSE
```

#### Schritt-für-Schritt

##### 1. Standard-Werte setzen
```bash
CONFIG="agents_config.yaml"
TURNS=5
```
Diese Werte gelten, wenn keine Parameter übergeben werden.

##### 2. Die while-Schleife verstehen

Wenn man die `while`-Schleife aufschlüsselt, dann ...:
* **`while`**: Klar, eine normale while-Schleife
* **`[[...]]`**: Das ist die Test-Syntax in Bash. Sie ist ähnlich einer `if`-Abfrage in anderen Sprachen und prüft ob etwas wahr oder falsch ist.
* **`$#`**: Anzahl der Parameter, die übergeben werden. `./run_heist.sh --turns 10 --verbose` beispielsweise liefert `$#=3`.
* **`-gt`**: Das ist der Vergleichsoperator "**g**reater **t**han".
* **`0`**: Naja... Erklärt sich von selbst behaupte ich mal 😉

**Die Parameter-Variablen:**
- `$1` = erster Parameter (z.B. `--turns`)
- `$2` = zweiter Parameter (z.B. `10`)
- `$3` = dritter Parameter (z.B. `--verbose`)
- usw.

##### 3. Case verstehen

Die `case`-Statements in bash kannte ich auch noch nicht. Was passiert hier?
* **`case $1 in`**: Hier beginnt das case-Statement und Variable `$1`wird geprüft.
* **`-v|--verbose`**: Prüft ob `$1`gleich `-v`ODER `--verbose`ist. Die `)` schließt das Muster ab.
* **`VERBOSE="-v"`**: Der Befehl der ausgeführt wird, sollte das obige Muster passen.
* **`;;`**: Ende des Falls. Wie ein `break` in anderen Sprachen und zwingend erforderlich, um Syntax-Fehler zu vermeiden.
* **`*)`**: Catch-all bzw. Default-Fall. Das `else`sozusagen. 
* **`esac`**: Ende des Case-Statements und case rückwärts geschrieben.

Den Rest erkläre ich vielleicht an einem einfachen Beispiel.

##### 4. Ein konkretes Beispiel

Wir rufen zum Beispiel `./run_heist.sh --turns 10 --verbose` auf.

**1. Durchlauf:**
```bash
$1 = "--turns"
$2 = "10"
$# = 3

case $1 in
    -t|--turns)
        TURNS="10"      # Speichere den Wert
        shift 2         # Entferne "--turns" und "10"
```

Nach `shift 2`:
- `$1` wird zu `--verbose` (war vorher `$3`)
- `$#` wird zu 1

**2. Durchlauf:**
```bash
$1 = "--verbose"
$# = 1

case $1 in
    -v|--verbose)
        VERBOSE="-v"
        shift           # Entferne nur "--verbose"
```
Nach `shift`:
- `$#` wird zu 0
- Schleife endet

#### 4. Python-Script aufrufen

Am Ende werden die gesammelten Werte verwendet:

```bash
python3 run_heist.py --config "$CONFIG" --turns "$TURNS" --discovery-url "$DISCOVERY_URL" $VERBOSE
```

Unser Beispiel wird dann zu:
```bash
python3 run_heist.py --config "agents_config.yaml" --turns "10" --discovery-url "http://localhost:8006" -v
```

**Beispiele:**

```bash
# Nutzt alle Standard-Werte (TURNS=5, CONFIG=agents_config.yaml, etc.)
./run_heist.sh

# Überschreibt nur TURNS (andere bleiben Standard)
./run_heist.sh --turns 10

# Überschreibt mehrere Werte
./run_heist.sh --turns 3 --config custom.yaml --verbose
```

Man muss nicht jedes Mal alle Parameter angeben. Die Standard-Werte werden automatisch verwendet, und man überschreibt nur was man ändern möchte.

### Dashboard Server CLI

Der Dashboard-Server akzeptiert ebenfalls CLI-Config:

```python
# dashboard_server.py
parser = argparse.ArgumentParser(description='Heist Analytics Dashboard Server')
parser.add_argument('--config', '-c', type=str, default=None,
                    help='Path to config file (default: day_19/config.yaml)')
args, unknown = parser.parse_known_args()

config = load_config(args.config)
```

Wenn man es mit einer Custom-Config starten möchte, übergibt einfach sie einfach:

```bash
python3 dashboard_server.py --config custom_config.yaml
```

## Dashboard Server

Der Server nutzt die lokale SessionAnalytics-Kopie, die geringfügige Änderungen gegenüber tag 18 aufweist.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from session_analytics import SessionAnalytics  # Local copy!
import yaml
from pathlib import Path

# Load configuration
def load_config(config_file: str = None) -> dict:
    if config_file is None:
        config_file = str(Path(__file__).parent / "config.yaml")

    config_path = Path(config_file)
    if not config_path.is_absolute():
        config_path = Path(__file__).parent / config_file

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()
db_path = config['database']['path']

app = FastAPI(title=config['server']['title'])
analytics = SessionAnalytics(db_path)

@app.get("/")
async def get_dashboard():
    """Serve the Cyberpunk dashboard HTML."""
    return FileResponse(Path(__file__).parent / "dashboard.html")
```

### API Endpoints

Es sind die gleichen Endpoints wie an Tag 18, aber ergänzt um die lokale Analytics-Instanz:

```python
@app.get("/api/sessions")
async def get_sessions():
    sessions = analytics.list_sessions()
    return {"sessions": sessions, "total_sessions": len(sessions)}

@app.get("/api/session/{session_id}")
async def get_session_details(session_id: str):
    return analytics.get_session_details(session_id)

@app.get("/api/tool-stats")
async def get_tool_stats():
    stats = analytics.get_tool_statistics()
    return {"tools": stats["tool_statistics"]}

@app.get("/api/agent-activity/{session_id}")
async def get_agent_activity(session_id: str):
    activity_data = analytics.get_agent_activity(session_id)
    return {
        "session_id": session_id,
        "activity": activity_data["agent_activity"]
    }
```

## WebSocket für Real-Time Updates

**WebSockets** ermöglichen eine bidirektionale, persistente Verbindung zwischen Client (Browser) und Server. Im Gegensatz zu normalen HTTP-Requests (wo der Client fragt und der Server antwortet) können beide Seiten jederzeit Nachrichten senden. Das ist perfekt für Live-Updates im Dashboard - der Server kann neue Session-Daten sofort an alle verbundenen Browsers pushen, ohne dass diese ständig nachfragen müssen.

Der WebSocket-Support erfordert zusätzliche Dependencies, über die ich erst beim Ausführen gestoplert bin 😅

```bash
pip install 'uvicorn[standard]' websockets
```

**Der Connection Manager** verwaltet alle aktiven WebSocket-Verbindungen. Wenn mehrere Benutzer das Dashboard gleichzeitig öffnen, hat jeder eine eigene WebSocket-Verbindung. Der Manager speichert alle diese Verbindungen in einer Liste und kann dann Nachrichten an alle gleichzeitig senden (Broadcasting). 

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Neural.Net",
            "timestamp": datetime.now().isoformat()
        })
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "echo",
                "message": data,
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

Hier, wie auch beim Frontend, habe ich mich allerdings unterstützen lassen müssen.

## Frontend: Cyberpunk 2077 Design

Das Dashboard nutzt ein futuristisches Cyberpunk-Design mit Neon-Farben und ist wie gesagt komplett vibecoded.

[text](day_19_dashboard.md)

Zunächst zu den **C**ascading **S**tyle **S**heets (CSS). Das ist die Sprache, die das Aussehen von Webseiten definiert. Farben, Schriftarten, Größen, Positionen, Animationen, ...

### Farb-Schema

```css
/* Neon Colors */
--cyan: #00ffff;
--magenta: #ff00ff;
--yellow: #ffff00;
--neon-green: #00ff00;
--neon-red: #ff0000;

/* Background */
background: #0a0e27;
```

### Animationen

**Neon-Flicker:**
```css
@keyframes neon-flicker {
    0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
        text-shadow:
            0 0 10px #00ffff,
            0 0 20px #00ffff,
            0 0 30px #00ffff,
            0 0 40px #00ffff;
    }
    20%, 24%, 55% {
        text-shadow: none;
    }
}

h1 {
    animation: neon-flicker 3s infinite;
}
```

**Glitch-Effekt:**
```css
@keyframes glitch {
    0% { transform: translate(0); }
    20% { transform: translate(-2px, 2px); }
    40% { transform: translate(-2px, -2px); }
    60% { transform: translate(2px, 2px); }
    80% { transform: translate(2px, -2px); }
    100% { transform: translate(0); }
}

.agent-badge.suspect {
    animation: glitch 0.3s infinite;
}
```

**Scan-Line:**
```css
@keyframes scan-line {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(100vh); }
}

body::before {
    content: '';
    position: fixed;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, transparent, #ff00ff, transparent);
    animation: scan-line 8s linear infinite;
}
```

### Typografie

Typografie ist die Gestaltung von Schriften und Teil des CSS. Technisch gesehen sind es einfach CSS-Regeln.

```html
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
```

```css
h1 {
    font-family: 'Orbitron', sans-serif;
    font-size: 3em;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 5px;
    color: #00ffff;
}

body {
    font-family: 'Rajdhani', sans-serif;
    color: #00ffff;
}
```

### UI-Elemente

Hier geht es um die UI-Elemente, also die einzelnen visuellen Bausteine der Benutzeroberfläche (oder des **U**ser **I**nterfaces). Das sind alle interaktiven oder visuellen Komponenten, die man als Benutzer sieht.

**Cards mit Neon-Borders:**
```css
.card {
    background: rgba(10, 14, 39, 0.9);
    border: 2px solid #00ffff;
    padding: 25px;
    box-shadow:
        0 0 20px rgba(0, 255, 255, 0.3),
        inset 0 0 30px rgba(0, 255, 255, 0.05);
    transition: all 0.3s;
}

.card:hover {
    border-color: #ff00ff;
    box-shadow:
        0 0 30px rgba(255, 0, 255, 0.5),
        inset 0 0 40px rgba(255, 0, 255, 0.1);
}
```

**Agent Badges:**
```css
.agent-badge {
    padding: 15px 25px;
    background: rgba(0, 0, 0, 0.7);
    border: 2px solid #00ffff;
    font-family: 'Orbitron', sans-serif;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.3s;
}

.agent-badge:hover {
    background: rgba(0, 255, 255, 0.2);
    border-color: #ff00ff;
    box-shadow: 0 5px 20px rgba(255, 0, 255, 0.5);
}
```

## Chart.js Integration

Chart.js ist eine JavaScript-Bibliothek zum Erstellen interaktiver Diagramme und Visualisierungen im Browser und wird im Dashboard verwendet, um die Analytics-Daten visuell darzustelle.

```javascript
function updateActivityChart(data) {
    const ctx = document.getElementById('activityChart').getContext('2d');

    const agents = data.activity.map(a => a.agent_name.toUpperCase());
    const messageCounts = data.activity.map(a => a.message_count);

    const colors = ['#00ffff', '#00ff00', '#ffff00', '#ff00ff'];

    activityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: agents,
            datasets: [{
                label: 'MESSAGE COUNT',
                data: messageCounts,
                backgroundColor: colors.map(c => c + '80'),  // 50% opacity
                borderColor: colors,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    ticks: { color: '#00ffff', font: { family: 'Orbitron' } },
                    grid: { color: 'rgba(0, 255, 255, 0.1)' }
                },
                y: {
                    ticks: { color: '#00ffff', font: { family: 'Orbitron' } },
                    grid: { color: 'rgba(0, 255, 255, 0.1)' },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffff00',
                        font: { family: 'Orbitron', size: 12 }
                    }
                }
            }
        }
    });
}
```

Wir haben jetzt die Architektur, die Datenbank, die API-Endpoints, die WebSocket-Integration und das Frontend mit Chart.js durchgesprochen. 

Im folgenden Abschnitt schauen wir uns an, wie man das Dashboard startet, Heist-Sessions durchführt und die Visualisierungen nutzt.

## Setup & Verwendung

Das Dashboard-System besteht aus mehreren Komponenten, die in der richtigen Reihenfolge gestartet werden müssen. Zuerst brauchen wir die Datenbank, dann die Backend-Services für den Heist-Runner, und schließlich den Dashboard-Server selbst.

### 1. Datenbank Initialisieren

Bevor wir irgendetwas starten können, muss die Analytics-Datenbank existieren. Das Init-Script erstellt alle benötigten Tabellen mit dem Tag 18/19 Schema.

```bash
cd day_19
python3 init_database.py
```

Das erstellt `heist_analytics.db` mit dem passenden Schema (sessions, agents, messages, tool_usage, etc.). Diese Datenbank wird sowohl vom Heist-Runner zum Schreiben als auch vom Dashboard zum Lesen verwendet.

### 2. Services Starten

Wenn wir neue Heist-Sessions generieren wollen, brauchen wir die komplette Tag 16/17 Infrastruktur. Das Dashboard selbst kann auch ohne laufende Services genutzt werden - es zeigt dann nur bereits gespeicherte Daten an.

**Terminal 1 - Day 16 Services:**
```bash
./day_16/start_services.sh
```

**Terminal 2 - Discovery Server:**
```bash
./day_17/start_discovery_server.sh
```

**Terminal 3 - LM Studio:**
- LM Studio öffnen
- Model `google/gemma-3n-e4b` laden
- Server starten (Port 1234)

Diese drei Services (OAuth, Memory, Tool Discovery, und LM Studio) sind die Basis für die Multi-Agent-Konversation. Ohne sie kann der Heist-Runner keine neuen Sessions erzeugen.

### 3. Heist Session Ausführen

Jetzt wo alle Services laufen, können wir eine Heist-Session starten. Der `run_heist.sh`-Script macht das besonders einfach, da wir nicht jedes Mal alle Parameter angeben müssen.

**Terminal 4:**
```bash
cd day_19
./run_heist.sh --turns 5
```

Output:
```
🔧 Initializing orchestrator...
[planner] 🔍 Discovered 4 tools
[hacker] 🔍 Discovered 4 tools
[safecracker] 🔍 Discovered 4 tools
[mole] 🔍 Discovered 4 tools
✓ Session initialized: heist_1766152674
✓ Database: heist_analytics.db
✓ Agents: planner, hacker, safecracker, mole

🚀 Starting conversation (5 turns)...
```

Die Session läuft jetzt und schreibt alle Daten in die `heist_analytics.db`. Jede Agent-Message, jeder Tool-Call, jede Aktion wird gespeichert. Sobald die Session abgeschlossen ist, können wir sie im Dashboard visualisieren.

### 4. Dashboard Starten

Während die Heist-Session läuft (oder auch danach), können wir das Dashboard starten. Es liest die Daten aus der Datenbank und zeigt sie visuell an.

**Terminal 5:**
```bash
./day_19/start_dashboard.sh
```

Output:
```
🔧 Starting Dashboard Server...
🚀 Launching Dashboard Server on port 8007...
✅ Dashboard Server started (PID: 21660)

📋 Dashboard:
   🌐 http://localhost:8007
   📊 http://localhost:8007/docs - API Documentation
```

Der Dashboard-Server läuft jetzt auf Port 8007 und ist bereit, die Analytics-Daten zu präsentieren. Zusätzlich zur Web-UI gibt es auch eine interaktive API-Dokumentation unter `/docs`, die alle verfügbaren Endpoints zeigt. Das kennen wir auch schon.

### 5. Browser Öffnen

Jetzt können wir das Dashboard im Browser öffnen und die Heist-Analytics in voller Cyberpunk-Pracht sehen.

```
http://localhost:8007
```

Das Dashboard zeigt verschiedene Bereiche, die jeweils unterschiedliche Aspekte der Multi-Agent-Konversation visualisieren:

* **⟨⟨ SYSTEM OVERVIEW ⟩⟩**: Gesamt-Statistiken wie Total Sessions, Completion Rate, Average Turns
* **⟨⟨ AGENT ACTIVITY ⟩⟩**: Bar-Chart mit Message-Counts pro Agent
* **⟨⟨ TOOL STATISTICS ⟩⟩**: Visualisierung der Tool-Usage mit Success-Rates
* **⟨⟨ NEURAL FEED ⟩⟩**: Scrollbare Liste der Live-Konversation mit Farbcodierung pro Agent
* **⟨⟨ THREAT DETECTION ⟩⟩**: UI für das Mole-Game (noch nicht funktional)

Wenn die Heist-Session noch läuft, aktualisiert sich das Dashboard dynamisch über WebSocket-Verbindungen. Man kann in Echtzeit sehen, wie neue Messages ankommen und die Charts sich updaten.

### Dashboard Stoppen

Wenn wir mit der Analyse fertig sind, können wir den Dashboard-Server wieder herunterfahren.

```bash
./day_19/stop_dashboard.sh
```

## Troubleshooting

Bei Problemen mit dem Dashboard-Setup (WebSocket-Fehler, fehlende Datenbank, leere Session-Liste, Port-Konflikte, etc.) gibt es detaillierte Lösungen in der [[READM.md#troubleshooting|README]]

## Zusammenfassung

Tag 19 macht Multi-Agent-Analytics sichtbar. Was bisher als JSON-Responses aus einer REST API kam, wird jetzt in einem Cyberpunk-inspirierten Web-Dashboard visualisiert. Das System baut auf dem Analytics-Format von Tag 18 auf und erweitert es um ein FastAPI-Backend mit WebSocket-Support sowie ein Chart.js-Frontend.

Das Dashboard selbst ist eigenständig und benötigt nur Zugriff zur SQLite-Datenbank. Der Heist-Runner hingegen integriert sich mit der Tag 16/17 Infrastruktur, um neue Multi-Agent-Sessions zu erzeugen. Beide Komponenten sind über YAML-Dateien konfigurierbar und bieten CLI-Integration für flexible Nutzung.

Das visuelle Design kombiniert Neon-Farben mit futuristischer Typografie und Animationen und ist vollständig vibecoded 🤷‍♂️ Die Echtzeit-Updates über WebSockets machen Live-Monitoring während laufender Heist-Sessions möglich. Tag 20 wird darauf aufbauen und interaktive Steuerungsmöglichkeiten hinzufügen. Zumindest ist das der Plan.