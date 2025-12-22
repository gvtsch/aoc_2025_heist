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

Alle Dokumente zu diesem Beitrag sind in meinem [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_20) zu finden.

Gestern haben wir das Projekt visualisiert. Heute machen wir aus dem Dashboard ein echtes Command Center – mit bidirektionaler Kommunikation, Live-Control und Command-Injection.

## Das Problem

Das Dashboard aus Tag 19 ist read-only. Wir sehen was passiert, können aber nicht eingreifen. Wenn ein Agent falsch entscheidet können wir nur zusehen. Wenn wir den Überfall pausieren wollen um Strategien zu diskutieren haben wir keine Möglichkeit dazu. Allerdings ist das auch nur wieder ein Konstrukt, um etwas zum Interagieren hinzuzufügen. wirklich sinnvoll ist das so wohl nicht. Ich werde es zumindest eher nicht diskutieren 😄

Ein echtes Command Center braucht Controls. Unser Heist Command Center sollte Missionen pausieren, Strategien anpassen und neue Instruktionen an Agents senden können.

## Die Lösung

Ein interaktives Dashboard mit bidirektionaler Kommunikation. Der Backend-Server akzeptiert nicht nur GET-Requests, sondern auch POST-Commands. Das Frontend sendet User-Actions an den Server. Der Server steuert die laufenden Heist-Sessions.

In einem professionellen Umfeld könnte man so etwas einsetzen, um Multi-Agent-Systeme in der Produktion zu überwachen und zu steuern. Zum Beispiel, um automatisierte Trading-Bots zu pausieren wenn Marktanomalien auftreten, Kundenservice-Agents mit Echtzeit-Instruktionen bei unerwarteten Szenarien zu unterstützen, oder Produktions-Workflows bei Fehlern zu unterbrechen und manuell zu korrigieren.

Um das umzusetzen, führen wir neue Komponenten ein.

### Neue Komponenten

* **HeistController**: Backend-Klasse, die laufende Sessions verwaltet. Ermöglicht Pause/Resume, Command-Injection, Status-Tracking.
* **Interactive Dashboard Server**: Erweitert den Server von Tag 19 um Control-Endpoints: POST-Endpoints für Pause, Resume, Commands.
* **Interactive Frontend**: Erweitert Tag 19's UI um Control-Panels und Command-Forms.

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

Das ist bidirektionale Kommunikation. User -> Server -> Agents und Agents -> Server -> User.

## HeistController

Der HeistController ist die zentrale Klasse für das Session-Management. Sie nutzt `HeistStatus` um den Zustand einer Session zu repräsentieren (z.B. `HeistStatus.RUNNING.value` -> `"running"`).

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

Der Controller hat drei Datenstrukturen:

* **active_sessions**: Dict aller laufenden Sessions mit Status (als String-Wert aus HeistStatus), Agents, Config.
* **command_queue**: Queue von Commands die an Agents gesendet wurden aber noch nicht ausgeführt sind.
* **pause_flags**: Flags, die anzeigen ob eine Session pausiert ist.

Die wichtigsten Methoden des Controllers sind **Start Session**, **Pause und Resume** und **Command Injection**.

### Start Session

Eine neue Session wird mit Status RUNNING, einer Agent-Liste und einer Konfiguration initialsiert. Die Command-Queue und das Pause-Flag werden auf leer/false gesetzt.


