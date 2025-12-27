---
title: "Tag 24: 24 Tage Lernen - Konzepte & Code-Beispiele"
date: 2025-12-24
tags:
  - python
  - aoc
  - adventofcode
  - zusammenfassung
  - learnings
  - referenz
toc: true
---

Alle Dokumente zu diesem Beitrag sind in meinem [Repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_24) zu finden.

## Was wir entwickelt haben

Nach 24 Tagen Entwicklung steht ein vollständiges Multi-Agent-System. Was als einfache Verbindung zu einem lokalen Sprachmodell begann, ist zu einer "produktionsreifen" Microservice-Architektur gewachsen. Natürlich immer vo dem Hintergrund, dass es komplett konstruiert ist und so etwas natürlich nicht in die Produktion gehen würden.

Das System simuliert ein Überfall(Heist)-Szenario, bei dem mehrere KI-Agenten zusammenarbeiten müssen. Jeder Agent hat eine spezialisierte Rolle. Planer, Hacker, Safecracker, Intel, Driver und Lookout. Die Agenten kommunizieren miteinander, nutzen verschiedene Tools und planen gemeinsam den Überfall. Der Clou: Einer der Agenten ist zufällig ein Saboteur, der das Team subtil sabotiert. So die Idee.

### Architektur

Das System besteht aus 6-7 unabhängigen Microservices:
* **OAuth Service** (Port 8001): Zentraler Authentifizierungsdienst mit JWT-Token-Verwaltung
* **Calculator Service** (Port 8002): Mathematische Berechnungen für den Safecracker
* **File Reader Service** (Port 8003): Zugriff auf Dokumente und Spezifikationen
* **Database Query Service** (Port 8004): Sicherheitsdatenbank für Intel-Recherche
* **Memory Service** (Port 8005): Kontext-Kompression und Langzeitgedächtnis
* **Dashboard** (Port 8008): Interaktive Web-Oberfläche mit Echtzeit-Analytics
* **Detection API** (Port 8010): KI-gestützte Sabotage-Erkennung

Alle Services sind über Docker containerisiert und kommunizieren über ein gemeinsames Netzwerk. OAuth schützt jeden Tool-Zugriff und Health Checks stellen sicher, dass die Services in der richtigen Reihenfolge starten.

### Kerntechnologien

* **Backend**: FastAPI als Web-Framework, Python 3.11 und SQLite für Persistenz. Jeder Service ist eine eigenständige FastAPI-Anwendung mit eigenen Endpoints und Verantwortlichkeiten.
* **Authentifizierung**: OAuth 2.0 Client Credentials Ablauf. Jeder Agent authentifiziert sich beim OAuth-Dienst und erhält einen zeitlich begrenzten JWT-Token. Werkzeuge prüfen Token-Gültigkeit und Scopes bevor sie Anfragen akzeptieren.
* **Frontend**: Einfaches HTML/CSS/JavaScript Dashboard mit Chart.js für Visualisierungen. WebSocket-Verbindung für Echtzeit-Updates der Agent-Aktivitäten. 100% vibecoded. 
* **LLM**: Lokale Sprachmodelle über LM-Studio. Kein Cloud-API-Zugriff, alles läuft lokal. Das ermöglicht Experimente ohne Kosten und Datenschutzbedenken.
* **Deployment**: Docker Compose orchestriert alle Services. Ein einziger Befehl `docker-compose up` startet das gesamte System.

### Besondere Features

* **Multi-Agent-Konversation**: Agenten sprechen in Runden miteinander. Jeder Agent sieht die letzten Nachrichten als Kontext und antwortet entsprechend seiner Persona. Die Konversation entwickelt sich organisch.
* **Memory Compression**: Alte Nachrichten werden automatisch zusammengefasst, neue bleiben detailliert. Das verhindert Token-Explosion bei langen Gesprächen. Ein LLM erstellt die Zusammenfassungen.
* **Tool Discovery**: Agenten fragen einen Erkennungs-Dienst welche Werkzeuge sie nutzen dürfen. Basierend auf ihren OAuth-Scopes bekommen sie gefilterte Werkzeug-Listen. Werkzeuge sind zur Laufzeit austauschbar.
* **Maulwurf-Spiel**: Ein zufälliger Agent wird zum Saboteur. Dieser bekommt geheime Instruktionen in seinem System-Prompt, für die anderen Agenten unsichtbar. Es gibt fünf verschiedene Sabotage-Strategien: Timing-Fehler, Falschinformationen, Koordinationschaos, subtile Verzögerungen, falsche Werkzeuge.
* **KI-Erkennung**: Hybrides System zur Saboteur-Erkennung. 60% regelbasierte Pattern-Analyse (Tool-Nutzung, Timing-Inkonsistenzen, Nachrichten-Anomalien, Informationsqualität) kombiniert mit 40% LLM-Reasoning. Das ist ein RAG-Ansatz: Retrieval der Patterns, Augmentation des Contexts, Generation der finalen Scores durch ein LLM.
* **Interaktives Dashboard**: Echtzeit-Überwachung aller Agent-Aktivitäten. Sessions können pausiert, fortgesetzt oder gestoppt werden. Commands können direkt an einzelne Agenten geschickt werden und überschreiben deren aktuelle Instruktionen. Charts zeigen Tool-Statistiken, Agent-Interaktionen und Session-Verläufe.
* **Session Analytics**: Detaillierte Auswertung jeder Session. SQL-Queries analysieren Tool-Erfolgsraten, Agent-Interaktionsmatrizen (wer hat mit wem gesprochen), Nachrichtenhäufigkeiten. Die Daten fließen in die Saboteur-Erkennung ein.

### Technische Highlights

Das System demonstriert mehrere moderne Patterns.

