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

Alle Dokumente zu diesem Beitrag sind in meinem [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_18) zu finden.

Tag 18 macht aus gesammelten Daten verwertbare Insights. Seit Tag 16 loggen wir jede Message, jeden Tool-Call und jede Agent-Interaktion in SQLite. Seit Tag 17 tracken wir dynamisch entdeckte Tools. Aber bisher haben wir die Daten nur gesammelt, nie analysiert. Also zumindest ich nicht... 😄 Das ändern wir heute.

## Das Problem

Wir haben jetzt Sessions in der Datenbank. Verschiedene Tool-Konfigurationen, verschiedene Agent-Setups und verschiedene Runs. Aber wie vergleichen wir sie? Welche Konfiguration funktioniert besser? Welcher Agent nutzt welche Tools am häufigsten? Wer interagiert mit wem?

Die Daten sind da. Wir brauchen nur die Werkzeuge um sie zu analysieren.

## Session Analytics

Die Lösung ist eine Analytics-Schicht über der SQLite-Datenbank. Eine API die Sessions vergleicht, Tool-Usage zusammenfasst und Agent-Interaktionen visualisiert.

### Was wir analysieren könnten

* **Session-Vergleich**: Verschiedene Runs nebeneinander legen. Welcher hatte mehr Turns? Welcher war erfolgreicher?
* **Tool Usage Patterns**: Welche Tools werden wie oft genutzt? Wie hoch ist die Success-Rate? Welcher Agent nutzt welches Tool?
* **Agent Activity**: Wie aktiv ist jeder Agent? Wer spricht am meisten? Wer am wenigsten?
* **Interaction Matrix**: Wer folgt wem in der Konversation? Welche Agent-Paare interagieren am häufigsten?
* **Success Metrics**: Completion-Rate über alle Sessions. Durchschnittliche Turns pro Session. Tool-Success-Rates.
* ...

Hast du noch eine Idee, welche Analyse oder Metrik sinnvoll sein kann? 

Kommen wir nun zur Implementierung.

## Session Analytics Klasse

Die `SessionAnalytics` Klasse kapselt alle Datenbankabfragen:

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

Jede Methode kapselt eine SQL-Query. Clean Separation of Concerns: Die Klasse kennt SQL, der Rest des Systems nicht.

Ich glaube ich habe nun schon häufiger Separation of Concerns genannt, ohne es genauer zu beschreiben. Daher ein kurzer Exkurs:
> **Separation of Concerns**
> Jede Komponente macht eine Sache (gut), nicht alles auf einmal. Tag 18 zum Beispiel:
> `analytics_api.py` -> HTTP-Endpunkte (Kommunikation)
> `session_analytics.py` -> Datenlogik (Berechnungen)
> `init_database.py` -> DB-Setup (Struktur)
> Jede Komponente hat seine Aufgabe und muss sich nur darum kümmern.

Kommen wir zu den nächsten Methoden, die auch je nur eine Aufgabe haben 😉

### Tool Statistics

Die Tool-Statistiken zeigen wie häufig welches Tool genutzt wird und wie erfolgreich:

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

Für jedes Tool in der gewählten Session bekommen wir eine Aussage zu:
- **total_calls**: Wie oft wurde es aufgerufen?
- **successful_calls**: Wie viele Calls waren erfolgreich?
- **success_rate**: Erfolgsquote (0.0 bis 1.0)

Wenn `session_id` None ist, aggregieren wir über alle Sessions. Das zeigt dann globale Patterns.

### Agent Interaction Matrix

Die Interaction Matrix zeigt wer mit wem spricht. Wir werden das mit einem Self-Join lösen. Ich kannte das noch nicht, daher schauen wir uns das mal etwas genauer an.

#### Warum brauchen wir einen Self-Join?

Zuerst unsere `messages` Tabelle:

| turn_id | agent_name | message |
|---------|------------|---------|
| 1 | Planner | "Let's plan" |
| 2 | Hacker | "I'll hack" |
| 3 | Planner | "Good idea" |
| 4 | Driver | "I'm ready" |

Wir wollen wissen "Wer folgt auf wen?", aber in jeder Zeile steht nur **ein** Agent. Um zu sehen dass **Hacker** auf **Planner** folgt, müssen wir **zwei Zeilen gleichzeitig** betrachten:
- Zeile 1 (Planner)
- Zeile 2 (Hacker)

