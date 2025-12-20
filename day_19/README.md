# Day 19: Dashboard Visualization

Web-based dashboard for visualizing multi-agent heist sessions in real-time.

**Note:** Day 19 is completely **standalone** with its own config files:
- [config.yaml](config.yaml) - Dashboard server configuration
- [agents_config.yaml](agents_config.yaml) - Agent and database configuration

Day 19 does not modify Day 15-17. It uses Day 17's system as a library but maintains its own configuration.

## Quick Start

### 1. Initialize Database

Day 19 uses its own analytics database (`heist_analytics.db`):

```bash
cd day_19
python3 init_database.py
```

This creates `heist_analytics.db` in the day_19 directory.

### 2. Generate Session Data

Run the integrated system to create sessions:

```bash
# Start services first (see QUICKSTART.md in root)
./day_16/start_services.sh
./day_17/start_discovery_server.sh

# Option A: Use the day_19 wrapper script (recommended)
./day_19/run_heist.sh

# Option B: With custom config
./day_19/run_heist.sh --config my_config.yaml --turns 10

# Option C: Use Python directly (uses day_19/agents_config.yaml)
python3 day_19/run_heist.py --turns 5

# Option D: Original Day 17 method (still works)
python3 day_17/integrated_system_with_discovery.py
```

### 3. Start Dashboard

```bash
./day_19/start_dashboard.sh
```

### 4. Open Browser

Navigate to: http://localhost:8007

## CLI Usage

### Dashboard Server

Start with default config:
```bash
python3 day_19/dashboard_server.py
```

Start with custom config:
```bash
python3 day_19/dashboard_server.py --config my_dashboard_config.yaml
```

### Heist Session Runner

Run with default settings:
```bash
./day_19/run_heist.sh
```

Run with custom config:
```bash
./day_19/run_heist.sh --config my_agents_config.yaml
```

Run with more turns:
```bash
./day_19/run_heist.sh --turns 20
```

Run with verbose output:
```bash
./day_19/run_heist.sh --turns 10 --verbose
```

Get help:
```bash
./day_19/run_heist.sh --help
```

Python direct usage:
```bash
# Uses local day_19/agents_config.yaml by default
python3 day_19/run_heist.py --turns 5 --verbose

# Or specify a different config
python3 day_19/run_heist.py --config /path/to/my_config.yaml --turns 5
```

## Configuration

All dashboard settings are in [config.yaml](config.yaml):

### Database Path

```yaml
database:
  path: "heist_analytics.db"  # Local analytics database (Day 18/19 format)
```

### Server Settings

```yaml
server:
  host: "0.0.0.0"
  port: 8007
  title: "Heist Analytics Dashboard"
  reload: false  # Set to true for development
```

### Chart Colors

Customize agent colors:

```yaml
charts:
  agent_colors:
    planner: "#2196F3"      # Blue
    hacker: "#4CAF50"       # Green
    safecracker: "#FF9800"  # Orange
    mole: "#F44336"         # Red
```

## Features

### 📊 System Overview
- Total sessions count
- Completion rate
- Average turns per session
- Tool success rates

### 📈 Agent Activity Chart
- Bar chart showing message count per agent
- Color-coded by agent type
- Interactive tooltips

### 🛠️ Tool Usage Chart
- Total calls vs successful calls per tool
- Success rate visualization
- Grouped by tool and operation

### 💬 Live Conversation Feed
- Scrollable message timeline
- Agent role indicators
- Turn numbers
- Message truncation for long messages

### 🔍 Session Selector
- Dropdown to switch between sessions
- Shows session ID and turn count
- Auto-loads most recent session

### 🌐 WebSocket Real-Time Updates
- Live updates during active heists
- Connection status indicator
- Auto-reconnect on disconnect

### 🕵️ Mole Detection (Interactive)
- Click agents to mark as suspect
- Visual feedback
- Broadcasts to all connected clients

## API Endpoints

The dashboard server provides REST API endpoints:

### Health Check
```bash
curl http://localhost:8007/health
```

### List Sessions
```bash
curl http://localhost:8007/api/sessions
```