* **Microservices mit OAuth**: Jeder Service ist eigenständig deploybar. Zentraler OAuth-Service authentifiziert alle Clients. Keine Service-zu-Service-Kommunikation ohne Token. Scopes regeln granulare Berechtigungen.
* **Configuration-Driven**: Agenten werden aus YAML-Configs geladen, nicht hartcodiert. Das erlaubt A/B-Testing, verschiedene Umgebungen (dev/prod) und schnelles Experimentieren mit neuen Agent-Setups.
* **RAG für robuste KI**: Pure Regeln sind starr, pure LLMs halluzinieren. Die Kombination bringt das derzeit Beste aus beiden Welten. Regeln finden messbare Anomalien und das LLM versteht Kontext und Nuancen.
* **Health Checks in Docker**: Services starten nicht einfach nur, sie melden "ready". Docker wartet bis Health Checks erfolgreich sind bevor abhängige Services starten. Das verhindert Race Conditions.
* **WebSocket für Echtzeit**: Das Dashboard aktualisiert sich live. Keine Polling-Requests, echte Push-Updates. Sobald ein Agent eine Nachricht sendet, erscheint sie im Dashboard.

### Entwicklungsverlauf

Tag 1 startete mit der simplen Frage: Wie verbinde ich ein lokales LLM? Tag 24 endet mit einem produktionsreifen System aus 7 Services, OAuth-Security, KI-Detection, interaktivem Dashboard und Docker-Deployment.

Jeder Tag fügte ein Konzept hinzu. Persistence (SQLite), Web-APIs (FastAPI), Containerisierung (Docker), Multi-Agent-Koordination, Memory Management, Tool-Integration, Analytics, Visualisierung, Gamification, KI-Detection. Kleine inkrementelle Schritte, die sich zu einem komplexen System summieren.

Manche Konzepte mussten überarbeitet werden. Die erste Memory-Implementation speicherte alles, was zu einer Token-Explosion führte und mein Macbook an seine Limits brachte. Die erste Docker-Integration startete Services in falscher Reihenfolge und hatte Connection Errors zur Folge. Die erste Detection war nur regelbasiert und schlicht sehr ungenau. Iteration und Debugging gehören dazu.

Das Ergebnis ist ein System, das grundlegende Architektur-Prinzipien demonstriert. Nicht perfekt, aber ein funktionierendes Beispiel. 

### Was folgt

Diese Zusammenfassung dokumentiert alle 24 Tage. Jedes Konzept bekommt eine kurze Erklärung und ein minimales Code-Beispiel. Das Dokument dient als Referenz. Auch für mich für Wiederholung, zum Nachschlagen, als Lernpfad für ähnliche Projekte, ...

---

## Die Konzepte im Detail

## Tag 1: Lokales LLM verbinden

**Konzept**: Lokal gehostete Sprachmodelle statt Cloud-APIs nutzen.

**Kernidee**: LM-Studio und Ollama bieten OpenAI-kompatible APIs für lokale Modelle, ermöglichen Privatsphäre und kostenfreies Experimentieren.

**Code-Beispiel**:
```python
from openai import OpenAI

# Verbindung zu lokalem LLM
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="local-model",
    messages=[{"role": "user", "content": "Hallo!"}]
)

print(response.choices[0].message.content)
```

**Technologien**: LM-Studio, OpenAI Python Library, Gemma 3B

---

## Tag 2: Persona Patterns

**Konzept**: Rollen und Verhaltensweisen durch System Prompts zuweisen.

**Kernidee**: Unterschiedliche System Prompts erzeugen Agenten mit verschiedenen Persönlichkeiten, Expertise und Kommunikationsstilen.

**Code-Beispiel**:
```python
PERSONAS = {
    "planner": "Du bist ein strategischer Planer. Fokussiere auf Koordination und Timing.",
    "hacker": "Du bist ein Tech-Experte. Analysiere Sicherheitssysteme und Schwachstellen.",
    "safecracker": "Du bist ein Präzisionsspezialist. Fokussiere auf technische Details."
}

class Agent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.system_prompt = PERSONAS[role]

    def create_messages(self, user_input: str):
        # System-Prompt + User-Nachricht für LLM-Call
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

# Agent nutzen
planner = Agent("planner", "planner")
messages = planner.create_messages("Was ist unser Ansatz?")
response = client.chat.completions.create(model="local-model", messages=messages)
```

**Technologien**: Prompt Engineering, System-Level Instructions

---

## Tag 3: Conversation Memory

**Konzept**: Konversationshistorie für kontextbewusstes Verhalten pflegen.

**Kernidee**: Agenten erinnern sich an vorherige Nachrichten durch vollständige Konversationshistorie, aber diese wächst linear mit jedem Turn, mit jeder Runde.

**Code-Beispiel**:
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

class Agent:
    def __init__(self, name: str, persona: str):
        self.name = name
        self.history = [{"role": "system", "content": persona}]

    def chat(self, message: str) -> str:
        # User-Nachricht zur Historie hinzufügen
        self.history.append({"role": "user", "content": message})

        # Response mit vollständiger Historie abrufen
        response = client.chat.completions.create(
            model="local-model",
            messages=self.history
        )

        # Assistant-Response zur Historie hinzufügen
        reply = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})

        return reply

# Agent nutzen
agent = Agent("planner", "Du bist ein strategischer Planer.")
response1 = agent.chat("Plant einen Überfall")
response2 = agent.chat("Was war unser erstes Ziel?")  # Erinnert sich an Kontext
```

**Technologien**: In-Memory Lists, Token Counting, Context Management

---

## Tag 4: SQLite Persistenz

**Konzept**: Agent-Konversationen in einer Datenbank speichern.

**Kernidee**: SQLite bietet leichtgewichtigen, dateibasierten Speicher für Konversationshistorie, Analytics und Audit Trails.

**Code-Beispiel**:
```python
import sqlite3
from datetime import datetime

def init_database():
    conn = sqlite3.connect("heist.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    return conn

def save_message(conn, session_id: str, agent: str, message: str):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, agent_name, message) VALUES (?, ?, ?)",
        (session_id, agent, message)
    )
    conn.commit()
```

**Technologien**: SQLite3, SQL, Transactions, Timestamps

---

## Tag 5: FastAPI REST API

**Konzept**: Agent-Funktionalität über HTTP-Endpoints verfügbar machen.

**Kernidee**: FastAPI bietet modernes, schnelles Web-API-Framework mit automatischer OpenAPI-Dokumentation.

**Code-Beispiel**:
```python
from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Agent API")