SQL hat **keine "nächste Zeile" Funktion**. Das ist nicht besonders hilfreich, wenn man genau das wissen möchte 😉

Wenn SQL eine Zeile verarbeitet, kann es **nicht auf die nächste Zeile zugreifen**. Wir können nichts derartiges programmieren: 

```sql
SELECT
    agent_name,           -- Aktuelle Zeile
    NEXT_ROW.agent_name   -- ❌ Es gibt keine NEXT_ROW Funktion
FROM messages
```

Eine solche Funktion gibt schlecht nicht 🤷‍♂️.

**Ohne Join** sieht SQL nur eine Zeile gleichzeitig:

```
SQL verarbeitet Zeile 1:
turn_id | agent_name
--------|------------
1       | Planner    <- SQL ist hier und kann nicht auf Zeile 2 zugreifen
```

**Mit Join** bringen wir zwei Zeilen in eine kombinierte Zeile:

```
SQL verarbeitet kombinierte Zeile:
m1.turn_id | m1.agent_name | m2.turn_id | m2.agent_name
-----------|---------------|------------|---------------
1          | Planner       | 2          | Hacker         ✅ Beide in EINER Zeile!
```

Nun lesen wir die Tabelle **zweimal** - einmal für "aktueller Agent", einmal für "nächster Agent":

```sql
FROM messages m1      -- Erste Lesung: "Aktueller Sprecher"
JOIN messages m2      -- Zweite Lesung: "Nächster Sprecher"
ON m1.turn_id = m2.turn_id - 1  -- Verbinde Turn N mit Turn N+1
```

Im Detail und im implementierten Code sieht das dann so aus: 

```python
cursor.execute("""
    SELECT
        m1.agent_name as from_agent,    # Agent der spricht
        m2.agent_name as to_agent,      # Agent der als nächstes spricht
        COUNT(*) as interaction_count   # Wie oft passiert das?
    FROM messages m1                    # Erste Kopie der Tabelle
    JOIN messages m2 ON                 # Zweite Kopie verbinden mit:
        m1.session_id = m2.session_id   # Gleiche Session UND
        AND m1.turn_id = m2.turn_id - 1 # m1 ist genau 1 Turn VOR m2
    WHERE m1.session_id = ?             # Nur für diese Session
    GROUP BY m1.agent_name, m2.agent_name  # Gruppiere nach Agent-Paaren
    ORDER BY interaction_count DESC     # Häufigste zuerst
""", (session_id,))
```

Schritt für Schritt in meinen Worten: 
1. **FROM messages m1** - Nimm die messages Tabelle, nenne sie "m1"
2. **JOIN messages m2** - Nimm die gleiche Tabelle nochmal, nenne sie "m2"
3. **ON m1.turn_id = m2.turn_id - 1** - Verbinde wo turn_id von m1 genau 1 kleiner ist als m2
4. **GROUP BY m1.agent_name, m2.agent_name** - Zähle für jedes Agent-Paar
5. **COUNT(*)** - Wie oft kommt dieses Paar vor?

Und wozu das ganze? Die Interaction Matrix zeigt:

1. **Dominanz**: Wer initiiert Konversationen?
   - Wenn "Planner -> X" häufig ist, dominiert der Planner
2. **Bottlenecks**: Gibt es Agents die kaum antworten?
   - Wenn "X -> Communicator" selten ist, wird er ignoriert
3. **Collaboration Patterns**: Welche Agents arbeiten zusammen?
   - Hohe Counts zwischen zwei Agents = enge Zusammenarbeit
4. **Konversationsfluss**: Ist es zirkulär oder linear?
   - Linear: A -> B -> C -> Ende
   - Zirkulär: A -> B -> C -> A -> B -> C

Und so weiter... Zumindest ist das meine Vorstellung. Was ich damit mache, weiß ich noch nicht ganz genau. Manche Features in diesem Projekt existieren ja auch nur, um ein Konzept oder ein Tool zu erlernen 😄

### Session Comparison

Eine weitere wichtige Analytics-Funktion ist der Session-Vergleich. Damit können wir verschiedene Runs direkt nebeneinander legen und systematisch vergleichen:

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

Das gibt uns Sessions nebeneinander. Wir sehen sofort:
- Welche Session mehr Turns hatte
- Welche Tools in Session A genutzt wurden aber nicht in Session B
- Welche Agents in verschiedenen Sessions unterschiedlich aktiv waren