### Session Details
```bash
curl http://localhost:8007/api/session/{session_id}
```

### Tool Statistics
```bash
curl http://localhost:8007/api/tool-stats
```

### Agent Activity
```bash
curl http://localhost:8007/api/agent-activity/{session_id}
```

### Summary Statistics
```bash
curl http://localhost:8007/api/stats/summary
```

### Latest Session
```bash
curl http://localhost:8007/api/latest-session
```

### Search Messages
```bash
curl "http://localhost:8007/api/search?keyword=vault&session_id=heist_001"
```

For full API documentation, visit http://localhost:8007/docs

## WebSocket

Connect to WebSocket for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8007/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
};
```

## Files

| File | Description |
|------|-------------|
| [config.yaml](config.yaml) | Dashboard configuration |
| [dashboard_server.py](dashboard_server.py) | FastAPI backend |
| [dashboard.html](dashboard.html) | Frontend with Chart.js |
| [start_dashboard.sh](start_dashboard.sh) | Start script |
| [stop_dashboard.sh](stop_dashboard.sh) | Stop script |
| [README.md](README.md) | This file |
| [day_19_dashboard.md](day_19_dashboard.md) | Full article (German) |

## Dependencies

The dashboard uses:
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Chart.js** - Data visualization
- **Day 18 SessionAnalytics** - Data backend
- **SQLite** - Database

## Troubleshooting

### WebSocket Errors

**Problem:** `WARNING: No supported WebSocket library detected`

**Solution:**
```bash
pip install 'uvicorn[standard]' websockets
```

Then restart the dashboard.

### Datenbank Nicht Gefunden

**Problem:** `FileNotFoundError: heist_analytics.db`

**Solution:**
```bash
cd day_19
python3 init_database.py
```

### Keine Sessions Im Dashboard

**Problem:** Session-Dropdown ist leer

**Solution:**
```bash
cd day_19
./run_heist.sh --turns 3  # Generate test session
```

### Model Antwortet Nicht Zum Thema

**Problem:** LLM spricht über "Data Structures" statt Heist-Planning

**Cause:** Falsches Model in LM Studio oder System-Prompts werden ignoriert

**Solution:**
- LM Studio: Richtiges Model laden (`google/gemma-3n-e4b`)
- Temperature anpassen in `agents_config.yaml`
- Max-Tokens erhöhen falls Responses abgeschnitten werden

### Port already in use

```bash
# Kill process on port 8007
lsof -ti:8007 | xargs kill -9

# Restart dashboard
./day_19/start_dashboard.sh
```

### No sessions found

```bash
# Check database
sqlite3 heist_analytics.db "SELECT COUNT(*) FROM sessions;"

# If 0, generate sessions
./run_heist.sh --turns 5
```

### Database file not found

```bash
# Check config.yaml database path
cat config.yaml | grep -A 2 "database:"

# Verify file exists
ls -la heist_analytics.db

# Initialize if missing
python3 init_database.py
```

### WebSocket connection failed

- Ensure server is running: `lsof -i :8007`
- Check browser console for errors
- Verify firewall settings
- Check WebSocket dependencies: `pip install 'uvicorn[standard]' websockets`

### Charts not showing

- Open browser developer console (F12)
- Check for JavaScript errors
- Verify data is returned: `curl http://localhost:8007/api/sessions`
- Clear browser cache and reload
- Ensure Chart.js CDN is accessible

## Development

### Enable Hot Reload

Edit [config.yaml](config.yaml):

```yaml
server:
  reload: true  # Enable auto-reload on code changes
```

### Custom Database Path

Use absolute path:

```yaml
database:
  path: "/absolute/path/to/your/heist_audit.db"
```

### Change Port

```yaml
server:
  port: 9000  # Use different port
```

## Integration

The dashboard integrates with:

- **Day 16/17** - Generates session data
- **Day 18** - Provides analytics backend
- **Day 20** - Will add interactive controls
- **Day 21** - Will add mole detection game

## Next Steps

See [day_19_dashboard.md](day_19_dashboard.md) for:
- Detailed architecture explanation
- Code examples
- Design decisions
- Future enhancements
