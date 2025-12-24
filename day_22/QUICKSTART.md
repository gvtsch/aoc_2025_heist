# Quick-Start Guide: Tag 22 – AI-Powered Mole Detection

**Voraussetzungen:**
- Python 3.9+
- Abhängigkeiten aus `requirements.txt` installiert (`pip install -r requirements.txt`)
- Tag 20 Interactive Dashboard (basis für Tag 22)

---

## 1. Dashboard-Server starten

```bash
./day_22/start_detection_dashboard.sh
```
- Startet das AI-Detection Dashboard auf [http://localhost:8010](http://localhost:8010)
- Alternativ direkt:
  ```bash
  python day_22/detection_dashboard_server.py
  ```

---

## 2. Heist mit Mole laufen lassen

Zuerst eine Session mit Daten erstellen (nutzt Tag 20's System):

```bash
# In separatem Terminal
python3 day_20/run_controlled_heist.py --demo
```

Dies erstellt eine Session mit:
- Random Mole Selection
- Sabotage Instructions für den Mole
- Agent-Konversation und Tool-Usage

---

## 3. AI-Detection nutzen

**Option A: Dashboard** (wenn HTML UI vorhanden)
- Im Browser öffnen: [http://localhost:8010](http://localhost:8010)
- Session auswählen
- AI Analysis starten

**Option B: API direkt**

```bash
# Vollständige AI-Analyse
curl -X POST http://localhost:8010/api/ai-detect/analyze \
  -H "Content-Type: application/json" \
  -d '{"session_id": "heist_001"}'

# Schnelle Suggestion
curl -X POST http://localhost:8010/api/ai-detect/suggest \
  -H "Content-Type: application/json" \
  -d '{"session_id": "heist_001"}'
```

---

## 4. AI-Detection Features
- **Tool Usage Analysis (25%)**: Verdächtige Tool-Nutzungsmuster
- **Timing Inconsistency (30%)**: Timing-Widersprüche und Verzögerungen
- **Message Anomaly (20%)**: Ungewöhnliche Nachrichtenmuster
- **Information Quality (25%)**: Vage vs. konkrete Informationen

Die AI kombiniert alle Signale zu einem Suspicion Score (0.0-1.0) pro Agent.

---

## 5. End-to-End-Test (optional)

```bash
python day_22/test_ai_detection_integration.py
```
- Testet den kompletten AI-Detection-Workflow automatisiert.
- Vergleicht AI-Suggestion mit echtem Mole.

---

## 6. API-Endpoints

**AI Detection (NEU in Tag 22):**
- `POST /api/ai-detect/analyze` – Vollständige RAG-Analyse mit Score-Breakdown
- `POST /api/ai-detect/suggest` – Schnelle Mole-Suggestion
- `GET /api/ai-detect/session/{id}` – Analyse für spezifische Session
- `GET /api/detection-info` – Info über Detection-System

**Tag 20 Base Endpoints (verfügbar):**
- `POST /api/heist/start` – Heist starten
- `POST /api/heist/{id}/pause` – Heist pausieren
- `POST /api/heist/{id}/resume` – Heist fortsetzen
- `POST /api/heist/{id}/command` – Command an Agent senden
- `GET /api/heist/{id}/mole-status` – Mole-Status abrufen
- `POST /api/heist/{id}/evaluate-detection` – Detection evaluieren

---

## 7. Vollständiges Workflow-Beispiel

```bash
# Terminal 1: Tag 22 Server starten
./day_22/start_detection_dashboard.sh

# Terminal 2: Heist mit Mole laufen lassen
python3 day_20/run_controlled_heist.py --demo

# Terminal 3: AI-Detection testen
python3 day_22/test_ai_detection_integration.py
```

---

**Fertig!**
- Tag 22 nutzt Tag 20's Infrastructure (HeistController, SessionAnalytics)
- Die AI analysiert automatisch Agent-Verhalten mit RAG-Ansatz
- Besser als Zufall (25%) – typisch 40-70% Accuracy!

Viel Spaß beim KI-gestützten Detektiv-Spielen! 🤖🔍