Das ist wertvoll für A/B-Testing. Wenn wir verschiedene Tool-Sets (aus Tag 17) testen, zeigt uns der Vergleich welches Setup besser performed.

### Success Metrics

Die letzte wichtige Analytics-Funktion aggregiert Metriken über alle Sessions hinweg:

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

Das gibt uns Kennzahlen auf System-Ebene:
- **Completion Rate**: Wie viele Sessions laufen bis zum Ende?
- **Durchschnittliche Turns**: Wie lang ist eine typische Session?
- **Tool Success Rates**: Welche Tools funktionieren zuverlässig?

Diese Metriken zeigen Trends über Zeit. Wenn wir das System verbessern, sollte die Completion Rate steigen.

Damit haben wir alle Analytics-Funktionen auf SQLite-Ebene implementiert:
- **Tool Statistics**: Welche Tools werden genutzt
- **Agent Interaction Matrix**: Wer spricht mit wem (Self-Join!)
- **Session Comparison**: Runs vergleichen
- **Success Metrics**: System-weite Kennzahlen

Jetzt machen wir sie über HTTP zugänglich.

## REST API

Und hier kommt die uns bereits bekannte FastAPI wieder zum tragen. Während ich das schreibe fällt mir auf, dass ich noch nicht aufgelöst habe, wie REST API und FastAPI zueinander stehen. Die Begriff werden recht häufig genutzt.

REST ist ein Architektur-Stil (wie man eine API designed), während FastAPI ein Python Framework ist (also die Implementierung). Oder anders: REST ist der Bauplan für ein Haus und FastAPI ist der Werkzeugkasten. In unserem Fall bauen wir eine REST API mit GET/POST/... und nutzen dafür das Framework FastAPI.

Damit machen wir die Daten über HTTP verfügbar, was uns viele Türen öffnet für Dashboards, CLI-tools oder andere Services, die die Session-Daten analysieren möchten. 

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

Die API läuft auf Port 8007. Alle Endpoints sind GET (read-only), was bedeutet, dass die Datenbank nicht modifiziert wird. Zur Anwendung folgt am Ende noch ein Quickstart-Guide :]

### Query-Parameter

Einige Endpoints akzeptieren optionale Parameter:

**Session-Filter:**

```bash
GET /api/tool-stats?session_id=heist_20251218_140000
```

Die obigen Zeilen filtern die Statistiken auf eine spezifische Session.

**Session-Vergleich:**

```bash
GET /api/compare?session_ids=heist_001&session_ids=heist_002&session_ids=heist_003
```

Diese Zeilen vergleichen mehrere Sessions. Der `session_ids` Parameter kann wiederholt werden. Damit haben wir alle Analytics-Endpoints abgedeckt.

## Praktische Anwendung: A/B-Testing

Die wahre Stärke der Analytics-API zeigt sich beim systematischen Experimentieren. Hier ein hypothetisches Beispiel, wie man verschiedene Tool-Konfigurationen vergleichen könnte:

**Szenario**: Du willst testen ob mehr Tools zu besseren Ergebnissen führen.

**Setup A**: Standard Tools (calculator, file_reader)
**Setup B**: Erweiterte Tools (calculator, file_reader, database_query, simulation_data)

Wir lassen jeweils fünf5 Sessions pro Setup laufen und fragst dann die API:

```bash
GET /api/compare?session_ids=setup_a_1&session_ids=setup_a_2&session_ids=setup_a_3&session_ids=setup_a_4&session_ids=setup_a_5&session_ids=setup_b_1&session_ids=setup_b_2&session_ids=setup_b_3&session_ids=setup_b_4&session_ids=setup_b_5
```

**Hypothetische Ergebnisse könnten zeigen:**
- Setup B hat durchschnittlich mehr Turns (Agents nutzen die Extra-Tools)
- Setup B hat höhere Completion Rate (mehr Tools = mehr Möglichkeiten)
- `database_query` wird am häufigsten vom Hacker genutzt
- Die Interaction Matrix zeigt: Mit mehr Tools reden Agents öfter miteinander

Das wäre echte datengetriebene Entscheidungsfindung - nicht nach Bauchgefühl, sondern basierend auf Metriken.

