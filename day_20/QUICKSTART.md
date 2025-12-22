# Quick-Start Guide: Tag 20 – Interactive Dashboard

**Voraussetzungen:**
- Python 3.9+
- Abhängigkeiten aus `requirements.txt` installiert (`pip install -r requirements.txt`)

---

## 1. Heist-Session starten

```bash
python day_20/run_controlled_heist.py --turns 15
```
- Startet eine neue Heist-Session mit mehreren Agents.
- Die Session wird in der Datenbank gespeichert.

---

## 2. Dashboard-Server starten

```bash
./day_20/start_interactive_dashboard.sh
```
- Startet das Dashboard auf [http://localhost:8008](http://localhost:8008)
- Alternativ direkt:
  ```bash
  python day_20/interactive_dashboard_server.py
  ```

---

## 3. Dashboard nutzen
- Im Browser öffnen: [http://localhost:8008](http://localhost:8008)
- Session auswählen (Dropdown)
- Konversation live verfolgen
- Heist pausieren/fortsetzen (Pause/Resume)
- Commands an Agents senden (Command-Input)
- Agenten-Aktivität und Status in Echtzeit beobachten

---

## 4. End-to-End-Test (optional)

```bash
python day_20/test_interactive_dashboard.py
```
- Testet alle API- und Dashboard-Funktionen automatisiert.

---

## 5. Logs & Ergebnisse
- Markdown-Logs im `day_20/`-Ordner (z.B. `conversation_log_*.md`)
- Statistiken & Outcomes im Dashboard und per API abrufbar

---

**Fertig!**
- Das Dashboard ist jetzt dein Command Center für Multi-Agent Heists.
- Pausiere, steuere, beobachte – alles in Echtzeit.

Viel Spaß beim Kontrollieren! 🚨