```python
def start_session(self, session_id: str, agents: List[str], config: Dict) -> Dict:
    self.active_sessions[session_id] = {
        "session_id": session_id,
        "status": HeistStatus.RUNNING.value,
        "agents": agents,
        "config": config,
        "start_time": datetime.now().isoformat(),
        "current_turn": 0,
        "mole": None,  # Wird in Tag 21 zufällig gewählt
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


### Pause und Resume

Pause setzt den Status auf PAUSED und das Flag auf true. Resume setzt es zurück auf RUNNING und false. Das Agent-System prüft regelmäßig `is_paused()` und blockiert bei true. 

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

So wird die Möglichkeit gegeben, aktiv durch z.B. **Command Injection** in den Ablauf einzugreifen.

### Command Injection

Commands/Befehle werden in die Queue gestellt. Die Agents prüfen vor jedem Turn ob Commands für sie ausstehend sind. Wenn ja werden sie in den LLM Context als "Override Instruction from Command Center" injiziert.

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

Das ermöglicht die besagten Korrekturen während eines laufenden Überfalls. Wenn der Hacker vergisst die Kameras zu deaktivieren, kann ein Befehl gesendet werden: "Disable camera 3 immediately".

Schauen wir uns nun genauer an, wie diese Command Injection in der Praxis funktioniert.

## Command Injection während der Ausführung

Ein interaktives Dashboard ermöglicht es uns, während einer laufenden Session direkt in das Geschehen einzugreifen. Und wie funktioniert das?

### 1. Command Injection

Über das Dashboard oder die API können wir Commands an einzelne Agents senden. Diese Befehle werden in die Command-Queue der laufenden Session eingefügt und warten dort auf ihre Ausführung. Der `HeistController` prüft bei jedem Turn, ob neue Commands in der Queue vorhanden sind, und leitet diese an die entsprechenden Agents weiter.

### 2. Echtzeit-Feedback

Sobald ein Command ausgeführt wird, benachrichtigt das System das Dashboard über WebSockets. Alle Änderungen wie Status-Updates oder Log-Einträge werden dadurch sofort und ohne Verzögerung im Dashboard angezeigt. Alle verbundenen Clients sehen die gleichen Updates in Echtzeit.

### 3. Beispiel: Command senden

Ein Command kann über die API wie folgt gesendet werden:

```bash
curl -X POST http://localhost:8008/api/heist/<session_id>/command \
-H "Content-Type: application/json" \
-d '{"agent": "hacker", "command": "Disable camera"}'
```

### 4. Auswirkungen

Der Unterschied zwischen normaler Ausführung und Command-gesteuerter Ausführung ist deutlich sichtbar: Ohne Command führt ein Agent seine vorgesehene Standardaktion aus, zum Beispiel "Hacke Tür A". Mit einem gesendeten Command priorisiert der Agent jedoch die neue Anweisung und führt stattdessen beispielsweise "Hacke Tür B" aus.

### 5. Testen

Um die Funktionalität selbst zu erleben, nutze das Demo-Skript `demo_live_control_verbose.py`. Starte in einem Terminal eine Session mit `run_controlled_heist.py` und sende in einem zweiten Terminal Commands über das Demo-Skript. Du kannst dann live beobachten, wie die Agents auf die neuen Anweisungen reagieren und ihr Verhalten entsprechend anpassen. Eine detaillierte Anleitung findest du weiter unten im Abschnitt "Live Control Demo".

Natürlich funktioniert die Command-Injection auch direkt über das Dashboard im Browser. Dazu benötigen wir aber zunächst den entsprechenden Server mit seinen Endpoints.

## Interactive Dashboard Server

Der Server erweitert die Endpoints von gestern um Control-Funktionen. Er nutzt weiterhin die SessionAnalytics für Lese-Operationen und den HeistController für Schreib-Operationen.

**Hinweis:** Tag 20 enthält eine lokale Kopie von `session_analytics.py`, um eine vollständig standalone Deployment-Unit zu schaffen. Das ermöglicht es, `day_20` als eigenständiges Paket zu nutzen, ohne Abhängigkeiten zu `day_18` zu haben. In einer Production-Umgebung würde man dies über separate Microservices lösen.

```python
from fastapi import FastAPI, WebSocket
from day_20.session_analytics import SessionAnalytics  # Lokale Kopie für Standalone-Deployment
from day_20.heist_controller import HeistController, get_controller