Solche systematischen Vergleiche sind besonders wertvoll beim Experimentieren mit Agent-Konfigurationen, Tool-Sets oder Prompting-Strategien. Statt zu raten "könnte Setup B besser sein?", hast du konkrete Zahlen: "Setup B hat 23% höhere Completion Rate bei durchschnittlich 12 mehr Turns."

## Integration mit bestehendem System

Ein wichtiger Aspekt von Tag 18 ist wie es sich ins Gesamtsystem einfügt... oder eben **nicht** einfügt. Die Analytics-API ist bewusst **völlig entkoppelt** vom Rest des Systems.

### Read-Only Architektur

Die Analytics-API hat nur **Lesezugriff** auf die Datenbank:

```python
# Alle Queries sind SELECT
cursor.execute("SELECT * FROM sessions WHERE ...")
cursor.execute("SELECT COUNT(*) FROM tool_usage WHERE ...")
```

Diese Beschränkung auf Read-Only hat drei wichtige Konsequenzen:

**Kein Risiko für laufende Sessions**

Da die API nur liest, kann sie nichts kaputt machen. Selbst wenn die Analytics-API crasht, abstürzt oder fehlerhafte Queries ausführt... die Datenbank bleibt unverändert. Das Heist-System kann währenddessen weiterlaufen und Sessions speichern, ohne dass die Analytics-API das stört.
Im Gegensatz dazu: Wenn ein Service mit Schreibzugriff abstürzt während er eine Transaction durchführt, könnte die Datenbank in einem inkonsistenten Zustand zurückbleiben. Bei Read-Only gibt es dieses Risiko nicht.

**Keine Side-Effects** 

Jeder API-Call verändert genau... nichts. Das hat einen wichtigen Vorteil: Du kannst Queries beliebig oft ausführen, ohne dir Sorgen zu machen.

```bash
# Diese Calls 100x hintereinander ausführen? Kein Problem!
curl http://localhost:8007/api/sessions
curl http://localhost:8007/api/sessions
curl http://localhost:8007/api/sessions
# ... immer das gleiche Ergebnis, keine ungewollten Änderungen
```

Im Gegensatz zu einer Write-API, wo jeder Call etwas ändert:
```bash
# ❌ VORSICHT bei Write-APIs:
POST /api/sessions/create  # Erzeugt Session A
POST /api/sessions/create  # Erzeugt Session B (nicht gewollt!)
POST /api/sessions/create  # Erzeugt Session C (auch nicht gewollt!)
```

**Vorhersagbar und reproduzierbar**

Derselbe Call liefert immer dasselbe Ergebnis (solange keine neuen Sessions hinzukommen). Wenn du heute `/api/sessions` aufrufst und 10 Sessions bekommst, und morgen nochmal aufrufst (ohne neue Sessions), bekommst du wieder exakt die gleichen 10 Sessions.
Das macht Debugging einfach: Du kannst einen API-Call, der ein unerwartetes Ergebnis liefert, beliebig oft wiederholen ohne dass sich das Ergebnis ändert. Das Verhalten ist deterministisch.
In der API-Entwicklung nennt man das **idempotent** (auch das habe ich neu gelernt, yay!), eine Eigenschaft die besonders bei GET-Requests wichtig ist. Die HTTP-Spezifikation sagt sogar: "GET requests MUST be safe and idempotent."

### Unabhängiger Lifecycle

Die Analytics-API hat einen komplett eigenständigen Lebenszyklus. Sie ist nicht an die Laufzeit des Heist-Systems gebunden und kann völlig unabhängig betrieben werden. Das zeigt sich in vier Aspekten:

**Parallel zum Heist-System**

Man kann beide Services gleichzeitig laufen lassen:
```bash
# Terminal 1: Heist-System
./day_16/start_services.sh

# Terminal 2: Analytics API
./day_18/start_analytics.sh

# Beide laufen unabhängig und teilen sich nur die Datenbank
```

**Jederzeit starten/stoppen**

Anders als das Heist-System, das während einer Session nicht unterbrochen werden sollte, kannst du die Analytics-API beliebig starten und stoppen:

```bash
./start_analytics.sh   # Starten
# Abfragen machen...
CTRL+C                 # Stoppen
# Heist-System läuft weiter, Analytics gestoppt
./start_analytics.sh   # Wieder starten - alles funktioniert
```

Das ist möglich weil die API stateless ist.

**Eigener Port, keine Konflikte**

