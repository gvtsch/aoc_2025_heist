# 📊 Tag 18: Session Analytics API

Complete Analytics API für Multi-Agent Heist Sessions - **Standalone Version**.

## 🎯 Was ist das?

Ein FastAPI Server der Session-Daten aus einer SQLite Database analysiert und über RESTful Endpoints bereitstellt.

## 📁 Dateien in diesem Ordner

```
day_18/
├── README.md                    # Diese Datei
├── init_database.py             # Database Setup Script
├── analytics_api.py             # FastAPI Server
├── session_analytics.py         # Analytics Logic
├── start_analytics.sh           # Start Script
├── stop_analytics_api.sh        # Stop Script
└── heist_audit.db              # SQLite Database (nach Init)
```

**Alle benötigten Dateien sind in diesem Ordner!** ✅

## 🚀 Quick Start

### 1. Database initialisieren

```bash
cd day_18
python3 init_database.py
```

**Output:**
```
✅ Database initialized successfully!
   Sessions: 3
   Tool calls: 135
   Messages: 6
   Tool usage summaries: 15
```

### 2. Server starten

```bash
./start_analytics.sh
```

**Output:**
```
================================================================================
Starting Day 18: Analytics API Server
================================================================================

📊 Endpoints available:
   GET  http://localhost:8007/health
   GET  http://localhost:8007/api/sessions
   GET  http://localhost:8007/api/sessions/{id}
   ...

INFO:     Uvicorn running on http://0.0.0.0:8007
```

### 3. Testen

```bash
# Health Check
curl http://localhost:8007/health

# Sessions Liste
curl http://localhost:8007/api/sessions

# API Docs im Browser
open http://localhost:8007/docs
```

### 4. Stoppen

```bash
# CTRL+C im Terminal
# Oder:
./stop_analytics_api.sh
```

## 📊 API Endpoints

| Endpoint | Beschreibung | Status |
|----------|--------------|--------|
| `GET /health` | Health Check | ✅ |
| `GET /api/sessions` | Liste aller Sessions | ✅ |
| `GET /api/sessions/{id}` | Session Details | ✅ |
| `GET /api/tool-stats` | Tool Usage Statistics | ✅ |
| `GET /api/agent-activity` | Agent Activity Patterns | ✅ |
| `GET /api/compare` | Session Vergleich | ✅ |
| `GET /api/timeline/{id}` | Session Timeline | ✅ |
| `GET /api/metrics` | Performance Metrics | ✅ |

## 🗄️ Database Schema

Die `heist_audit.db` enthält:

### Tables

1. **sessions** - Session Metadata
   - session_id, start_time, end_time, total_turns, status, success

2. **agents** - Agent Definitions
   - id, session_id, agent_name, role

3. **actions** - Turn-by-turn Actions
   - id, session_id, turn_number, agent_name, action_type, timestamp

4. **tool_calls** - Tool Usage Details
   - id, session_id, agent_name, tool_name, timestamp, success, execution_time

5. **messages** - Agent Communication
   - id, session_id, turn_id, agent_name, agent_role, message, timestamp

6. **tool_usage** - Tool Usage Summaries
   - id, session_id, tool_name, operation, usage_count, avg_execution_time, success_rate

7. **games** - Mole Game Data
   - game_id, session_id, mole_agent, sabotage_pattern, detected

## 🧪 Testing

### Test 1: Health Check
```bash
curl http://localhost:8007/health | python3 -m json.tool
```

**Expected:**
```json
{
    "status": "healthy",
    "database": "connected",
    "total_sessions": 3
}
```

### Test 2: Sessions Liste
```bash
curl http://localhost:8007/api/sessions | python3 -m json.tool
```

**Expected:**
```json
{
    "total": 3,
    "sessions": [
        {
            "session_id": "demo_session_001",
            "start_time": 1734000000.0,
            "end_time": 1734003600.0,
            "total_turns": 45,
            "status": "completed"
        },
        ...
    ]
}
```

### Test 3: Session Details
```bash
curl http://localhost:8007/api/sessions/demo_session_001 | python3 -m json.tool
```