app = FastAPI(title="Interactive Heist Command Center")
analytics = SessionAnalytics()
controller = get_controller()
```

### Control Endpoints

Der Server stellt drei zentrale POST-Endpoints bereit, um Sessions aktiv zu steuern: Start, Pause/Resume und Command-Injection.

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

Alle Control-Actions broadcasten Events über WebSocket. Alle verbundenen Clients sehen in Echtzeit was passiert.

### Status Endpoints

Neben den Control-Endpoints gibt es auch GET-Endpoints, um den aktuellen Zustand der Sessions abzufragen. Diese ermöglichen dem Frontend, kontinuierlich Status-Updates zu holen.

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

Diese Endpoints ermöglichen dem Frontend kontinuierlich Status-Updates zu holen.

## Interactive Frontend

Das Frontend erweitert das Dashboard um Control-Panels. Und ist auch vibecoded 😉 Aber ich lerne dadurch dazu!

### Heist Control Panel

Das Heist Control Panel ist das Herzstück der Steuerung. Aber bei einem Projekt dieser Größe ernsthaft von Herzstück und Control Panel zu reden ist schon fast etwas ironisch 😄 Es bietet drei zentrale Funktionen: Pause, Resume und Status-Refresh. Der Pause-Button stoppt alle laufenden Agents sofort, der Resume-Button setzt die Ausführung fort, und der Refresh-Button aktualisiert den angezeigten Session-Status. Das Panel zeigt außerdem immer an, welche Session gerade aktiv ist.

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

Die JavaScript-Implementierung sendet POST-Requests an die entsprechenden Endpoints und updated das UI basierend auf der Server-Response.

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

Der Ablauf gestaltet sich einfach. Sobald der Benutzer auf den Pause-Button klickt, sendet das Frontend einen POST-Request an den Server. Der HeistController empfängt diesen Request, setzt den Session-Status auf PAUSED und aktiviert das entsprechende Pause-Flag. Im Anschluss broadcastet der Server das Event über WebSocket an alle verbundenen Clients. Das Dashboard empfängt die Nachricht, aktualisiert die Buttons (Pause wird ausgeblendet, Resume wird sichtbar) und zeigt den neuen Status-Badge an. Durch die WebSocket-Kommunikation sehen alle verbundenen Clients die Statusänderung unmittelbar und in Echtzeit.

### Agent Command Center

Das Agent Command Center ermöglicht es, während der laufenden Ausführung direkt mit einzelnen Agenten zu kommunizieren. Über ein Dropdown-Menü wird der Ziel-Agent ausgewählt, in einem Textfeld der Befehl eingegeben und mit einem Klick wird der Command zur Ausführung an den Server gesendet. Der Command wird in die Queue eingereiht und beim nächsten Turn des Agenten als Override-Instruktion in dessen LLM-Kontext injiziert.

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

Die JavaScript-Funktion sammelt die Eingaben, erstellt ein JSON-Objekt und sendet es per POST-Request an den Server:

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

Der Ablauf: Benutzer wählt einen Agenten aus, tippt einen Befehl ein und klickt Send. Der POST-Request wird gesendet, der Command landet in der Queue, und der Agent holt ihn beim nächsten Turn ab. Die Bestätigung wird sofort im Activity Log angezeigt.

### Activity Log

Das Activity Log ist die zentrale Chronik aller Dashboard-Events. Jede Benutzeraktion, jeder Statuswechsel und jede System-Benachrichtigung wird hier mit einem Zeitstempel protokolliert. Das Log zeigt die neuesten Einträge oben an und behält automatisch nur die letzten 50 Einträge, um die Performance zu gewährleisten. Verschiedene Event-Typen werden farblich unterschieden: Erfolge in grün, Warnungen in orange und Fehler in rot.

Das HTML-Element ist bewusst minimalistisch gehalten und dient als Container für die dynamisch erzeugten Log-Einträge:

```html
<div class="card">
    <h2>📋 Activity Log</h2>
    <div id="activityLog">
        <div class="log-entry log-info">System initialized...</div>
    </div>