Port 8007 ist dediziert für Analytics. Das Heist-System nutzt die folgenden Services:
- Port 1234 - LM Studio
- Port 8001 - OAuth Service
- Port 8005 - Memory Service
- Port 8006 - Discovery Server

Es gibt keine Überschneidungen. Man könnte sogar mehrere Analytics-API Instanzen auf verschiedenen Ports laufen lassen.

**Minimale Dependencies**

Die einzige Abhängigkeit ist SQLite, eine dateibasierte Datenbank ohne eigenen Server. Keine externe Datenbank, keine Message Queues und kein Redis Cache. Nur Python, FastAPI und SQLite.

Das macht das Deployment einfach. Man kopiert den `day_18/` Ordner samt `heist_audit.db` auf einen anderen Server, startet `./start_analytics.sh` und ist fertig. Keine komplexe Infrastruktur notwendig.

Man könnte die API sogar auf einem separaten Server laufen lassen, mit read-only Zugriff auf eine replizierte Datenbank. Oder sie nur bei Bedarf starten, wenn man Daten analysieren möchte.

### Separation of Concerns in Aktion

Die Analytics-Schicht kennt **nur** die Datenbank-Struktur:

```python
class SessionAnalytics:
    def __init__(self, db_path: str = "heist_audit.db"):
        self.db_path = db_path  # Das ist alles!
```

Sie weiß nichts von:
- ❌ Agents und deren Implementierung
- ❌ LLM-APIs oder Prompts
- ❌ OAuth-Authentifizierung
- ❌ Discovery Servern
- ❌ Memory Services

Sie kennt nur:
- ✅ Tabellen: `sessions`, `messages`, `tool_usage`
- ✅ Spalten: `session_id`, `tool_name`, `success_rate`
- ✅ SQL-Queries

Das ist Separation of Concerns. Wir könnten das gesamte Heist-System neu schreiben. Solange die Datenbank-Struktur gleich bleibt, funktioniert die Analytics-API weiter.

Diese Entkopplung bringt mehrere Vorteile:

* **Stabilität**: Analytics-API kann nicht abstürzen wenn das Heist-System Probleme hat
* **Performance**: Queries blockieren nicht das Hauptsystem
* **Wartbarkeit**: Änderungen an Analytics betreffen nicht das Heist-System
* **Wiederverwendbarkeit**: Die API könnte auch andere Sessions analysieren, nicht nur vom Heist-System

Das ist ein Pattern das sich in vielen Production-Systemen bewährt hat: **Operational Database** (für laufende Sessions) getrennt von **Analytics Database** (für Auswertungen).

## Demo

Nachdem wir die Architektur und Implementierung durchgegangen sind, schauen wir uns an wie die API tatsächlich läuft und was sie zurückgibt.

### Server starten

Die API wird mit einem einfachen Script gestartet:

```bash
cd day_18
./start_analytics.sh
```

Der Server startet auf Port 8007 und zeigt alle verfügbaren Endpoints:

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

### Beispiel: Success Metrics abrufen

Wir fragen die systemweiten Metriken ab:

```bash
curl http://localhost:8007/api/metrics | python3 -m json.tool
```

Die API antwortet mit einem strukturierten JSON-Objekt:

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

Und was bedeutet das?

* **100% Completion Rate** - Alle 3 Sessions wurden erfolgreich abgeschlossen
* **Durchschnittlich 45 Turns** - Eine typische Session dauert etwa 45 Interaktionen
* **Perfekte Tool Success Rates** - Alle Tools funktionieren zuverlässig (1.0 = 100%)
* **Gleichmäßige Tool-Nutzung** - Jedes Tool wurde genau 3x genutzt (einmal pro Session)

Solche Metriken geben einen schnellen Überblick über die System-Gesundheit. In einem Produktions-System würden wir nach Trends schauen. Steigt die Completion Rate? Welche Tools haben niedrige Success Rates und müssen verbessert werden? Usw...

### Beispiel: Sessions vergleichen

Noch ein praktisches Beispiel, zwei Sessions direkt vergleichen:

```bash
curl 'http://localhost:8007/api/compare?session_ids=demo_session_001&session_ids=demo_session_002' | python3 -m json.tool
```

Die Response zeigt einen Side-by-Side Vergleich:

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

Session 001 hatte 45 Turns, Session 002 nur 38, obwohl beide completed sind. Warum? Mit den Detail-Daten in `tool_comparison` und `agent_comparison` kannst du analysieren welche Tools unterschiedlich genutzt wurden.