**Expected:** Session mit Messages und Tool Usage

### Test 4: Tool Statistics
```bash
curl http://localhost:8007/api/tool-stats | python3 -m json.tool
```

**Expected:** Tool Usage Statistics über alle Sessions

## 📝 Demo Daten

Die Database enthält 3 Demo Sessions:

| Session | Turns | Status | Agents |
|---------|-------|--------|--------|
| demo_session_001 | 45 | completed | Communicator, Planner, Executor |
| demo_session_002 | 38 | completed | Scout, Hacker, Driver |
| demo_session_003 | 52 | completed | Agent1, Agent2, Agent3 |

**Insgesamt:**
- 3 Sessions
- 135 Tool Calls
- 6 Messages
- 15 Tool Usage Summaries

## 🔧 Configuration

### Database Path

Default: `./heist_audit.db` (im day_18 Ordner)

Ändern via Environment Variable:
```bash
export DATABASE_PATH="/custom/path/heist_audit.db"
./start_analytics.sh
```

### Server Port

Default: 8007

Ändern in `analytics_api.py`:
```python
uvicorn.run(app, host='0.0.0.0', port=8007)  # Change port here
```

## 🛠️ Development

### Dependencies

```bash
pip install fastapi uvicorn sqlite3
```

### Database neu initialisieren

```bash
rm heist_audit.db
python3 init_database.py
```

### Server im Debug Mode

```bash
# In analytics_api.py ändern:
uvicorn.run(app, host='0.0.0.0', port=8007, reload=True)
```

## 📚 Dokumentation

### Interaktive API Docs

Wenn Server läuft:
- **Swagger UI**: http://localhost:8007/docs
- **ReDoc**: http://localhost:8007/redoc

### Code Struktur

**analytics_api.py** - FastAPI Server
- Definiert alle Endpoints
- Nutzt SessionAnalytics für Logic

**session_analytics.py** - Analytics Logic
- SessionAnalytics Klasse
- Database Queries
- Data Processing

**init_database.py** - Database Setup
- Erstellt alle Tables
- Fügt Demo Daten ein
- Kann mehrfach ausgeführt werden (CREATE IF NOT EXISTS)

## 🐛 Troubleshooting

### Problem: Port 8007 bereits belegt

```bash
# Port freigeben
lsof -ti:8007 | xargs kill -9

# Server neu starten
./start_analytics.sh
```

### Problem: Database nicht gefunden

```bash
# Prüfen ob Database existiert
ls -la heist_audit.db

# Falls nicht: initialisieren
python3 init_database.py
```

### Problem: Import Fehler

```bash
# Sicherstellen dass du im day_18 Ordner bist
cd day_18
pwd  # Sollte .../aoc_2025_heist/day_18 sein

# Python Path prüfen
python3 -c "import sys; print(sys.path)"
```

### Problem: 500 Internal Server Error

```bash
# Server Logs prüfen (im Terminal wo Server läuft)
# Oder:
curl http://localhost:8007/health  # Zeigt DB Status
```

## ✅ Checkliste: Tag 18 funktioniert

- [ ] `python3 init_database.py` erstellt heist_audit.db
- [ ] `./start_analytics.sh` startet Server ohne Fehler
- [ ] `curl http://localhost:8007/health` gibt "healthy" zurück
- [ ] `curl http://localhost:8007/api/sessions` zeigt 3 Sessions
- [ ] `open http://localhost:8007/docs` zeigt API Docs
- [ ] Alle Tests bestehen (siehe Testing Sektion)

## 🎯 Nächste Schritte

Nach Tag 18:

- **Tag 19**: Dashboard Visualization (Frontend)
- **Tag 20**: Interactive Dashboard Controls
- **Tag 21**: Mole Game Engine
- **Tag 22**: AI-powered Detection
- **Tag 23**: Production Deployment

## 📄 License

Teil des Advent of Code 2025 - Multi-Agent Heist Project

---

**Status**: ✅ Vollständig getestet und funktionsfähig

**Version**: 1.0 (Standalone)

**Port**: 8007

**Database**: heist_audit.db (lokal in day_18/)
