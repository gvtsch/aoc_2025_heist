# Day 15: Service Management

## Übersicht

Das Dynamic Agent System benötigt mehrere Microservices:

- **OAuth Service** (Port 8001) - Token-Verwaltung für Agents
- **Calculator Service** (Port 8002) - Berechnungen für Safecracker
- **File Reader Service** (Port 8003) - Dokumente für Hacker
- **Database Service** (Port 8004) - Guard-Schedules für Mole
- **LLM Service** (Port 1234) - LM Studio (manuell starten)

## Quick Start

### 1. Services starten

```bash
./day_15/start_services.sh
```

Das Skript startet automatisch alle 4 Services im Hintergrund.

### 2. Agent System ausführen

```bash
python day_15/dynamic_agent_system.py
```

### 3. Services stoppen

```bash
./day_15/stop_services.sh
```

## Manuelle Verwaltung

### Einzelne Services starten

```bash
# OAuth Service
python day_15/oauth_service.py

# Calculator
python day_15/tool_services.py calculator

# File Reader
python day_15/tool_services.py file_reader

# Database
python day_15/tool_services.py database
```

### Service Status prüfen

```bash
# Alle Services prüfen
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

## Logs

Service-Logs werden in `/tmp/` gespeichert:

```bash
tail -f /tmp/oauth_service.log
tail -f /tmp/calculator_service.log
tail -f /tmp/file_reader_service.log
tail -f /tmp/database_service.log
```

## Troubleshooting

### Port bereits belegt

```bash
# Port-Status prüfen
lsof -i :8001
lsof -i :8002
lsof -i :8003
lsof -i :8004

# Prozess beenden
kill -9 <PID>
```

### Services neu starten

```bash
./day_15/stop_services.sh
./day_15/start_services.sh
```

## Architektur

```
Dynamic Agent System
├── OAuth Service (8001)    → Token-Verwaltung
├── Calculator (8002)       → Tool für Safecracker
├── File Reader (8003)      → Tool für Hacker
├── Database (8004)         → Tool für Mole
└── LLM Studio (1234)       → Gemma Model
```

Alle Services werden vom `DynamicAgentSystem` automatisch über die `agents_config.yaml` konfiguriert und aufgerufen.