# Datenbank-Verbindung
conn = sqlite3.connect("heist.db")

class ChatRequest(BaseModel):
    agent: str
    message: str
    session_id: str

@app.post("/chat")
async def chat(request: ChatRequest):
    # Agent abrufen und Nachricht verarbeiten
    agent = agents[request.agent]  # Annahme: agents ist ein Dict mit Agent-Instanzen
    response = agent.chat(request.message)

    # In Datenbank speichern
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, agent_name, message) VALUES (?, ?, ?)",
        (request.session_id, request.agent, request.message)
    )
    cursor.execute(
        "INSERT INTO messages (session_id, agent_name, message) VALUES (?, ?, ?)",
        (request.session_id, request.agent, response)
    )
    conn.commit()

    return {"response": response}

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT agent_name, message, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp",
        (session_id,)
    )
    messages = cursor.fetchall()
    return {"messages": messages}

# Starten mit: uvicorn main:app --reload
```

**Technologien**: FastAPI, Pydantic, Uvicorn, REST Design, HTTP Methods

---

## Tag 6: Docker Containerisierung

**Konzept**: Anwendungen in portablen Containern verpacken.

**Kernidee**: Docker stellt konsistente Umgebungen über Entwicklung und Produktion sicher.

**Code-Beispiel**:
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  agent-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - LM_STUDIO_URL=http://host.docker.internal:1234/v1
```

**Technologien**: Docker, Dockerfile, docker-compose, Volumes, Networking

---

## Tag 7: Multi-Agent Konversation

**Konzept**: Mehrere Agenten kommunizieren in Runden.

**Kernidee**: Orchestrator managt rundenbasierte Konversation zwischen Agenten mit verschiedenen Rollen.

**Code-Beispiel**:
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

PERSONAS = {
    "planner": "Du bist ein strategischer Planer. Fokussiere auf Koordination.",
    "hacker": "Du bist ein Tech-Experte. Analysiere Sicherheitssysteme.",
    "safecracker": "Du bist ein Präzisionsspezialist. Fokussiere auf Details."
}

class Agent:
    def __init__(self, name: str, persona: str):
        self.name = name
        self.persona = persona

    def chat_with_context(self, recent_context: list, initial_prompt: str) -> str:
        # Context-Nachrichten formatieren
        context_text = "\n".join([
            f"{msg['agent']}: {msg['message']}" for msg in recent_context
        ])

        prompt = f"{initial_prompt}\n\nBisheriger Context:\n{context_text}"

        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": self.persona},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

class MultiAgentOrchestrator:
    def __init__(self, agents: list):
        self.agents = agents
        self.shared_context = []

    def run_turn(self, initial_prompt: str):
        for agent in self.agents:
            # Letzten 5 Nachrichten als Context Window
            recent_context = self.shared_context[-5:]

            # Agent antwortet auf aktuellen Context
            response = agent.chat_with_context(recent_context, initial_prompt)

            # Zum gemeinsamen Context hinzufügen
            self.shared_context.append({
                "agent": agent.name,
                "message": response,
                "turn": len(self.shared_context)
            })

        return self.shared_context

# Verwendung
orchestrator = MultiAgentOrchestrator([
    Agent("planner", PERSONAS["planner"]),
    Agent("hacker", PERSONAS["hacker"]),
    Agent("safecracker", PERSONAS["safecracker"])
])

orchestrator.run_turn("Plant den Heist")
```

**Technologien**: Multi-threading, Context Windowing, Orchestration

---

## Tag 8: OAuth 2.0 Token Service

**Konzept**: Zentraler Authentifizierungsservice für Microservices.

**Kernidee**: OAuth 2.0 Client Credentials Ablauf mit JWT Tokens für Service-zu-Service-Authentifizierung.

**Code-Beispiel**:
```python
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import jwt

app = FastAPI(title="OAuth Service")

SECRET_KEY = "your-secret-key"
CLIENTS = {
    "agent_client": {"secret": "agent_secret", "scopes": ["read", "write"]}
}

