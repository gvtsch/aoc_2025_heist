# Tag 16: Service Integration

Alle Dokumente zu diesem Beitrag sind in meinem [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_16).

Tag 16 bringt alles zusammen. Wir haben jetzt einzelne Bausteine: OAuth für Security, Tools für Spezialisierung, Memory Service für Context Management, SQLite für Persistenz und Dynamic Agents aus Config-Dateien. Alles funktioniert isoliert. Aber das reicht uns noch nicht. Wir wollen ein integriertes System, wo alle Komponenten zusammenarbeiten.

## Das Problem

Einzelne Services zu bauen ist das eine. Sie zusammenzubringen das andere. Jeder Service hat seine eigene API, seine eigenen Fehler-Modi und seine eigenen Performance-Charakteristiken. Der OAuth Service kann down sein während der Memory Service läuft. Tools können Timeouts haben während die Datenbank schreibt. Ein Agent bekommt sein Token, aber der nächste scheitert usw. usw.

Das ist der Unterschied zwischen Microservices auf dem Papier und Microservices in der Produktion. Auf dem Papier reden alle sauber miteinander. In der Realität gibt es Network Issues, Service Failures, Race Conditions, Inkonsistenzen...

Heute bauen wir das System zusammen, das mit dieser Realität umgehen kann. Hoffentlich 🙏 Dazu bruachen wir:
- **Service Health Checks** bevor es losgeht: Beim Start wird überprüft, ob OAuth, Memory Service und Tools erreichbar sind. So erfahren wir vor Beginn, ob etwas fehlt und nicht erst bei einem Crash.
- **Graceful handling** von Service Failures oder zu deutsch: **Eleganter Umgang** mit Fehlern. Statt hart abzustürzen, wird der Fehler geloggt und das System läuft weiter. So läuft das System bspw. auch bei einem einzelnen Timeout weiter.
- **Konsistente Datenverteilung** über alle Services: Jede Message wird nun synchron in Memory Service und SQLite Datenbank übergeben, um Inkonsistenzen zu vermeiden.
- Eine **Session ID** die durch alle Systeme läuft: Eine ID (z.B. `heist_20250116_143052`) wird bei jedem Service-Call mitgegeben. So markiert man alle Daten als zusammengehörend.
- **Vollständige Audit Trails** in SQLite: Es wird alles geloggt. Welcher Agent hat wann, was gesagt und welches Tool genutzt. Das ermöglicht später Debugging per SQL-Query statt Rätselraten 😉

Das klingt vielleicht gut in der Theorie, aber was bedeutet das konkret? Schauen wir uns einen einzelnen Agent-Turn im Detail an.

Stell dir einen typischen Agent-Turn vor. Der Planner antwortet auf eine Frage. Was muss alles passieren?

**Schritt 1: OAuth Token holen**
```python
token = oauth_client.get_token("planner", ["simulation:read"])
```

Was wenn OAuth Service down ist?

**Schritt 2: LLM Response generieren**
```python
response = llm_client.chat.completions.create(...)
```

Was wenn LM-Studio oder Ollama crashed?

**Schritt 3: In Memory Service speichern**
```python
memory_client.store_memory(agent_id, turn_id, message, session_id)
```

Was wenn der Memory Service einen Timeout hat?

**Schritt 4: In SQLite persistieren**
```python
db.store_message(session_id, turn_id, agent, role, message)
```

Was passiert, wenn die Festplatte voll ist oder es andere Schreib-Konflikte gibt?

Von diesen vier beispielhaften Fehlern kann jeder zum Absturz des Systems führen. Oder man bekommt einen inkonsistenten State mit inkonsistenten Daten. Um das zu vermeiden implementieren wir den `IntegratedAgent`, der alle Services koordinieren und mit Fehlern umgehen soll.

## Integrated Agent Architecture

Die Lösung für Service-Koordination ist der `IntegratedAgent`. Er bekommt beim Erstellen alle Service-Clients (LLM, OAuth, Tools, Memory und Database) und eine Session-ID übergeben. Seine Hauptaufgabe ist, bei jedem Agent-Turn alle Services zu koordinieren und mit Fehlern umzugehen.

Die `respond()` Methode zeigt wie das funktioniert:

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

Der Agent durchläuft alle Schritte der Reihe nach: LLM Response generieren, Memory Service updaten und SQLite persistent speichern. Bei Fehlern gibt es einen Fallback. Die Fehlermeldung wird ebenfalls in SQLite gespeichert.

Das ist nicht perfekt (wir könnten Retries einbauen, Circuit Breakers, etc.), aber viel besser als "hoffen dass nichts schief geht". 😄 

## Database Schema

Jetzt wo der `IntegratedAgent` alle Services koordiniert, brauchen wir eine klare Struktur für die persistente Speicherung. **SQLite** ist unsere Single Source of Truth. Hier landet alles was im System passiert. Aber "alles speichern" ist kein Schema und könnte ggf. schnell aus dem Ruder laufen. Wir brauchen eine Struktur die sowohl Sessions, Messages als auch Tool-Usage tracken kann.

