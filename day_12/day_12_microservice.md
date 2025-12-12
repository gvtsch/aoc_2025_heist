
An Tag zwölf wird's wieder spannender... Wir machen aus unserem Memory-System einen echten Microservice! Und dazu setzen wir auf das **Model Context Protocol (MCP)**, welches ursprünlgich von Anthropic implementiert wurde und der der Quasi-Standard für LLM-Tools ist.

Daran habe ich tatsächlich nun länger gesessen, als mir lieb ist. Viel neues :) 


**Was ist das Problem?** 

Bisher hatte jeder Agent sein eigenes Gedächtnis. Das führt zu **Code-Duplizierungen**, weil für jeden Agenten ein eigenes Memory programmiert werden muss. Evtl. führt das sogar **Inkonsistenzen**, weil unterschiedliche Memory-Strategien implementiert werden. Das kann durchaus auch gewollt sein und ist auch mit MCP immer noch möglich. Schwierig oder anstrengend wird es aber spätestens beim **Skalieren**. Was, wenn wir nicht mehr von drei oder vier Agenten reden, sondern von 20?

An Tag drei haben wir erstmals das Gedächtnis ins leben gerufen und jeder Agent hatte eine eigene Liste. An Tag sieben haben wir außerdem eine gemeinsame Liste bzw. ein gemeinsames Gedächtnis für alle Agenten definiert. Die Implementierungen sahen wie folgt aus:

```python
class AgentWithMemory: 
    def __init__(self, persona: str):
        self.persona = persona
        self.conversation_history = []  
        
class MultiAgentSystem:  
    def __init__(self):
        self.conversation = []
```

Und nun versuchen wir das zu verbessern und die oben genannten Nachteile durch MCP zu verbessern. Wir bauen einen zentralen Memory-Service, der das **Model Context Protocol** implementiert.

## Was ist MCP überhaupt?

Das **Model Context Protocol (MCP)** ist Anthropics Standard für LLM-Tools. Statt dass jeder Entwickler seine eigenen API-Endpunkte erfindet, gibt MCP klare Regeln vor:

- **Einheitliche Endpunkt-Namen** (`/tools/...`)
- **Standardisierte Datenstrukturen** (Request/Response Models)
- **Tool Discovery** (Agents finden Tools automatisch)
- **Community-Kompatibilität** (funktioniert mit allen MCP-Clients)

Diese Punkte klingen erstmal theoretisch und konstruiert. Aber in der Praxis ist das ein großes Thema. Stell dir vor, du willst deinen Agent mit verschiedenen Services verbinden und musst für jeden Service eine API schreiben oder ansprechen ... Das könnte recht aufwendig werden.

Aktuell erfindet jeder Entwickler seine eigenen API-Endpunkte. Memory Service von Firma A nutzt `POST /api/v1/memories/store`, während Firma B `POST /memory/save` verwendet. Firma C wiederum hat `POST /agent/store-message` implementiert, und bei Firma D heißt es `POST /chat/add-turn`. Alle machen dasselbe, aber jeder spricht eine andere Sprache.

Das führt dazu, dass dein Agent für jeden Service neu programmiert werden muss. Willst du drei verschiedene Services nutzen? Dann musst du drei verschiedene API-Integrationen schreiben. Bei 20 Services sind das 20 verschiedene Integrationen. Du siehst wo das hin führt... 

Mit MCP ist das anders. Hier folgen alle Services demselben Standard. Memory speichern heißt überall `POST /tools/store_memory`, letzte Nachrichten abrufen ist immer `POST /tools/get_recent_turns` und Compression läuft über `POST /tools/get_compressed_memory`. Egal welcher Service, egal welcher Anbieter. Der Vorteil liegt auf der Hand, oder?!

Ohne MCP muss dein Agent verschiedene APIs lernen. Er braucht eigene Verbindungen für den Memory Service, eine andere für den Search Service und wieder eine andere für Berechnungen. Jede mit eigenen Methoden, eigenen Datenstrukturen, eigenen Fehlercodes.

Mit MCP dagegen entdeckt dein Agent automatisch alle verfügbaren Tools. Er spricht eine einzige, standardisierte Sprache und kann sofort jeden MCP-kompatiblen Service nutzen. 
Kommt z.B. ein neuer Service online, erkennt der Agent ihn automatisch und kann ihn sofort verwenden, ohne dass wir eine Zeile Code ändern mussten.

Ich versuche es mal mit einer Analogie. 
MCP funktioniert wie USB für Computer. Früher hattest du verschiedene Anschlüsse für Maus, Tastatur, Drucker und externe Festplatten (in so fern du denn noch das Vergnügen dazu hattest :)). 
Heute haben alle Geräte einen USB Anschluss und wir stecken sie in den entsprechenden Port und alles funktioniert. Genauso macht MCP aus dem API-Chaos einen einheitlichen Standard für LLM-Tools.