@app.post("/token")
async def get_token(client_id: str, client_secret: str):
    # Credentials verifizieren
    if client_id not in CLIENTS or CLIENTS[client_id]["secret"] != client_secret:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # JWT Token erstellen
    payload = {
        "client_id": client_id,
        "scopes": CLIENTS[client_id]["scopes"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600
    }
```

**Technologien**: OAuth 2.0, JWT, HS256 Signatur, Token Expiration

---

## Tag 9: Protected APIs

**Konzept**: API-Endpoints mit Token-Verifizierung sichern.

**Kernidee**: Middleware validiert JWT Tokens und erzwingt scope-basierte Berechtigungen.

**Code-Beispiel**:
```python
from fastapi import Depends, HTTPException, Header
import jwt

def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_scope(required_scope: str):
    def scope_checker(token_data: dict = Depends(verify_token)):
        if required_scope not in token_data.get("scopes", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token_data
    return scope_checker

# Geschützter Endpoint
@app.get("/protected-data")
async def get_data(token_data: dict = Depends(require_scope("read"))):
    return {"data": "sensitive information"}
```

**Technologien**: JWT Validation, Dependency Injection, Bearer Token, Scope Enforcement

---

## Tag 10: Information Curation

**Konzept**: Selektive Informationsweitergabe zwischen Agenten.

**Kernidee**: Manche Agenten haben exklusiven Zugriff auf Daten und kuratieren, was sie mit dem Team teilen.

**Code-Beispiel**:
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

class HackerAgent:
    def __init__(self):
        self.bank_data = self.load_exclusive_data()

    def load_exclusive_data(self):
        # Lädt Daten die nur dieser Agent sieht
        with open("vault_data/bank_security.json") as f:
            import json
            return json.load(f)

    def curate_information(self, team_question: str) -> str:
        # LLM entscheidet was geteilt wird
        prompt = f"""
        Du hast Zugriff auf Bankdaten: {self.bank_data}

        Team fragt: {team_question}

        Gib nur relevante Informationen ohne sie zu überfordern.
        Teile nur was für die aktuelle Frage wichtig ist.
        """

        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

# Verwendung
hacker = HackerAgent()
team_answer = hacker.curate_information("Wie viele Wachen patrouillieren?")
print(team_answer)  # Nur gefilterte Info, nicht alle Daten
```

**Technologien**: LLM-basierte Zusammenfassung, Information Filtering, Data Aggregation

---

## Tag 11: Memory Compression

**Konzept**: Context-Größe durch hierarchische Kompression managen.

**Kernidee**: Alte Nachrichten werden zu Zusammenfassungen komprimiert, neue bleiben detailliert.

**Code-Beispiel**:
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

class CompressedMemory:
    def __init__(self, compression_threshold: int = 10):
        self.recent_messages = []
        self.compressed_summary = ""
        self.threshold = compression_threshold

    def add_message(self, message: str):
        self.recent_messages.append(message)

        # Komprimieren wenn Schwellwert erreicht
        if len(self.recent_messages) > self.threshold:
            self._compress_old_messages()

    def _compress_old_messages(self):
        # Älteste Hälfte der Nachrichten nehmen
        to_compress = self.recent_messages[:len(self.recent_messages)//2]

        # LLM erstellt Zusammenfassung
        prompt = f"""
        Vorherige Zusammenfassung: {self.compressed_summary}

        Neue Nachrichten zum Komprimieren:
        {chr(10).join(to_compress)}

        Erstelle eine prägnante Zusammenfassung der Kernpunkte.
        """

        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}]
        )

        self.compressed_summary = response.choices[0].message.content
        self.recent_messages = self.recent_messages[len(to_compress):]

    def get_context(self) -> str:
        return f"Zusammenfassung: {self.compressed_summary}\n\nAktuell:\n" + \
               "\n".join(self.recent_messages)

# Verwendung
memory = CompressedMemory(compression_threshold=10)

# Viele Nachrichten hinzufügen
for i in range(15):
    memory.add_message(f"Agent {i%3}: Nachricht {i}")

# Context ist komprimiert: alte Messages als Summary, neue im Detail
context = memory.get_context()
print(context)
```

**Technologien**: Hierarchical Memory, LLM Summarization, Token Budgeting

---

## Tag 12: MCP Microservice

**Konzept**: Model Context Protocol standardisierte Tool-Services.

**Kernidee**: MCP definiert Standard-Interfaces für LLM-Tools, ermöglicht Discoverability und Interoperabilität.

**Code-Beispiel**:
```python
from fastapi import FastAPI
import sqlite3

app = FastAPI(title="Memory Service")

# Datenbank-Setup
conn = sqlite3.connect("memory.db")
conn.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, text TEXT)")
conn.commit()

@app.get("/tools")
async def list_tools():
    """Tool Discovery Endpoint - listet verfügbare Tools"""
    return {
        "tools": [
            {
                "name": "store_memory",
                "description": "Informationen im Speicher ablegen",
                "parameters": {"text": "string"}
            },
            {
                "name": "retrieve_memory",
                "description": "Gespeicherte Erinnerungen abrufen",
                "parameters": {"query": "string"}
            }
        ]
    }

@app.post("/tools/store_memory")
async def store_memory(text: str):
    # In Datenbank speichern
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memories (text) VALUES (?)", (text,))
    conn.commit()
    return {"status": "stored", "text": text}

@app.post("/tools/retrieve_memory")
async def retrieve_memory(query: str):
    # Datenbank durchsuchen (einfache Textsuche)
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM memories WHERE text LIKE ?", (f"%{query}%",))
    results = [row[0] for row in cursor.fetchall()]
    return {"results": results}

# Starten mit: uvicorn memory_service:app --port 8005
```

**Technologien**: MCP Protocol, Tool Discovery, RESTful Design, Service Standardization

---

## Tag 13: Agent Tools mit OAuth

**Konzept**: Spezialisierte Tools geschützt durch OAuth Scopes.

**Kernidee**: Verschiedene Agenten haben Zugriff auf unterschiedliche Tools basierend auf ihren OAuth Scopes.

**Code-Beispiel**:
```python
from fastapi import Depends

# Tool Registry
TOOLS = {
    "calculator": {
        "required_scope": "math",
        "description": "Berechnungen durchführen"
    },
    "file_reader": {
        "required_scope": "files",
        "description": "Tresorspezifikationen lesen"
    },
    "database_query": {
        "required_scope": "database",
        "description": "Sicherheitsdatenbank abfragen"
    }
}

@app.post("/tools/calculator")
async def calculator(
    expression: str,
    token_data: dict = Depends(require_scope("math"))
):
    result = eval(expression)  # Hinweis: safe eval in Production nutzen!

    # Tool-Nutzung loggen
    log_tool_usage(token_data["client_id"], "calculator", expression, result)

    return {"result": result}

@app.post("/tools/file_reader")
async def file_reader(
    filename: str,
    token_data: dict = Depends(require_scope("files"))
):
    with open(f"vault_data/{filename}") as f:
        content = f.read()

    return {"content": content}
```

**Technologien**: OAuth Scopes, Tool Decorators, Dependency Injection, Audit Trails

---

## Tag 15: Dynamisches Agent-System

**Konzept**: Konfigurationsgesteuerte Agent-Instanziierung.

**Kernidee**: Agenten werden in YAML Config definiert statt hartcodiert, ermöglicht einfache Modifikationen.

**Code-Beispiel**:
```yaml
# agents_config.yaml
agents:
  - name: planner
    role: Strategischer Koordinator
    prompt: Du bist ein strategischer Planer fokussiert auf Koordination.
    tools:
      - memory
      - discovery
    scopes:
      - read
      - write

  - name: hacker
    role: Sicherheitsexperte
    prompt: Du bist ein Tech-Experte der Sicherheitssysteme analysiert.
    tools:
      - file_reader
      - database_query
    scopes:
      - read
      - files
      - database