Das wird zum zentralen Audit Log für alles was passiert. Ein Audit Log ist ein Überwachungsprotokoll und enthält eine chronologische Aufzeichunng aller Aktivitäten und Ereignisse innerhalb eines Software-Systems, einer Anwendung usw. 

Das ist wichtig, weil wir so effektiver debuggen können. Außerdem dient es der Compliance. Bei echten Systemen muss man nachweisen können was passiert ist. 

In unserem Fall wird es das folgende loggen:

* Welcher Agent hat zu welchem Zeitpunkt welche Message geschrieben?
* Welches Tool wurde mit welchen Parametern aufgerufen?
* Welche Session lief von wann bis wann?
* Gab es Fehler und wenn ja, wo oder welche?

Wir werden drei verschiedene Datentypen in Tabellen tracken. Da wäre das **sessions** Table:

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

Eine **Session** entspricht einem gesamten Heist-Durchlauf. In der Tabelle wird man nachverfolgen können, wann die Simulation begonnen wurde, wann sie endete, wie viele Turns es gab und ob die Session noch aktiv ist.

Als nächstes die **Messages** Table, die uns zeigen wird, wer was wann gesagt hat.

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

In dieser Tabelle ist jede einzelne Agenten-Nachricht hinterlegt.

Die dritte und letzte Tabelle ist die **Tool usage** Table.

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

Diese Tabelle sagt uns, wer welches Tool mit welchen Parametern benutzt und ob es funktioniert hat.

## Database Manager

Jetzt haben wir das Schema, aber die Agents sollen sich nicht mit SQL-Statements rumschlagen müssen. Der `DatabaseManager` kapselt alle DB-Operationen und bietet eine saubere API.

**Wichtige Methoden** des `DatabaseManager`:
- `create_session(session_id)` - Legt neue Session an
- `store_message(session_id, turn_id, agent, role, message)` - Speichert Agent-Messages
- `store_tool_usage(session_id, turn_id, agent, tool, params, result)` - Loggt Tool-Calls
- `end_session(session_id, num_turns)` - Schließt Session ab

Beispielhaft hier die `store_message()` Methode.

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

Der Agent ruft einfach `store_message()` auf und der Manager kümmert sich um SQL, Timestamps und Commits.

## Memory Service

Neben SQLite als persistenter Datenbank brauchen wir auch einen **Memory Service** für schnellen Context-Zugriff während der Laufzeit. SQLite ist perfekt für Audit Trails und langfristige Persistenz, aber für schnelle In-Memory-Operationen während einer Session brauchen wir etwas leichtgewichtigeres.

Der Memory Service läuft auf Port 8005 und bietet zwei zentrale Funktionen:

**1. Memory Speichern:**
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

**2. Compressed Memory abrufen:**
```python
@app.post("/tools/get_compressed_memory")
async def get_compressed_memory(request: GetCompressedMemoryRequest):
    # Holt die letzten N Messages für einen Agent
    recent_memories = memories[-recent_count:]
    summary = "\n".join([f"Turn {m['turn_id']}: {m['message'][:100]}..."
                         for m in recent_memories])
    return {"summary": summary}
```

Der Memory Service ist bewusst einfach gehalten: Er speichert alles in einem Python Dictionary (`memory_store`). Das reicht für unsere Demo vollkommen aus. In Production würde man Redis oder ähnliches verwenden.

**Wichtig:** Der Memory Service ergänzt SQLite, ersetzt es aber nicht. SQLite bleibt die Single Source of Truth. Der Memory Service ist nur für schnellen Runtime-Zugriff da.

## Der Orchestrator

Wir haben jetzt alle Einzelteile zusammen. Der `IntegratedAgent` koordiniert Services, der `DatabaseManager` speichert Daten persistent, der `ServiceHealthChecker` prüft Services und der `Memory Service` bietet schnellen Context-Zugriff. Irgendwer muss das nun noch alles zusammenbringen und orchestrieren. Und hier kommt der `Orchestrator` ins Spiel.

Der `Orchestrator` ist der zentrale Koordinator (implementiert in der Datei `integrated_system.py`) und durchläuft folgende Schritte:

1. **Config laden:** Liest die System-Konfiguration mit allen Agent-Definitionen und Service-URLs
2. **Session erstellen:** Generiert eine eindeutige Session-ID (z.B. `heist_20250116_143052`) und legt sie in der Datenbank an
3. **Services checken:** Prüft ob OAuth, Memory Service und alle Tools erreichbar sind (Fail Fast!)
4. **Clients initialisieren:** Erstellt LLM, OAuth, Tool, Memory und Database Clients
5. **Agents erstellen**: Instanziiert alle Agents mit ihren Service-Dependencies und der Session-ID
6. **Conversation ausführen**: Lässt die Agents in definierten Turns miteinander sprechen
7. **Session beenden**: Schließt die Session in der Datenbank ab

Der `Orchestrator` ist quasi die `main()`-Funktion unseres gesamten Service-Ökosystems.

Schauen wir uns die wichtigsten Teile im Detail an.

### Service Health Checks

