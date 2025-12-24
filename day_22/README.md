# Day 22: AI-Powered Mole Detection

**RAG-based Sabotage Detection System built on Day 20's Infrastructure**

## Overview

Day 22 adds AI-powered mole detection to the heist system. Instead of manually guessing who the mole is, this system uses a RAG (Retrieval-Augmented Generation) approach to analyze agent behavior and suggest the most suspicious agent.

## Key Features

### 🤖 RAG-Based Detection Pipeline

1. **Retrieval**: Rule-based pattern analysis extracts suspicious signals
   - Tool Usage Anomalies (25% weight)
   - Timing Inconsistencies (30% weight)
   - Message Anomalies (20% weight)
   - Information Quality (25% weight)

2. **Augmentation**: Patterns are structured as context for LLM analysis

3. **Generation**: Optional LLM analyzes conversation with retrieved context
   - 60% rule-based scores
   - 40% LLM scores (if enabled)

### 📊 Detection Signals

**Tool Usage Analysis:**
- Success rate below average
- Wrong tools suggested
- Unusual tool patterns

**Timing Analysis:**
- Frequent timing-related mentions
- Contradictions ("wait, actually...")
- Time estimate inconsistencies

**Message Analysis:**
- Unusual message length (too short/long)
- Hesitation markers ("hmm", "let me think")
- Deviation from baseline patterns

**Information Quality:**
- Vague language ("maybe", "not sure")
- Low concrete information ratio
- Missing specific details

## Architecture

```
Day 22 (Standalone, built on Day 20)
├── sabotage_detector.py           # RAG-based detection engine
├── detection_dashboard_server.py  # Server with AI endpoints
├── detection_dashboard.html       # UI for detection results
└── test_ai_detection_integration.py

Imports from Day 20:
├── heist_controller.py            # Session management & mole game
├── integrated_agent_with_controller.py  # Controller-aware agents
└── session_analytics.py           # Data access layer
```

## Quick Start

### 1. Start the Server

```bash
./day_22/start_detection_dashboard.sh
# Or directly:
python3 day_22/detection_dashboard_server.py
```

Server runs on: `http://localhost:8010`

### 2. Run a Heist with Mole

Use Day 20's controlled heist system to create a session:

```bash
# In Terminal 1: Start server (if not running)
python3 day_22/detection_dashboard_server.py

# In Terminal 2: Run a heist
python3 day_20/run_controlled_heist.py --demo
```

### 3. Analyze with AI Detection

```bash
# Run the integration test
python3 day_22/test_ai_detection_integration.py
```

Or use the API directly:

```bash
# Get AI analysis for a session
curl http://localhost:8010/api/ai-detect/analyze \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"session_id": "heist_001"}'

# Get quick suggestion
curl http://localhost:8010/api/ai-detect/suggest \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"session_id": "heist_001"}'
```

## API Endpoints

### AI Detection Endpoints (NEW in Day 22)

- `POST /api/ai-detect/analyze` - Full RAG analysis with score breakdown
- `POST /api/ai-detect/suggest` - Quick mole suggestion
- `GET /api/ai-detect/session/{session_id}` - Convenience endpoint
- `GET /api/detection-info` - Detection system information

### Day 20 Base Endpoints (Included)

All Tag 20 endpoints are available:
- `/api/heist/*` - Heist control (start, pause, resume, command)
- `/api/sessions` - Session analytics
- `/api/heist/{id}/mole-status` - Mole game status
- `/ws` - WebSocket for real-time updates

## Example Output

```json
{
  "session_id": "heist_001",
  "suggested_mole": "hacker",
  "confidence": 0.847,
  "suspicion_scores": {
    "hacker": 0.847,
    "planner": 0.421,
    "safecracker": 0.312,
    "getaway_driver": 0.198
  },
  "score_breakdown": {
    "hacker": {
      "tool_usage": 0.650,
      "timing": 0.920,
      "message_anomaly": 0.750,
      "information_quality": 0.850,
      "combined": 0.847
    }
  },
  "analysis_weights": {
    "tool_usage_anomaly": 0.25,
    "timing_inconsistency": 0.30,
    "message_anomaly": 0.20,
    "information_quality": 0.25
  }
}
```

## Configuration

### Enable LLM Integration (Optional)

The detector can use a local LLM for enhanced analysis:

```python
from day_22.sabotage_detector import SabotageDetector

# With LLM (requires LM Studio or compatible)
detector = SabotageDetector(
    use_llm=True,
    llm_base_url="http://localhost:1234/v1"
)

# Pure rule-based (no LLM needed)
detector = SabotageDetector(use_llm=False)
```

### Adjust Detection Weights

```python
detector.weights = {
    "tool_usage_anomaly": 0.30,    # Increase tool weight
    "timing_inconsistency": 0.25,
    "message_anomaly": 0.20,
    "information_quality": 0.25
}
```

## Testing

Run the integration test to verify AI detection:

```bash
python3 day_22/test_ai_detection_integration.py
```

The test will:
1. Find an existing session with data
2. Run full AI analysis
3. Get quick AI suggestion
4. Compare AI prediction with actual mole
5. Display accuracy metrics

## How It Works

### 1. Data Collection

The `SabotageDetector` receives:
- **Messages**: Agent conversation history
- **Tool Usage**: Tool calls with success/failure
- **Agents**: List of agent names

### 2. Pattern Analysis (Retrieval)

Four analyzers extract suspicious patterns:
- `_analyze_tool_usage()` - Tool failure rates
- `_analyze_timing_patterns()` - Timing keywords & contradictions
- `_analyze_message_anomalies()` - Message length & hesitation
- `_analyze_information_quality()` - Concrete vs vague language

### 3. Scoring (Generation)

Rule-based scores are combined with weights to produce suspicion scores (0.0-1.0):

```python
suspicion = (
    tool_score * 0.25 +
    timing_score * 0.30 +
    message_score * 0.20 +
    info_score * 0.25
)
```

Optional: LLM analyzes conversation with retrieved patterns as context.

### 4. Suggestion

The agent with the highest combined score is suggested as the mole.

## Comparison with Day 20/21

**Day 20**: Interactive dashboard with pause/resume and command injection
**Day 21**: Random mole selection with manual detection (integrated into Day 20)
**Day 22**: AI-powered detection that analyzes patterns to suggest the mole

Day 22 builds on Day 20's infrastructure but runs as a standalone service on port 8010.

## Performance

Detection accuracy improves with:
- **More data**: Longer conversations provide more signals
- **Clear sabotage**: Obvious patterns are easier to detect
- **Multiple agents**: Better baseline for anomaly detection

Expected accuracy: **Better than random (25%)**, typically **40-70%** depending on sabotage subtlety.

## Troubleshooting

**No sessions found:**
```bash
# First run a heist to create session data
python3 day_20/run_controlled_heist.py --demo
```

**LLM errors:**
```python
# Disable LLM and use pure rule-based
detector = SabotageDetector(use_llm=False)
```

**Low accuracy:**
- Ensure sufficient session data (5+ turns)
- Check that mole actually sabotaged (injected instructions)
- Try adjusting detection weights

## Further Reading

- [Day 22 Article](day_22_sabotage_detection.md) - Full explanation of RAG approach
- [Day 20 Article](../day_20/day_20_interactive_dashboard.md) - Base infrastructure
- [QUICKSTART.md](QUICKSTART.md) - Step-by-step getting started guide

## License

Part of Advent of Code 2025 Heist Project