```

```python
import yaml
from dataclasses import dataclass
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

@dataclass
class AgentConfig:
    name: str
    role: str
    prompt: str
    tools: list
    scopes: list

def load_agents_config(config_path: str) -> list[AgentConfig]:
    with open(config_path) as f:
        config = yaml.safe_load(f)

    return [
        AgentConfig(**agent_data)
        for agent_data in config["agents"]
    ]

class ConfigurableAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.history = [{"role": "system", "content": config.prompt}]

    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        response = client.chat.completions.create(
            model="local-model",
            messages=self.history
        )
        reply = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})
        return reply

# Agenten dynamisch erstellen
configs = load_agents_config("agents_config.yaml")
agents = {cfg.name: ConfigurableAgent(cfg) for cfg in configs}

# Agent nutzen
planner_response = agents["planner"].chat("Plant den Heist")
```

**Technologien**: YAML, Dataclasses, Dynamic Instantiation, Configuration Management

---

## Tag 16: Service Integration

**Konzept**: Orchestrierung mehrerer Microservices.

**Kernidee**: IntegratedAgent koordiniert OAuth, Memory, Tools und Database Services mit Health Checks.

**Code-Beispiel**:
```python
import httpx

class IntegratedAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.services = {
            "oauth": "http://localhost:8001",
            "memory": "http://localhost:8003",
            "tools": "http://localhost:8002"
        }
        self.token = None

    async def ensure_authenticated(self):
        """OAuth Token abrufen falls nötig"""
        if not self.token:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.services['oauth']}/token",
                    data={
                        "client_id": self.config.name,
                        "client_secret": "secret"
                    }
                )
                self.token = response.json()["access_token"]

    async def call_tool(self, tool_name: str, params: dict):
        """Geschütztes Tool mit OAuth Token aufrufen"""
        await self.ensure_authenticated()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.services['tools']}/tools/{tool_name}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            return response.json()

    async def check_services_health(self):
        """Verifizieren dass alle Services laufen"""
        async with httpx.AsyncClient() as client:
            for name, url in self.services.items():
                try:
                    await client.get(f"{url}/health")
                except httpx.RequestError:
                    raise Exception(f"Service {name} ist nicht verfügbar")
```

**Technologien**: Service Orchestration, Health Checks, Async HTTP, Session Management

---

## Tag 17: Tool Discovery Protocol

**Konzept**: Runtime Tool Discovery statt statischer Konfiguration.

**Kernidee**: Agenten fragen Discovery Server welche Tools verfügbar sind, gefiltert nach ihren OAuth Scopes.

**Code-Beispiel**:
```python
from fastapi import FastAPI, Depends

app = FastAPI(title="Tool Discovery")

# Tool Registry mit Scope-Anforderungen
TOOL_REGISTRY = {
    "calculator": {"scopes": ["math"], "endpoint": "http://localhost:8002"},
    "file_reader": {"scopes": ["files"], "endpoint": "http://localhost:8003"},
    "database_query": {"scopes": ["database"], "endpoint": "http://localhost:8004"}
}

@app.get("/discover")
async def discover_tools(token_data: dict = Depends(verify_token)):
    """Tools zurückgeben die für dieses Token verfügbar sind"""
    user_scopes = set(token_data.get("scopes", []))

    available_tools = {}
    for tool_name, tool_info in TOOL_REGISTRY.items():
        required_scopes = set(tool_info["scopes"])

        # Prüfen ob User die benötigten Scopes hat
        if required_scopes.issubset(user_scopes):
            available_tools[tool_name] = {
                "endpoint": tool_info["endpoint"],
                "scopes": tool_info["scopes"]
            }

    return {"tools": available_tools}

# Agent-Nutzung
async def discover_my_tools(agent_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8006/discover",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        return response.json()["tools"]
```

**Technologien**: Service Discovery, Scope Filtering, Dynamic Tool Loading, Metadata

---

## Tag 18: Session Analytics

**Konzept**: Datengetriebene Einsichten in Agent-Verhalten.

**Kernidee**: Fortgeschrittene SQL Queries extrahieren Patterns, Statistiken und Metriken aus Session-Daten.

**Code-Beispiel**:
```python
import sqlite3

class SessionAnalytics:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def get_tool_statistics(self, session_id: str):
        """Tool-Nutzungszahlen und Erfolgsraten"""
        query = """
            SELECT
                tool_name,
                COUNT(*) as total_uses,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                ROUND(AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate
            FROM tool_usage
            WHERE session_id = ?
            GROUP BY tool_name
            ORDER BY total_uses DESC
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (session_id,))
        return cursor.fetchall()

    def get_agent_interaction_matrix(self, session_id: str):
        """Wer hat auf wen geantwortet (Self-Join)"""
        query = """
            SELECT
                m1.agent_name as from_agent,
                m2.agent_name as to_agent,
                COUNT(*) as interactions
            FROM messages m1
            JOIN messages m2 ON m1.session_id = m2.session_id
                AND m1.turn + 1 = m2.turn
            WHERE m1.session_id = ?
            GROUP BY m1.agent_name, m2.agent_name
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (session_id,))
        return cursor.fetchall()

    def compare_sessions(self, session_ids: list):
        """Metriken über Sessions vergleichen"""
        query = """
            SELECT
                session_id,
                COUNT(DISTINCT agent_name) as num_agents,
                COUNT(*) as num_messages,
                MAX(turn) as total_turns
            FROM messages
            WHERE session_id IN ({})
            GROUP BY session_id
        """.format(','.join('?' * len(session_ids)))

        cursor = self.conn.cursor()
        cursor.execute(query, session_ids)
        return cursor.fetchall()

# Verwendung
analytics = SessionAnalytics("heist_analytics.db")

# Tool-Statistiken für eine Session
tool_stats = analytics.get_tool_statistics("game_001")
for tool_name, total, successful, success_rate in tool_stats:
    print(f"{tool_name}: {successful}/{total} ({success_rate}%)")