Kommen wir zu unserer Implementierung und unserem Service.

## Unsere Services

Unser Service stellt drei standardisierte Tools zur Verfügung:

### 1. Memory speichern
```python
@app.post("/tools/store_memory")
async def tool_store_memory(request: StoreMemoryRequest):
    # Agent schickt: "Planner said: We go at 2 AM"
    # Service speichert mit Timestamp und Session-ID
```

### 2. Letzte Nachrichten holen  
```python
@app.post("/tools/get_recent_turns")
async def tool_get_recent_turns(request: GetRecentTurnsRequest):
    # Agent fragt: "Gib mir die letzten 5 Messages"
    # Service filtert nach Agent + Session und gibt zurück
```

### 3. Komprimierte Zusammenfassung
```python  
@app.post("/tools/get_compressed_memory")
async def tool_get_compressed_memory(request: GetCompressedMemoryRequest):
    # Agent fragt: "Fass die alte History in 50 Token zusammen"  
    # Service nutzt hierarchische Kompression (siehe Tag 11: Memory Compression)
```

Der MCP-Standard verlangt saubere Datenstrukturen. Mit Pydantic definieren wir diese zu:

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

Das sorgt für **automatische Validierung**, **API-Dokumentation** und **Type Safety**. Davon profitiert man in vielerlei Hinsicht.


Und wie sieht die Anwendung nun in der Praxis aus?

Ein Agent will eine Nachricht speichern:

```python
# Agent als MCP-Client
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

Später will derselbe Agent die History:

```python
# Agent holt seine Memory zurück
get_request = {
    "agent_id": "planner",
    "limit": 5,
    "game_session_id": "heist-2024"
}

response = client.post("/tools/get_recent_turns", json=get_request)
# Response: {"agent_id": "planner", "turns": [...], "turn_count": 1}
```

## Tool Discovery - das Coole an MCP

Der Agent muss nicht wissen, welche Tools verfügbar sind! Er fragt einfach:

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

Die obigen Zeilen (die ich etwas ausgedünnt habe gegenüber der Version im Repo) liefern diesen Output:

```bash
Service: Memory Server (MCP)
Version: 1.0.0
Available Tools: 3

3️⃣ MCP Tools (automatisch entdeckt!)
------------------------------------------------------------
🔍 Agent discovered 3 tools automatically:
  POST /tools/store_memory         → Auto-discovered MCP tool
  POST /tools/get_recent_turns     → Auto-discovered MCP tool
  POST /tools/get_compressed_memory → Auto-discovered MCP tool

📋 Standard Service Endpoints:
  GET    /                              → MCP Tool Discovery
  GET    /health                        → Health Check
```

Und genau dort sind sie, die entdeckten Services. Der Agent lernt zur Laufzeit, was er alles machen kann! Klingt praktisch, nicht wahr?

Wir können aber noch mehr von oder über unseren Service erfahren.
SO braucht z.B. jeder professionelle Service einen Health Check:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "memory-server", 
        "timestamp": datetime.now().isoformat()
    }
```

Damit können Load Balancer und Monitoring-Tools prüfen, ob der Service läuft.

Und da geht sicher noch sehr viel mehr. Ich steige auch gerade erst in das Thema ein und habe noch viel zu lernen!

## Warum ist das besser?

Noch mal die Vorteile zusammengefasst, nachdem wir nun gesehen haben, wie man es implementieren kann. Der zentrale MCP Memory Service bringt uns drei entscheidende Vorteile. 

**Skalierung wird zum Kinderspiel.** VOrher lief bei jedem Agent eine eigene Memory-Instanz. Das bedeutet 10 Agents, 10 Memory-Objekte im Speicher, 10-mal dieselbe Logik geladen. Mit dem zentralen Service haben wir 10 Agents, aber nur einen Memory-Service. Das macht das System nicht nur ressourcenschonender, sondern auch viel einfacher zu überwachen und zu debuggen.

**Konsistenz durch Design.** Alle Agents nutzen automatisch dieselbe Memory-Kompression, dieselben Datenstrukturen und dieselbe Fehlerbehandlung. Keine Abweichungen mehr, keine unterschiedlichen Implementierungen. Was bei Agent A funktioniert, funktioniert garantiert auch bei Agent B und C.

**Wartung wird zum Traum.** Memory-Bug entdeckt? Ein Fix, fertig. Neues Memory-Feature entwickelt? Ein Deployment, alle Agents profitieren sofort. Performance-Tuning nötig? Ein Service optimieren statt zehn verschiedene Implementierungen durchzugehen. Das spart Zeit, Nerven und reduziert die Fehlerquote drastisch.

Weiter geht es mit unserer Implementierung. Kommen wir zu LLM-Integration. Ausnahmweise werde ich mal wieder posten, wie wir LM-Studio und unser Model ansprechen können ;)

## LLM-Integration für Memory Compression

