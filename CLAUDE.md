# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BeCoin EcoSim is a self-contained simulation of an autonomous startup economy with treasury-aware accounting, agent productivity modeling, and a FastAPI dashboard. It includes an autonomous agent execution system powered by local LLMs (Ollama) that can implement feature plans independently.

## Essential Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest becoin_economy/tests/test_engine_transactions.py

# Run dashboard tests only
pytest dashboard/tests/

# Run with verbose output
pytest -v
```

### Dashboard Server
```bash
# Install dashboard dependencies
cd dashboard
pip install -r requirements.txt

# Start FastAPI server (default port 3000)
uvicorn server:app --reload --port 3000

# Serve static dashboard (separate terminal)
python3 -m http.server 8080
```

### Autonomous Agents
```bash
# One-click setup (installs Ollama, downloads Qwen2.5-Coder 7B, loads 51 agent personalities)
./autonomous_agents/setup_autonomous_agents.sh

# Dry-run execution (shows plan without executing)
python3 autonomous_agents/orchestrator.py docs/plans/<plan-name>.md --dry-run

# Execute plan autonomously
python3 autonomous_agents/orchestrator.py docs/plans/<plan-name>.md

# Monitor progress in real-time
python3 autonomous_agents/monitor.py -f
```

### Ollama (Local LLM)
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# List installed models
ollama list

# Test model directly
ollama run qwen2.5-coder:7b "test prompt"
```

## Architecture

### Three-Layer Design

1. **Economy Engine** (`becoin_economy/`)
   - `models.py`: Immutable dataclasses (Treasury, Agent, Project, Transaction, EconomySnapshot, ImpactRecord)
   - `engine.py`: Core orchestration with `BecoinEconomy` class
     - Methods: `start_project()`, `complete_project()`, `pay_agent()`, `advance_time()`
     - Exceptions: `InsufficientFundsError`, `UnknownProjectError`, `UnknownAgentError`
   - `exporter.py`: Converts snapshots to dashboard JSON via `build_dashboard_payload()`

2. **Dashboard** (`dashboard/`)
   - `server.py`: FastAPI app with REST and WebSocket endpoints
   - `ceo_data_bridge.py`: Reads discovery sessions from `.claude-flow/discovery-sessions/`
   - `websocket_manager.py`: Manages WebSocket clients for live updates
   - Authentication: Uses HTTP Basic Auth if `AUTH_USERNAME` and `AUTH_PASSWORD` env vars set

3. **Autonomous Agents** (`autonomous_agents/`)
   - `orchestrator.py`: Main execution engine (parses plans, routes tasks, executes via LLM)
   - `personalities/loader.py`: Loads 51 specialized agent personalities from Agency_of_Agents
   - `monitor.py`: Real-time log monitoring
   - Logs: `autonomous_agents/logs/execution_*.log`

### Critical Patterns

**Economy Invariants**: The engine enforces strict treasury safety:
- No operation can reduce balance below zero (raises `InsufficientFundsError`)
- All transactions are chronologically ordered
- Project stages follow: `pipeline` → `active` → `completed` (or `paused`)

**Dashboard Data Flow**:
```
BecoinEconomy → snapshot() → build_dashboard_payload() → JSON files
                                                        ↓
                        FastAPI (server.py) ← office-ui.html polls REST endpoints
```

**Autonomous Execution Flow**:
```
Markdown Plan → PlanParser → Orchestrator → Personality Loader → Ollama LLM → Code Generation → File Changes
```

## Key Design Decisions

1. **Immutable Snapshots**: `EconomySnapshot` freezes state at a point in time (uses dataclasses with `frozen=True` where appropriate)

2. **Dashboard JSON Schema**: Five files expected by `office-ui.html`:
   - `treasury.json`: Balance, transactions, burn rate
   - `agent-roster.json`: Agent list with productivity metrics
   - `projects.json`: Project pipeline with stages
   - `impact-ledger.json`: Historical impact records
   - `orchestrator-status.json`: Orchestrator health metrics

3. **CEO Discovery Integration**: FastAPI reads JSON sessions from `.claude-flow/discovery-sessions/` and broadcasts over WebSocket (`/ws/ceo`)

4. **Local-First Autonomous Agents**: Uses Ollama for zero-API-key execution with specialized personalities for task routing

## Testing Strategy

- **Engine tests** (`becoin_economy/tests/`): Verify transaction logic, treasury safety, project lifecycle
- **Stress tests** (`test_stress_simulation.py`): Randomized operations to prove invariants hold
- **Exporter tests** (`test_exporter.py`): Ensure JSON payloads are serializable and dashboard-compatible
- **Dashboard tests** (`dashboard/tests/`): REST endpoints, WebSocket connections, data bridge

All tests must pass before merging (`pytest` from repo root).

## Environment Variables

Required for dashboard authentication:
- `AUTH_USERNAME`: HTTP Basic Auth username (optional, disables auth if unset)
- `AUTH_PASSWORD`: HTTP Basic Auth password (optional, disables auth if unset)

## Common Workflows

### Generating Dashboard Payloads
```python
from becoin_economy import BecoinEconomy, build_dashboard_payload
import json

economy = BecoinEconomy(treasury=..., agents=..., projects=...)
payload = build_dashboard_payload(economy)

for filename, data in payload.items():
    with open(f"dashboard/becoin-economy/{filename}", "w") as f:
        json.dump(data, f, indent=2)
```

### Adding New Economy Operations
1. Add method to `BecoinEconomy` in `engine.py`
2. Ensure treasury safety (check balance before deductions)
3. Create `Transaction` record for audit trail
4. Add test in `becoin_economy/tests/`
5. Update exporter if dashboard needs new data

### Creating Autonomous Execution Plans
1. Write markdown plan in `docs/plans/` with task structure:
   ```markdown
   ## Task N: Title
   Description

   **File: path/to/file.py**
   ```python
   # code example
   ```
   ```
2. Test with `--dry-run` flag first
3. Monitor logs during execution

## Dependencies

Dashboard requires: `fastapi`, `uvicorn`, `websockets`, `pydantic`, `anthropic`, `pytest`, `httpx`

Autonomous agents require: Ollama running locally with `qwen2.5-coder:7b` model (setup via `setup_autonomous_agents.sh`)

## File Locations

- Tests: `becoin_economy/tests/`, `dashboard/tests/`
- Implementation plans: `docs/plans/`
- Discovery sessions: `.claude-flow/discovery-sessions/`
- Dashboard static files: `dashboard/` (HTML/CSS)
- Dashboard JSON: `dashboard/becoin-economy/` (generated)
- Agent personalities: Loaded from `~/Dokumente/DYAI_home/DEV/AI_LLM/Agency_of_Agents/`
- Execution logs: `autonomous_agents/logs/`