</div>
```

Die JavaScript-Funktion `addLog()` übernimmt die Erstellung und Verwaltung der Log-Einträge. Sie fügt jeden neuen Eintrag am Anfang des Logs ein, versieht ihn mit einem Zeitstempel und weist ihm eine CSS-Klasse basierend auf dem Event-Typ zu.

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

Jede Benutzerinteraktion wird sofort protokolliert. Commands die an Agenten gesendet werden, Pause- und Resume-Aktionen, Statusänderungen der Session und alle WebSocket-Events. Das Log wird von allen anderen UI-Komponenten genutzt und bietet eine vollständige Timeline aller Dashboard-Aktivitäten. Durch die chronologische Reihenfolge mit Zeitstempeln lässt sich der Ablauf eines Heists lückenlos nachvollziehen.

### WebSocket Integration

Die WebSocket-Integration ist das Nervensystem (schon wieder sehr hochtrabend für unser kleines Projekt 😉) des Dashboards und ermöglicht bidirektionale Echtzeit-Kommunikation zwischen Server und allen verbundenen Clients. Während die REST-Endpoints für explizite User-Aktionen zuständig sind, sorgt WebSocket dafür, dass alle Clients automatisch über jede Änderung im System informiert werden. Ohne WebSocket müsste das Dashboard kontinuierlich Polling betreiben, was ineffizient wäre und zu Verzögerungen führen würde.

Die zentrale Message-Handler-Funktion verarbeitet eingehende Server-Broadcasts und aktualisiert die UI entsprechend. Jeder Event-Type triggert spezifische UI-Updates.

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

Die verschiedenen Event-Typen haben unterschiedliche Funktionen. `heist_started` initialisiert eine neue Session und setzt die aktuelle Session-ID im Dashboard. `heist_paused` und `heist_resumed` triggern Status-Updates und ändern die Sichtbarkeit der Control-Buttons. `command_sent` zeigt die Command-Bestätigung im Activity Log an. `mole_detected` wird für das Mole-Detection-Game in Tag 21 genutzt.

Alle WebSocket-Events durchlaufen denselben Ablauf. Der Server broadcastet ein Event an alle verbundenen Clients, der Client empfängt das Event über die WebSocket-Verbindung, die Handler-Funktion wertet den Event-Type aus, die entsprechenden UI-Komponenten werden aktualisiert und das Activity Log erhält einen neuen Eintrag. Dadurch sehen alle Benutzer, die das Dashboard geöffnet haben, exakt dieselben Updates zur gleichen Zeit. Wenn ein Benutzer eine Session pausiert, sehen alle andere Benutzer sofort den "Heist paused" Badge und die entsprechenden Log-Einträge.

## Integration mit Agent System

Die Integration des HeistControllers mit dem Agent-System ist der entscheidende Schritt, der aus einer passiven Infrastruktur ein interaktives System macht. Ohne diese Integration würden Pause-Flags und Commands zwar im Controller gespeichert, aber die Agenten würden davon nichts mitbekommen und einfach weiterlaufen. Die `IntegratedAgentWithController` Klasse schließt diese Lücke, indem sie die Agenten aus Tag 16 um das "Controller-Bewusstsein" erweitert.

Die Klasse überschreibt die `respond()`-Methode und fügt vor der eigentlichen LLM-Antwort drei kritische Prüfungen ein.

```python
from day_16.integrated_system import IntegratedAgent
from heist_controller import get_controller

class IntegratedAgentWithController(IntegratedAgent):
    """Erweitert IntegratedAgent um HeistController-Integration."""

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

Die vier Schritte im Detail. 
* **Schritt 1** prüft, ob die Session pausiert ist. Falls ja, wird sofort eine Pause-Nachricht zurückgegeben ohne das LLM zu konsultieren. Der Agent blockiert effektiv, bis Resume aufgerufen wird. 
* **Schritt 2** holt alle ausstehenden Commands für diesen spezifischen Agenten. Wenn Commands vorliegen, wird der erste Command als System-Message mit höchster Priorität in den Kontext eingefügt. Das `OVERRIDE INSTRUCTION`-Präfix signalisiert dem LLM, dass dieser Befehl Vorrang vor allen anderen Anweisungen hat. 
* **Schritt 3** updated den Turn-Counter im Controller, damit das Dashboard immer den aktuellen Fortschritt anzeigen kann. 
* **Schritt 4** ruft die normale `respond()`-Methode der Parent-Klasse auf, die den modifizierten Kontext (mit injiziertem Command) an das LLM sendet.

Das Ergebnis ist ein Agent, der sich nahtlos in das interaktive Dashboard einfügt.

### Verwendung der Controller-Integration

Die Verwendung der Controller-integrierten Agenten unterscheidet sich kaum von den Standard-Agenten aus Tag 16. Der einzige Unterschied ist, dass jeder Agent eine `session_id` zugewiesen bekommt, die ihn mit dem HeistController verbindet.

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

Der wichtige Unterschied liegt im Verhalten zur Laufzeit. Während ein normaler Agent seinen Turn immer ausführt, prüft der Controller-integrierte Agent zunächst den Pause-Status und die Command-Queue. Diese Prüfungen sind transparent für den aufrufenden Code, passieren aber bei jedem `respond()`-Aufruf automatisch im Hintergrund.

Das Demo-Script `run_controlled_heist.py` zeigt die vollständige Integration in Aktion. Es startet eine Session mit vier Controller-bewussten Agenten und ermöglicht Live-Control über die API.

```bash
python3 day_20/run_controlled_heist.py --demo
```

Der Ablauf bei jedem Agent-Turn ist gleich. Vor jedem Response-Call prüft der Agent zuerst das Pause-Flag. Wenn die Session pausiert ist, gibt er sofort eine Pause-Nachricht zurück und überspringt die LLM-Generierung komplett. Falls nicht pausiert, prüft er die Command-Queue für ausstehende Befehle. Wenn Commands vorliegen, injiziert er diese als Override-Instruktion in den Kontext und markiert sie als ausgeführt. Erst nach diesen Prüfungen wird das LLM aufgerufen, das dann den (möglicherweise modifizierten) Kontext verarbeitet. Der Agent antwortet entsprechend den injizierten Commands oder führt seine Standard-Logik aus, falls keine Commands vorlagen.