Bevor wir mit der eigentlichen Orchestrierung beginnen, müssen wir sicherstellen, dass alle Services erreichbar sind. Wir wollen Fail Fast, nicht Fail Late. Wenn der OAuth Service down ist, wollen wir das beim System-Start wissen, nicht nachdem der erste Agent versucht hat ein Token zu holen und scheitert.

Der `ServiceHealthChecker` prüft, ob Services erreichbar sind:

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

Der Service Health Check wird beim Start über die Methode `_check_services()` ausgeführt:

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

Die Ausgabe könnte dann so aussehen:

```bash
🏥 Checking service health...
✅ OAuth Service is healthy
✅ Memory Service is healthy
❌ Tool Service (calculator) is unreachable: Connection refused
⚠️  System starting with degraded services
```

Du siehst sofort welche Services laufen und welche nicht. Das spart Zeit.

### Session Management

Das Herzstück der Integration ist die Session ID. Eine ID die beim System-Start generiert und durch alle Services gezogen wird:

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

Wir müssen verschiedene Sessions unterscheiden können. Wenn wir morgen das System nochmal starten, ist das eine neue Session. Die Messages sollten nicht mit den heutigen vermischt werden.

Mit Session IDs können wir:
- Mehrere Heist-Runs parallel tracken
- Historische Sessions analysieren
- A/B Tests verschiedener Agent-Configs vergleichen
- Debug-Logs einer spezifischen Session isolieren

Die Session ID fließt in alle Service Calls:

```python
# Memory Service
memory_client.store_memory(agent_id, turn_id, message, self.session_id)

# SQLite
db_manager.store_message(self.session_id, turn_id, agent, role, message)

# Tool Usage
db_manager.store_tool_usage(self.session_id, turn_id, agent, tool, params, result)
```

So entsteht ein konsistenter Audit Trail über alle Services hinweg.

### Orchestrator Implementation

Der `Orchestrator` bringt alles zusammen:

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

Die Conversation Logic ist simpel, weil die Komplexität in die Agents verlagert wurde:

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

Die Run-Logic kennt keine Service-Details mehr. Kein OAuth-Handling, kein Memory-Management, kein Database-Persistence. Alles ist in die IntegratedAgents gekapselt. Stichwort: Separation of Concerns.

## Was bringt uns das?

Fehler finden wird einfacher. Statt "Was ist passiert?" schreiben wir jetzt `SELECT * FROM messages WHERE session_id = X`. Jede Nachricht ist in SQLite. Jeder Tool-Aufruf. Jeder Agent-Turn. Mit Session ID, Zeitstempel und Agent Name.

Services können ausfallen. Das System läuft trotzdem weiter. Die Checks beim Start zeigen uns sofort was fehlt. Jeder Agent-Turn fängt Fehler ab. Das System degradiert statt abzustürzen.

Der State wird konsistent. Eine Session ID durch alle Services. Alles wird synchron in Memory und Datenbank geschrieben. Keine Race Conditions.

Das ist nun nicht mehr "Demo-Code der hoffentlich funktioniert". Das ist robuste Integration mit Überwachung, Logging und Fehlerbehandlung.

## Die Kosten bzw. Nachteile

Mehr Services bedeuten mehr Abhängigkeiten. OAuth Service, Memory Service, SQLite und LM Studio müssen alle laufen. Fällt einer aus, kann das System blockieren.

Mehr Latency. Ein Agent-Turn macht jetzt einen LLM Call, einen Memory Service Call und ein SQLite Write. Das addiert sich.

Mehr Error-Modes. Network Timeouts. Service Crashes. Database Locks. Mehr Dinge die kaputt gehen können.

Für eine professionelle Anwendung ist das der richtige Trade-off. Für einen Quick Prototype vielleicht eher Overkill 😄 Wir sind jetzt klar auf der "robusten" Seite.

## Ausblick

Das System ist funktional. Aber nicht perfekt. Für echte eine echte Anwendung würden wir noch brauchen:

- Retry Logic mit Exponential Backoff
- Circuit Breakers für failing Services
- Async Operations für parallele Writes
- Distributed Tracing mit OpenTelemetry

Aber das sind Optimierungen. Das Fundament steht.

## Zusammenfassung

Wir haben einzelne Services zu einem integrierten System zusammengeführt. Das ist der Unterschied zwischen "Microservices die im Vacuum funktionieren" und "Microservices die zusammenarbeiten".

Was wir gebaut haben:
- `IntegratedAgent` der alle Services koordiniert
- `DatabaseManager` für vollständige Audit Trails
- `ServiceHealthChecker` für Fail Fast Behavior
- Session Management für konsistente State Tracking
- Error Handling für robuste Service Integration

Alle Services reden miteinander. Das ist der Moment wo aus einzelnen Komponenten ein echtes System wird.

## Verwendung

Quick Start

> # 1. Services starten
> ./day_16/start_services.sh
>
> # 2. LM Studio mit Gemma starten (Port 1234)
> # Manuell in LM Studio GUI
> 
> # 3. Agent System ausführen
> python day_16/integrated_services.py
>
> # 4. Services stoppen
> ./day_16/stop_services.sh