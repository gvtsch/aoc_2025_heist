# End-to-End Testing Guide: Interactive Dashboard

Dieser Guide zeigt dir Schritt für Schritt, wie du das komplette Interactive Dashboard System testest. Von Server-Start bis zur funktionierenden Live-Kontrolle mit echten Agents.

## Schritt 1: Server starten

```bash
cd day_20
python3 interactive_dashboard_server.py
```

Der Output:

```
================================================================================
🎮 Interactive Heist Command Center
================================================================================
Starting server on http://0.0.0.0:8008
Dashboard: http://localhost:8008
...
```

## Schritt 2: Dashboard öffnen

Öffne http://localhost:8008 im Browser. Du siehst das "Cyberpunk"-Dashboard mit:
- System Overview (Sessions, Messages, Tools)
- Agent Activity Charts
- Neural Feed (Live Conversation)
- Heist Control Panel
- Mole Detection Game

## Schritt 3: API-Tests ausführen

```bash
python3 test_interactive_dashboard.py
```

Output:
```
✅ Health Check: Server is healthy: healthy
✅ List Sessions: Found 1 sessions
✅ Start Session: Session test_session_... started
✅ Get Session Status: Status: running
✅ Send Command: Command sent to hacker
✅ Get Pending Commands: Found 1 pending commands
✅ Pause Session: Session paused successfully
✅ Resume Session: Session resumed successfully
✅ Get Active Heists: Found 2 active heists
✅ Detect Mole: Marked safecracker as detected mole
✅ Get Mole Status: Detected: safecracker

Total Tests: 11
Passed: 11 ✅
Success Rate: 100.0%
```

Alle 11 Tests grün - Server funktioniert!

## Schritt 4: Live Control Demo

Terminal 1:
```bash
python3 run_controlled_heist.py
```

Terminal 2:
```bash
python3 demo_live_control_verbose.py
```

Terminal 2 zeigt:
```
[09:21:57] 📤 Sende Command an hacker: 'PRIORITY OVERRIDE: Focus on stealth approach'
[09:21:57] ✅ Command erfolgreich in Queue eingereiht
[09:21:58] 📊 Aktuell 5 Commands in Queue
```

Terminal 1 zeigt:
```
[hacker] Received command: PRIORITY OVERRIDE: Focus on stealth approach
```

Das ist der Beweis: Commands beeinflussen echte Agents in Echtzeit!

## Schritt 5: Mole Game testen

```bash
python3 test_mole_game_integration.py
```

Output:
```
[09:35:22] ✅ Session gestartet: mole_test_...
[09:35:22] 🎭 Mole wurde zufällig ausgewählt!
[09:35:22] ✅ planner als Verdächtiger markiert
[09:35:22] 😢 Wrong! planner is innocent. The real mole safecracker sabotaged the heist!
[09:35:22] 🎭 The mole was: safecracker
[09:35:22] Game Outcome: FAILURE
```

Das Spiel funktioniert:
- Mole wurde zufällig gewählt
- User hat einen Verdacht geäußert
- System hat evaluiert ob korrekt
- Outcome: FAILURE (falsch geraten)

## Was du gelernt hast

**Commands wirken wirklich:** Der Agent erhält das Command als `OVERRIDE INSTRUCTION` in seinen LLM-Context. Das ist keine Simulation - das ist echte Runtime-Intervention.

**Pause funktioniert:** Wenn du eine Session pausierst, blockt der Agent beim nächsten Turn-Check. Er gibt `[PAUSED] waiting for resume...` aus.

**Mole Game ist fair:** Der Mole wird wirklich zufällig gewählt. Jeder Run ist anders. Das macht es spannend.

## Quick-Start

Schnellstart für die Ungeduldigen:

```bash
# 1. Server starten
python3 day_20/interactive_dashboard_server.py

# 2. Dashboard öffnen
open http://localhost:8008

# 3. Tests laufen lassen
python3 day_20/test_interactive_dashboard.py

# 4. Mole Game testen
python3 day_20/test_mole_game_integration.py
```

Das war's! Dashboard läuft, Tests sind grün, Mole Game funktioniert.