Diese Architektur ermöglicht Interventionen während der Ausführung. Commands können zu jedem Zeitpunkt während der Ausführung gesendet werden und beeinflussen den nächsten Turn des Ziel-Agenten unmittelbar. Pause-Aktionen stoppen die gesamte Session sofort, ohne dass Code-Änderungen oder Restarts nötig sind.

## Verwendung

Ich möchte nun kurz auf die Verwendung eingehen, ohne alles noch mal detailliert zu erklären. 

### Server starten

```bash
./day_20/start_interactive_dashboard.sh
```

Der Server startet auf Port 8008:

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

### Dashboard öffnen

Navigiere zu `http://localhost:8008`. Das Dashboard zeigt alle Control-Features. Die API-Dokumentation findest du unter `http://localhost:8008/docs`.

### Heist pausieren

1. Click "⏸️ Pause Heist"
2. UI zeigt "Heist Paused" Badge (orange)
3. Resume-Button erscheint

Zum Fortsetzen: Click "▶️ Resume Heist"

### Command senden

1. Wähle Agent aus Dropdown
2. Tippe Command (z.B. "Disable security camera 3")
3. Click "📤 Send"
4. Activity Log zeigt Bestätigung
5. Agent erhält Command beim nächsten Turn als `OVERRIDE INSTRUCTION`

**Tipp:** Formuliere Commands klar und konkret. "Scan room for guards" ist besser als "Do something". Nobrainer 😄

## Testing

Für das Testing gibt es mehrere Ebenen:

**API-Tests** (`test_interactive_dashboard.py`): Testet alle Server-Endpoints ohne echte Agents - Health Check, Session Management, Command Injection, Pause/Resume und Mole Detection. 11 Tests in wenigen Sekunden.

**Live Control Demo** (`demo_live_control_verbose.py`): Zeigt die Interaktion mit echten LLM-gesteuerten Agents. Commands werden als `OVERRIDE INSTRUCTION` in den LLM-Kontext injiziert und beeinflussen das Verhalten in Echtzeit.

**Mole Game Integration** (`test_mole_game_integration.py`): End-to-End Test des Mole Detection Games mit zufälliger Mole-Auswahl und Evaluation.

Für eine detaillierte Schritt-für-Schritt-Anleitung siehe [Testing Guide](day_20_testing_guide.md). 

## Zusammenfassung

Tag 20 verwandelt das passive Dashboard aus Tag 19 in ein interaktives "Command Center". Die neue Architektur basiert auf bidirektionaler Kommunikation zwischen User, Server und Agents und ermöglicht aktive Eingriffe während der Laufzeit.

Der HeistController verwaltet alle laufenden Sessions und trackt deren Status (RUNNING, PAUSED, COMPLETED, FAILED). Er verwaltet Command-Queues für einzelne Agents und ermöglicht Pause- und Resume-Funktionen. Der Interactive Dashboard Server erweitert die API um POST-Endpoints für Steuerungsoperationen, wie Heists pausieren, fortsetzen und Commands senden. Alle Aktionen werden über WebSockets an alle Clients gebroadcastet.

Das Frontend bietet nun drei Control-Panels. Heist Control (Pause/Resume), Agent Command Center (Commands während der Ausführung senden) und Activity Log (chronologische Protokollierung aller Aktionen). Die IntegratedAgentWithController-Klasse prüft vor jedem Response automatisch Pause-Status und Command-Queue. Commands werden als Override-Instruktion in den LLM-Context injiziert.

Wieder ein Schritt weiter. Ein paar Schritte fehlen noch.

## Quick-Start

Schnellstart für die Ungeduldigen:

```bash
# 1. Server starten
./day_20/start_interactive_dashboard.sh
# Oder direkt: python3 day_20/interactive_dashboard_server.py

# 2. Dashboard öffnen
open http://localhost:8008

# 3. Controlled Heist Demo starten (in separatem Terminal)
python3 day_20/run_controlled_heist.py --demo
```

Jetzt kannst du im Dashboard:
- Den Heist live verfolgen
- Session pausieren/fortsetzen
- Commands an Agents senden
- Die Mole-Detection spielen

Für detaillierte Anleitungen siehe [QUICKSTART.md](QUICKSTART.md) und [Testing Guide](day_20_testing_guide.md).