Diese Art von Vergleich ist Gold wert beim Experimentieren mit verschiedenen Konfigurationen.

## Zusammenfassung

Tag 18 schließt eine wichtige Lücke. Wir sammeln seit Tag 16 Daten, aber haben sie bisher nie systematisch ausgewertet. Das ändert sich heute. Auch wenn das nur ein konstruiertes Problem bzw. Lösung ist, um Konzepte und Mehtoden zu erlernen 😃

### Was haben wir gebaut?

**Die Analytics-Schicht**

Wir haben eine komplette Analytics-Infrastruktur über der bestehenden SQLite-Datenbank gebaut:

* **SessionAnalytics Klasse** - Kapselt alle SQL-Queries und Aggregations-Logik
  * Tool Statistics: Welche Tools werden genutzt, wie erfolgreich sind sie?
  * Agent Interaction Matrix: Wer spricht mit wem? (mit Self-Join Deep-Dive)
  * Session Comparison: Runs direkt vergleichen
  * Success Metrics: System-weite Kennzahlen

* **REST API mit FastAPI** - Macht die Analytics über HTTP verfügbar
  * 7 GET-Endpoints für verschiedene Analysen
  * Read-only: Keine Side-Effects, sicher
  * Port 8007: Unabhängig vom Heist-System
  * Stateless: Kann jederzeit gestartet/gestoppt werden

### Warum ist das wichtig?

**Datengetriebene Entscheidungen**

Ohne Analytics arbeiten wir im Blindflug. Mit Tag 18 können wir objektiv messen und datengetriebene Entscheidungen treffen:
* Welche Tool-Konfiguration funktioniert besser?
* Welche Agents sind Bottlenecks?
* Steigt die Success-Rate über Zeit?

**A/B-Testing ermöglichen**

Der Session-Vergleich macht systematisches Experimentieren möglich. Du kannst verschiedene Setups testen und basierend auf echten Daten entscheiden, nicht nach Bauchgefühl.

**Separation of Concerns**

Die Analytics-API ist ein Paradebeispiel für saubere Architektur (schön, dass ich das selber behaupte 😅):
* Völlig entkoppelt vom Heist-System
* Kennt nur die Datenbank-Struktur
* Read-only: Kein Risiko für laufende Sessions
* Kann auf separatem Server laufen

### Was kommt als nächstes?

Mit Tag 18 haben wir die Grundlage für datenbasiertes Arbeiten gelegt. In den nächsten Tags könnten wir die folgenden Themen angehen:
* Visualisierung der Metrics (Grafana, Custom Dashboard)
* Alerting bei niedrigen Success Rates
* Trend-Analysen über Zeit
* Machine Learning auf den Session-Daten

Wir haben jetzt die Werkzeuge um zu verstehen was in unserem System passiert. Keine Vermutungen mehr, nur Daten.

---

## Verwendung

### Quick Start

```bash
# 1. Ins day_18 Verzeichnis wechseln
cd day_18

# 2. Analytics API starten
./start_analytics.sh

# In einem NEUEN Terminal:

# 3. Health Check
curl http://localhost:8007/health | python3 -m json.tool

# 4. Alle Sessions anzeigen
curl http://localhost:8007/api/sessions | python3 -m json.tool

# 5. Session-Details
curl http://localhost:8007/api/sessions/demo_session_003 | python3 -m json.tool

# 6. Tool-Statistiken
curl http://localhost:8007/api/tool-stats | python3 -m json.tool

# 7. Agent-Activity
curl http://localhost:8007/api/agent-activity | python3 -m json.tool

# 8. Sessions vergleichen
curl "http://localhost:8007/api/compare?session_ids=demo_session_001&session_ids=demo_session_002" | python3 -m json.tool

# 9. Success Metrics
curl http://localhost:8007/api/metrics | python3 -m json.tool

# Server stoppen: CTRL+C im Terminal wo der Server läuft
```

**Tipp:** Nutze `| python3 -m json.tool` am Ende jedes curl-Befehls für formatierte JSON-Ausgabe!

Die Database enthält bereits 3 Demo-Sessions (`demo_session_001`, `demo_session_002`, `demo_session_003`) die du sofort für Tests nutzen kannst - siehe die Beispiele im Kapitel "Die API in Aktion".