# Agent-Interaktions-Matrix
interactions = analytics.get_agent_interaction_matrix("game_001")
for from_agent, to_agent, count in interactions:
    print(f"{from_agent} → {to_agent}: {count} Interaktionen")
```

**Technologien**: Advanced SQL, Self-Joins, Aggregation, Data Analysis, FastAPI Endpoints

---

## Tag 19: Dashboard Visualisierung

**Konzept**: Echtzeit-visuelle Darstellung von Agent-Aktivitäten.

**Kernidee**: Web-Dashboard mit Chart.js zeigt Session-Daten, Agent-Aktivität und Tool-Statistiken.

**Code-Beispiel**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Heist Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <canvas id="activityChart"></canvas>

    <script>
        // Session-Daten abrufen
        fetch('/api/analytics/session/game_001')
            .then(r => r.json())
            .then(data => {
                // Activity Chart erstellen
                const ctx = document.getElementById('activityChart');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.turns,
                        datasets: data.agents.map(agent => ({
                            label: agent.name,
                            data: agent.activity_per_turn,
                            borderColor: agent.color
                        }))
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            });

        // WebSocket für Echtzeit-Updates
        const ws = new WebSocket('ws://localhost:8008/ws');
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            updateDashboard(update);
        };
    </script>
</body>
</html>
```

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        # Updates senden wenn neue Nachrichten ankommen
        data = await get_latest_activity()
        await websocket.send_json(data)
        await asyncio.sleep(1)
```

**Technologien**: HTML/CSS/JavaScript, Chart.js, WebSocket, Real-Time Updates

---

## Tag 20: Interaktives Dashboard

**Konzept**: Bidirektionale Kontrolle laufender Sessions.

**Kernidee**: HeistController managt Session-State (RUNNING/PAUSED/COMPLETED) mit Pause/Resume/Command Injection.

**Code-Beispiel**:
```python
from fastapi import FastAPI
from enum import Enum
from datetime import datetime

app = FastAPI(title="Heist Controller")

class SessionState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

class HeistController:
    def __init__(self):
        self.sessions = {}

    def create_session(self, session_id: str):
        self.sessions[session_id] = {
            "state": SessionState.RUNNING,
            "command_queue": [],
            "activity_log": []
        }

    def pause_session(self, session_id: str):
        self.sessions[session_id]["state"] = SessionState.PAUSED
        self.log_event(session_id, "Session pausiert")

    def resume_session(self, session_id: str):
        self.sessions[session_id]["state"] = SessionState.RUNNING
        self.log_event(session_id, "Session fortgesetzt")

    def inject_command(self, session_id: str, agent: str, command: str):
        """Agent-Instruktionen während laufender Session überschreiben"""
        self.sessions[session_id]["command_queue"].append({
            "agent": agent,
            "command": command,
            "timestamp": datetime.now()
        })
        self.log_event(session_id, f"Command injected für {agent}")

    def get_next_command(self, session_id: str, agent: str):
        """Agent prüft auf Override-Commands"""
        queue = self.sessions[session_id]["command_queue"]
        for cmd in queue:
            if cmd["agent"] == agent:
                queue.remove(cmd)
                return cmd["command"]
        return None

    def log_event(self, session_id: str, event: str):
        self.sessions[session_id]["activity_log"].append({
            "event": event,
            "timestamp": datetime.now().isoformat()
        })

# Globaler Controller
controller = HeistController()

# API Endpoints
@app.post("/session/{session_id}/create")
async def create(session_id: str):
    controller.create_session(session_id)
    return {"status": "created", "session_id": session_id}

@app.post("/session/{session_id}/pause")
async def pause(session_id: str):
    controller.pause_session(session_id)
    return {"status": "paused"}

@app.post("/session/{session_id}/resume")
async def resume(session_id: str):
    controller.resume_session(session_id)
    return {"status": "resumed"}

@app.post("/session/{session_id}/command")
async def send_command(session_id: str, agent: str, command: str):
    controller.inject_command(session_id, agent, command)
    return {"status": "command queued"}
```

**Technologien**: State Management, Command Queues, Event Logging, Real-Time Control

---

## Tag 21: Mole Game

**Konzept**: Gamification mit zufälligen Sabotage-Patterns.

**Kernidee**: Ein zufälliger Agent wird zum "Mole" mit geheimen Sabotage-Instruktionen im System Prompt.

**Code-Beispiel**:
```python
import random

SABOTAGE_PATTERNS = {
    "TIMING_ERRORS": """
        Gib absichtlich falsche Zeitangaben und widersprich dir später.
        Beispiel: Erst "5 Minuten", dann "eigentlich 20 Minuten".
    """,
    "FALSE_INFO": """
        Verbreite subtile Falschinformationen über Wachen und Sicherheit.
        Mache plausibel klingende Fehler.
    """,
    "COORDINATION_CHAOS": """
        Gib verwirrende und widersprüchliche Koordinationsanweisungen.
        Ändere häufig deine Meinung.
    """,
    "SUBTLE_DELAYS": """
        Zögere, stelle unnötige Fragen, verlangsame die Planung.
        Nutze Phrasen wie "hmm", "lass mich nachdenken", "warte".
    """,
    "WRONG_TOOLS": """
        Schlage Tools vor die nicht zum Job passen.
        Gib falsche technische Details.
    """
}

class MoleGame:
    def __init__(self, agents: list):
        self.agents = agents
        self.mole = None
        self.pattern = None

    def start_game(self):
        # Zufällige Mole-Auswahl
        self.mole = random.choice(self.agents)
        self.pattern = random.choice(list(SABOTAGE_PATTERNS.keys()))

        # Sabotage-Instruktionen injizieren
        sabotage_prompt = SABOTAGE_PATTERNS[self.pattern]
        self.mole.add_secret_instruction(sabotage_prompt)

        return {
            "mole": self.mole.name,  # Versteckt vor Spielern
            "pattern": self.pattern
        }

    def evaluate_guess(self, guessed_agent: str):
        if guessed_agent == self.mole.name:
            return {"result": "SUCCESS", "actual_mole": self.mole.name}
        else:
            return {"result": "FAILURE", "actual_mole": self.mole.name}

