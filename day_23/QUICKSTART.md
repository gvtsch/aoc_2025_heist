# Tag 23: Quick Start Guide

**Heist System mit Docker in 5 Minuten starten**

## Prerequisites

- Docker Desktop installiert
- LM Studio installiert und laufend
- Min. 8GB RAM verfügbar

## 🚀 Start in 3 Schritten

### 1. LM Studio vorbereiten

```bash
# LM Studio öffnen
# → Modell laden: Gemma 2 9B (empfohlen) oder andere
# → Local Server starten (Port 1234)
```

### 2. Docker Services starten

```bash
# Im Projekt-Root
docker-compose up --build
```

**Was passiert:**
- 6 Microservices werden gebaut (dauert ~2-3 Min beim ersten Mal)
- Health Checks warten auf Service-Bereitschaft
- Dashboard startet zuletzt (abhängig von allen anderen)

### 3. Dashboard öffnen

```bash
open http://localhost:8008
```

**Oder manuell:** Browser → `http://localhost:8008`

## 🎮 Ersten Heist starten

1. **"Start New Heist"** Button klicken
2. Zuschauen wie 6 Agents den Bankraub planen
3. **AI Detection** beobachten - wer ist der Mole?
4. **Agent Badge** klicken um Verdacht zu markieren
5. **"Submit Detection"** → Ergebnis!

## 📊 Was du sehen solltest

**Conversation Feed:**
```
[planner] We need 45 minutes for vault access...
[TOOL:calculator:45*60] → 2700 seconds
[hacker] Reading security specs... [TOOL:file_reader:security_specs.txt]
[intel] Querying guard schedule... [TOOL:database_query:guard_schedule]
```

**Tool Statistics:**
```
Calculator: 15 calls, 100% success
File Reader: 8 calls, 87% success
Database Query: 5 calls, 100% success
```

**AI Analysis:**
```
🤖 Suggested Mole: driver
Confidence: 67.8%
- Tool Usage: 80% (suspiciously perfect)
- Timing: 53% (contradictions)
- Message Anomaly: 71% (hesitation)
```

## 🔧 Troubleshooting

### Problem: "Cannot connect to LM Studio"

**Lösung:**
```bash
# LM Studio Server läuft?
curl http://localhost:1234/v1/models

# Falls nicht:
# → LM Studio öffnen
# → "Local Server" Tab
# → "Start Server" Button
```

### Problem: "Tool error: 404"

**Lösung:**
```bash
# File-Reader Files prüfen
docker exec heist-file-reader ls -la /app/files/

# Sollte zeigen:
# bank_layout.txt
# security_specs.txt
# vault_specs.txt
```

### Problem: Container bleibt nicht healthy

**Lösung:**
```bash
# Logs prüfen
docker-compose logs calculator

# Container neu starten
docker-compose restart calculator
```

## 🛑 Stoppen & Cleanup

```bash
# Services stoppen (Daten bleiben)
docker-compose down

# Services + Datenbank löschen
docker-compose down -v

# Nur einen Service neu starten
docker-compose restart dashboard
```

## 📝 Logs & Debugging

```bash
# Alle Logs
docker-compose logs

# Nur Dashboard
docker-compose logs -f dashboard

# Datenbank prüfen
docker exec heist-dashboard sqlite3 /data/heist_analytics.db \
  "SELECT session_id, status, total_turns FROM sessions"
```

## 🎯 Nächste Schritte

- Mehrere Heists starten → Statistiken vergleichen
- Verschiedene Mole-Detection-Strategien testen
- AI Analysis Scores interpretieren lernen
- Mit Agent-Konfiguration experimentieren

## 💡 Tipps

**Schneller Development Cycle:**
```bash
# Nur Dashboard neu bauen (nach Code-Änderungen)
docker-compose build dashboard
docker-compose restart dashboard
```

**Clean Start:**
```bash
# Alles löschen, fresh start
docker-compose down -v
docker-compose up --build
```

**Background Mode:**
```bash
# Services im Hintergrund laufen lassen
docker-compose up -d

# Logs später ansehen
docker-compose logs -f
```

## 📚 Weitere Dokumentation

- **Vollständige Anleitung:** `day_23_docker_production.md`
- **Architecture:** Docker Compose File
- **Configuration:** `day_20/agents_config.docker.yaml`
- **AI Detection:** `day_22/sabotage_detector.py`

---

**Ready to catch the mole? Let's go! 🎯**