Für die Memory Compression nutzen wir LM Studio - genau wie in den vorherigen Tagen:

```python
# LM Studio Integration
from openai import OpenAI

llm_client = OpenAI(
    base_url="http://localhost:1234/v1", 
    api_key="lm-studio"
)

def compress_with_llm(messages, agent_id, max_tokens, phases):
    prompt = f"""Erstelle eine präzise Zusammenfassung der folgenden Agent-Nachrichten:
    
AGENT: {agent_id}
NACHRICHTEN ({len(messages)} total): {messages}

AUFGABE: Fasse die wichtigsten Punkte in MAXIMAL {max_tokens} Wörtern zusammen."""
    
    response = llm_client.chat.completions.create(
        model="mistralai/ministral-3b", 
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens * 2,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()
```

Das LLM sorgt für intelligente Strukturierung, erkennt wichtige Details und formatiert die Ausgabe. Je nach Token-Limit passt es den Stil automatisch an, von kompakten Stichpunkten bis zu detaillierten Planungsskizzen. Das werden wir nachher im Beispiel auch beobachten. 

## Demo: Service in Aktion

Unser `day_12_microservice.py` zeigt den kompletten MCP-Workflow in der Praxis. Das Demo-Script durchläuft systematisch alle wichtigen Funktionen des Services.

Zuerst überprüft es die Service-Gesundheit mit einem Health Check, dann nutzt es die **MCP Tool Discovery** um automatisch herauszufinden, welche Tools verfügbar sind. Der Agent muss also nicht wissen, was der Service kann, er entdeckt es zur Laufzeit. Das haben wir uns weiter oben schon genauer angesehen.

Danach simuliert das Script einen Planungsablauf. Es speichert eine Serie von zusammenhängenden Nachrichten: Sicherheitsanalyse, Timing-Details, Ausrüstungslisten, Fluchtwege und Risikobewertungen. So entsteht eine echte Conversation History, wie sie bei der Zusammenarbeit mehrerer Agents entstehen würde.

```python
test_messages = [
    "Security analysis: Two guards at main entrance, one at back.",
    "Timing critical: Bank closes at 6 PM, security system activates at 6:15 PM.",
    "Equipment check: Need 3 lockpicks, 2 radios, 1 thermal scanner.",
    # ... weitere Planungs-Nachrichten
]
```

Der interessante Teil kommt bei der **hierarchischen Memory Compression** (aus Tag 11): Das Script testet verschiedene Token-Limits und `recent_count` Werte. Die letzten 2-3 Nachrichten bleiben vollständig erhalten, während ältere Nachrichten komprimiert werden. So geht keine aktuelle Information verloren, aber der Token-Verbrauch bleibt kontrolliert. Das kennen wir ja bereits. 

Im kleineren der beiden Tests führt das zum Beispiel zu diesem Ergebnis:

```bash
Hierarchical Compression Tests:

📚 30 tokens, recent_count=2:
📝 Compressed: Planung eines Raubüberfalls. Sicherheit: 2 Wachen vorne, 1 hinten. Zeitkritisch: Bank schließt um 18:00 Uhr, Alarm ab 18:15 Uhr. Benötigte Ausrüstung: 3 Lockpicks, 2
🔥 Recent (2):
  - Risk assessment: Police response time approximatel...
  - Contingency plan: If detected, abort via emergency...
💾 Total tokens: 43
```


## Zusammenfassung und Ausblick

Mit unserem MCP Memory Service haben wir einen wichtigen Schritt gemacht. Statt verteilter Agent-Memories haben wir jetzt eine zentrale, standardisierte Lösung. Das bringt uns echte Microservice-Architektur: Ein Service, eine Verantwortung, saubere API, horizontal skalierbar!

Das Fundament steht, aber für den Produktionseinsatz fehlen noch einige Features:

```python
# Nächste Schritte für Production:
- Authentication (API Keys, OAuth)
- Rate Limiting (nicht mehr als X Requests/Minute)  
- Metrics (Prometheus Integration)
- Structured Logging (JSON Logs)
- Circuit Breaker (Fallback bei Überlastung)
- Load Balancing (mehrere Service-Instanzen)
```

Der wichtigste Vorteil ist aber bereits da: **Standardisierung durch MCP**. Unser Service spricht die gleiche Sprache wie alle anderen MCP-Services. Das bedeutet, Agents können ihn automatisch entdecken und nutzen, ohne spezielle Integration.

Und das ist erst der Anfang. Mit MCP können wir ein ganzes Ökosystem von Services aufbauen: Memory, Search, Calculations, Data Processing - alle mit derselben standardisierten Schnittstelle. Der Agent entdeckt sie automatisch und kann sie sofort verwenden.

Das ist die Zukunft von LLM-Architekturen: Modulare, austauschbare Services, die zusammenarbeiten wie Lego-Bausteine!