# Agent mit geheimen Instruktionen
class MoleAgent:
    def add_secret_instruction(self, instruction: str):
        # Vor System Prompt einfügen
        self.system_prompt = instruction + "\n\n" + self.system_prompt
```

**Technologien**: Randomization, Game State, Secret Instructions, Outcome Evaluation

---

## Tag 22: KI-gestützte Sabotage-Erkennung

**Konzept**: Hybrides regelbasiertes + LLM Erkennungssystem mit RAG-Pattern.

**Kernidee**: 60% regelbasierte Pattern-Erkennung + 40% LLM-Reasoning = robuste Mole-Erkennung.

**Code-Beispiel**:
```python
from collections import defaultdict
from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

class SabotageDetector:
    def __init__(self):
        self.weights = {
            "tool_usage_anomaly": 0.25,
            "timing_inconsistency": 0.30,
            "message_anomaly": 0.20,
            "information_quality": 0.25
        }
        self.rule_weight = 0.6
        self.llm_weight = 0.4

    def analyze_session(self, session_id: str, messages: list,
                       tool_usage: list, agents: list):
        # SCHRITT 1: RETRIEVAL - Regelbasierte Pattern-Erkennung
        rule_scores = self._get_rule_based_scores(messages, tool_usage, agents)

        # SCHRITT 2: AUGMENTATION - Strukturierten Context aufbauen
        context = self._build_rag_context(messages, tool_usage, agents, rule_scores)

        # SCHRITT 3: GENERATION - LLM-Analyse mit Context
        llm_scores = self._get_llm_scores(messages, context, agents)

        # Scores kombinieren: 60% Regeln + 40% LLM
        combined_scores = {}
        for agent in agents:
            combined_scores[agent] = (
                rule_scores[agent] * self.rule_weight +
                llm_scores[agent] * self.llm_weight
            )

        return combined_scores

    def _get_rule_based_scores(self, messages, tool_usage, agents):
        # Tool-Nutzungs-Patterns analysieren
        tool_scores = self._analyze_tool_usage(tool_usage, agents)

        # Timing-Keywords analysieren
        timing_scores = self._analyze_timing_patterns(messages, agents)

        # Nachrichten-Anomalien analysieren
        message_scores = self._analyze_message_anomalies(messages, agents)

        # Informationsqualität analysieren
        info_scores = self._analyze_information_quality(messages, agents)

        # Mit Gewichtungen kombinieren
        suspicion_scores = {}
        for agent in agents:
            suspicion_scores[agent] = (
                tool_scores[agent] * self.weights["tool_usage_anomaly"] +
                timing_scores[agent] * self.weights["timing_inconsistency"] +
                message_scores[agent] * self.weights["message_anomaly"] +
                info_scores[agent] * self.weights["information_quality"]
            )

        return suspicion_scores

    def _analyze_timing_patterns(self, messages, agents):
        timing_keywords = ["minute", "stunde", "zeit", "warte", "verzögerung"]
        contradiction_keywords = ["eigentlich", "warte", "falsch", "ändere", "vergiss"]

        timing_counts = defaultdict(int)
        contradiction_counts = defaultdict(int)

        for msg in messages:
            text = msg["message"].lower()
            agent = msg["agent_name"]

            for kw in timing_keywords:
                if kw in text:
                    timing_counts[agent] += 1

            for kw in contradiction_keywords:
                if kw in text:
                    contradiction_counts[agent] += 1

        # Normalisieren und kombinieren
        max_timing = max(timing_counts.values()) if timing_counts else 1
        max_contradictions = max(contradiction_counts.values()) if contradiction_counts else 1

        scores = {}
        for agent in agents:
            timing_ratio = timing_counts[agent] / max_timing
            contradiction_ratio = contradiction_counts[agent] / max_contradictions
            scores[agent] = (timing_ratio + contradiction_ratio) / 2

        return scores

    def _build_rag_context(self, messages, tool_usage, agents, rule_scores):
        """Strukturierten Context für LLM aufbauen"""
        context_parts = []

        # Top Verdächtige aus Regeln
        sorted_suspects = sorted(rule_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        context_parts.append("TOP VERDÄCHTIGE (Regelbasiert):")
        for agent, score in sorted_suspects:
            context_parts.append(f"  - {agent}: {score:.2%} Verdacht")

        # Tool-Fehler
        tool_failures = defaultdict(int)
        for usage in tool_usage:
            if not usage.get("success", True):
                tool_failures[usage["agent"]] += 1

        if tool_failures:
            context_parts.append("\nTOOL-FEHLER:")
            for agent, failures in tool_failures.items():
                context_parts.append(f"  - {agent}: {failures} Fehler")

        return "\n".join(context_parts)

    def _get_llm_scores(self, messages, context, agents):
        """LLM-Analyse mit abgerufenem Context"""
        conversation_text = "\n".join([
            f"{msg['agent_name']}: {msg['message']}"
            for msg in messages[:50]
        ])

        prompt = f"""Du bist ein Detektiv der eine Heist-Mission analysiert.

GEFUNDENE VERDÄCHTIGE PATTERNS:
{context}

AGENT-KONVERSATION:
{conversation_text}

Analysiere die Konversation unter Verwendung der Patterns oben.
Schätze Sabotage-Wahrscheinlichkeit (0.0-1.0) für jeden Agent.

Antworte NUR mit JSON: {{"agent": score, ...}}
"""

        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": "Du bist ein Detektiv. Antworte nur mit gültigem JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        llm_output = response.choices[0].message.content.strip()
        llm_scores = json.loads(llm_output)

        # Scores normalisieren
        return {
            agent: max(0.0, min(1.0, float(llm_scores.get(agent, 0.0))))
            for agent in agents
        }
```

**Technologien**: Pattern Recognition, Keyword Analysis, LLM Reasoning, RAG Pattern, Weighted Scoring

---

## Tag 23: Docker Production Setup

**Konzept**: Produktionsreife Multi-Container-Orchestrierung.

**Kernidee**: Docker Compose verwaltet 6-7 Services mit Health Checks, Volumes und Networking.

**Code-Beispiel**:
```yaml
# docker-compose.yml
version: '3.8'

services:
  oauth:
    build:
      context: .
      dockerfile: day_08/Dockerfile
    container_name: heist-oauth
    ports:
      - "8001:8001"
    networks:
      - heist-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  calculator:
    build:
      context: .
      dockerfile: day_13/Dockerfile.calculator
    container_name: heist-calculator
    ports:
      - "8002:8002"
    networks:
      - heist-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  dashboard:
    build:
      context: .
      dockerfile: day_22/Dockerfile
    container_name: heist-dashboard
    ports:
      - "8008:8008"
    environment:
      - DATABASE_PATH=/data/heist_analytics.db
      - LM_STUDIO_URL=http://host.docker.internal:1234/v1
    volumes:
      - heist-data:/data
    depends_on:
      oauth:
        condition: service_healthy
      calculator:
        condition: service_healthy
    networks:
      - heist-network

volumes:
  heist-data:
    driver: local

networks:
  heist-network:
    driver: bridge
```

```dockerfile
# Service Dockerfile Beispiel
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service.py .

ENV PYTHONUNBUFFERED=1
EXPOSE 8002

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

CMD ["python", "service.py"]
```

**Technologien**: Docker Compose, Health Checks, Volumes, Networks, Environment Variables, Service Dependencies

## Gelernte Architektur-Patterns

Über die 24 Tage hinweg haben sich wiederkehrende Architektur-Muster herauskristallisiert. Diese Patterns sind nicht spezifisch für dieses Heist-System, sondern übertragbar auf viele Software-Projekte. Hier sind die fünf wichtigsten Patterns, die sich meiner Meinung nach als besonders wertvoll erwiesen haben:

### 1. Microservices-Architektur
- Single Responsibility pro Service
- Service-to-Service-Kommunikation über REST
- Zentralisierte Authentifizierung (OAuth)
- Health Checks und Monitoring

### 2. Event-Driven Design
- WebSocket für Echtzeit-Updates
- Activity Logging und Audit Trails
- State Management mit Events

### 3. Configuration Over Code
- YAML-gesteuerte Agent-Definitionen
- Umgebungsbasierte Konfiguration
- Feature Flags und A/B Testing

### 4. RAG Pattern (Retrieval-Augmented Generation)
- Regelbasiertes Retrieval von Fakten
- Context Augmentation für LLM
- LLM Generation mit fundierten Daten
- Hybrides Scoring für Robustheit

### 5. OAuth 2.0 Sicherheitsmodell
- Client Credentials Ablauf für Dienste
- Scope-basierte Berechtigungen
- JWT Tokens mit Ablaufzeit
- Zentralisierte Token-Validierung

## Technologie-Stack Zusammenfassung

| Ebene | Technologien |
|-------|-------------|
| **LLM** | LM-Studio, Ollama, Lokale Modelle (Gemma, Llama) |
| **Backend** | FastAPI, Uvicorn, Python 3.11+ |
| **Datenbank** | SQLite3, SQL |
| **Auth** | OAuth 2.0, JWT, HS256 |
| **Frontend** | HTML/CSS/JavaScript, Chart.js |
| **Echtzeit** | WebSocket |
| **Containerisierung** | Docker, Docker Compose |
| **Protokoll** | MCP (Model Context Protocol) |
| **Datenformat** | JSON, YAML, Pydantic Models |

## Zusammenfassung

Tag Eins war eine simple LLM-Verbindung mit 20 Zeilen Code. Tag 24 ist ein System mit sieben Microservices, OAuth, AI-Detection und Docker-Deployment. Dieser Unterschied entstand nicht durch perfekte Planung, sondern durch inkrementelles Wachstum. Jeden Tag ein Konzept, kleine Schritte die sich summieren. Manche Konzepte waren geplant, andere entstanden aus Problemen heraus. Tag Elf's Memory Compression zum Beispiel war ungeplant, aber nach Tag Zehn explodierten die Token-Counts und ich musste reagieren. Diese Flexibilität war der Schlüssel zum Erfolg. 

Die wichtigsten Erkenntnisse lassen sich so zusammenfassen. **Configuration schlägt Hardcoding.** Spätestens beim dritten Agent wurde klar, dass YAML-Configs (Tag 14) alles flexibler machen. **Sicherheit ist fundamental.** OAuth und JWT fühlten sich anfangs wie Overkill an, wurden aber die Grundlage für Tool Discovery, Analytics und AI Detection. **Daten treiben alles Fortgeschrittene.** SQLite ermöglichte Analytics, Pattern-Detection und aussagekräftige Dashboards. **Hybride Ansätze vereinen Stärken.** Reine Regeln sind zu starr, reine LLMs halluzinieren. Die Lösung liegt in der Kombination von z.B. 60% Regeln für messbare Anomalien und 40% LLM für Kontext und Nuancen. **Developer Experience ist Produktivität.** Docker Compose verwandelte den täglichen manuellen Start von sechs Services in `docker-compose up`. Die gewonnene Zeit fließt in Features. **Echtzeit transformiert UX.** WebSocket statt Polling macht den Unterschied zwischen träge und lebendig spürbar. Diese Patterns sind nicht spezifisch für dieses Projekt, sondern übertragbar auf viele LLM-basierte Systeme.

24 Tage, 24 Konzepte, ein vollständiges System. Von einer simplen LLM-Verbindung zu einer produktionsreifen Multi-Agent-Architektur. Das Ergebnis ist nicht perfekt, aber es funktioniert, es lehrt und es demonstriert wie moderne LLM-Systeme gebaut werden könnten.

## Code-Referenzen

Alle Codes und Dokumentation verfügbar unter: [github.com/gvtsch/aoc_2025_heist](https://github.com/gvtsch/aoc_2025_heist)

Individuelle Tag-Implementierungen in jeweiligen `day_XX/` Verzeichnissen.
