# 🪙 BeCoin EcoSim

![CI Status](https://github.com/DYAI2025/becoin-ecosim-llm/actions/workflows/ci.yml/badge.svg)

BeCoin EcoSim is a self-contained simulation of an autonomous startup economy. It
models treasury health, agent productivity, project pipelines, and the CEO discovery
workflow that surfaces proposals and operational patterns. A FastAPI dashboard exposes
the evolving state while the economy engine enforces BeCoin accounting rules and
prevents catastrophic overspending.

## ✨ Key Capabilities

- **Deterministic economy core** – `becoin_economy` provides a treasury-aware engine
  that tracks transactions, agent output, project lifecycle, and impact records.
- **Dashboard-ready exports** – the exporter converts simulation snapshots into the
  JSON payloads consumed by the pixel-art office UI.
- **CEO discovery bridge** – the FastAPI server reads discovery sessions and streams
  WebSocket updates so leadership can monitor new proposals in real time.
- **Two-way chat** – REST and WebSocket chat endpoints let users talk to agents and
  receive answers grounded in the latest discovery session data.
- **Stress-tested safety rails** – randomized burn/payroll scenarios ensure the
  treasury never silently drops below zero and that hand-offs between components are
  verified by unit tests.
- **Autonomous agents** – self-executing AI agents powered by local LLMs (Ollama) and
  51 specialized personalities that can implement entire feature plans autonomously.

## 🧱 Architecture Overview

```
┌────────────────┐     snapshot      ┌────────────────────┐     JSON files
│ BecoinEconomy   ├───────────────▶  │ Dashboard Exporter │ ─────────────────▶ office-ui.html
│  (engine.py)    │                  │  (exporter.py)     │
└──────┬──────────┘                  └────────┬──────────┘
       │ transactions & metrics               │ REST + WS
       ▼                                      ▼
┌────────────────┐                 ┌────────────────────┐
│ Treasury /      │                 │ FastAPI Server      │
│ Agent Models    │                 │ (dashboard/server) │
└────────────────┘                 └────────────────────┘
```

1. **Simulation** – `BecoinEconomy` coordinates treasury movements, agent activity,
   and project status while guarding against overspending.
2. **Export** – `build_dashboard_payload` turns a snapshot into the five JSON files
   the dashboard expects (`treasury.json`, `agent-roster.json`, `projects.json`,
   `impact-ledger.json`, `orchestrator-status.json`).
3. **Presentation** – the FastAPI service exposes CEO discovery data over REST and
   WebSockets; the static HTML dashboard reads both the generated JSON and live
   discovery updates.

## 📂 Code Map

| Path | Purpose |
|------|---------|
| `becoin_economy/models.py` | Dataclasses for treasury, agents, projects, transactions, and immutable snapshots. |
| `becoin_economy/engine.py` | Economy orchestration logic plus safeguards against overspending. |
| `becoin_economy/exporter.py` | Converts economy snapshots into dashboard JSON payloads. |
| `dashboard/server.py` | FastAPI app exposing CEO discovery endpoints and WebSocket broadcasts. |
| `dashboard/ceo_data_bridge.py` | Reads discovery session JSON from `.claude-flow/discovery-sessions`. |
| `dashboard/websocket_manager.py` | Manages WebSocket clients for live updates. |
| `dashboard/tests/` | API, WebSocket, and data bridge tests. |
| `becoin_economy/tests/` | Engine, exporter, and stress simulation tests. |
| `autonomous_agents/` | Autonomous execution system with local LLMs and specialized agents. |
| `autonomous_agents/orchestrator.py` | Main orchestrator that executes implementation plans autonomously. |
| `autonomous_agents/personalities/` | Loads 51 specialized agent personalities from Agency_of_Agents. |
| `docs/plans/` | Implementation plans in markdown format for autonomous execution. |

## 🧪 Testing & Quality Gates

The codebase ships with end-to-end coverage for the economy engine and dashboard:

- Engine tests validate project lifecycle, payroll, and treasury invariants.
- Exporter tests keep dashboard payloads JSON-serializable.
- Stress simulations ensure balances never go negative and transactions stay
  chronological.
- Dashboard tests cover REST APIs, WebSocket streaming, and chat persistence.

Run the full suite from the repository root:

```bash
pytest
```

### Continuous Integration

GitHub Actions run formatting, linting, and a focused engine test suite on every
push and pull request:

- **Formatting**: `black --check .`
- **Linting**: `flake8 .`
- **Unit tests**: `pytest -q becoin_economy`

See `.github/workflows/ci.yml` for the full pipeline.

## 🚀 Running the Dashboard

1. Install dashboard dependencies:

   ```bash
   pip install -r dashboard/requirements.txt
   ```

2. Ensure data is available:

   - CEO discovery sessions: place JSON files under `.claude-flow/discovery-sessions`
     (or set `DISCOVERY_SESSIONS_PATH`).
   - Economy snapshots: generate JSON under `dashboard/becoin-economy/` using
     `build_dashboard_payload` or run `./autonomous_startup.sh` to produce demo data.

3. Start the FastAPI server from the repo root:

   ```bash
   uvicorn dashboard.server:app --host 0.0.0.0 --port 3000 --reload
   ```

4. Open `http://localhost:3000/` to view the office UI. The page serves directly from
   FastAPI, consumes the exported JSON files, and stays live via WebSocket updates and
   the chat endpoints (`/api/chat/*` and `/ws/chat`).

## 🤖 Autonomous Agents

The project includes an autonomous execution system that can implement entire feature
plans independently using local LLMs and specialized agent personalities.

### Quick Start

```bash
# One-click setup (installs Ollama, downloads Qwen2.5-Coder 7B, loads 51 agent personalities)
./autonomous_agents/setup_autonomous_agents.sh

# Execute a plan with dry-run (shows what would happen without executing)
python3 autonomous_agents/orchestrator.py docs/plans/2025-11-05-ceo-dashboard-integration.md --dry-run

# Execute a plan autonomously
python3 autonomous_agents/orchestrator.py docs/plans/2025-11-05-ceo-dashboard-integration.md

# Monitor progress in real-time (separate terminal)
python3 autonomous_agents/monitor.py -f
```

### Key Features

- **51 Specialized Agents**: Frontend, Backend, AI/ML, DevOps, Testing, Design, Marketing, etc.
- **Local LLM**: Runs Qwen2.5-Coder 7B via Ollama (no API keys needed)
- **Plan-Based Execution**: Reads markdown implementation plans from `docs/plans/`
- **Automatic Code Generation**: Generates and applies code changes to files
- **Real-Time Monitoring**: Track execution progress with live log monitoring
- **Task Routing**: Automatically assigns tasks to appropriate specialized agents

See `autonomous_agents/README.md` for complete documentation.

## 🛠️ Generating Dashboard Payloads

The dashboard expects five JSON files located under `dashboard/becoin-economy/`
(or any directory served alongside the HTML). Use the exporter to generate them from
any economy instance:

```python
import json

from becoin_economy import BecoinEconomy, Agent, Project, Treasury, build_dashboard_payload

treasury = Treasury(start_capital=10000, balance=10000)
agents = [...]  # list of Agent objects
projects = [...]  # list of Project objects
economy = BecoinEconomy(treasury=treasury, agents=agents, projects=projects)

payload = build_dashboard_payload(economy)
for name, data in payload.items():
    with open(f"dashboard/becoin-economy/{name}", "w") as fh:
        json.dump(data, fh, indent=2)
```

## 🧭 CEO Discovery Integration

The FastAPI layer surfaces discovery insights stored as JSON in
`.claude-flow/discovery-sessions/`. Endpoints include:

- `GET /api/ceo/status` – latest session overview
- `GET /api/ceo/proposals` – ROI-filtered proposals
- `GET /api/ceo/patterns` – operational patterns by type
- `GET /api/ceo/pain-points` – aggregated issues
- `GET /api/ceo/history` – session summaries
- `WS /ws/ceo` – live push notifications for proposals, patterns, and status changes

## 🧑‍💻 Development Workflow

1. Update or extend the economy in `becoin_economy/engine.py`.
2. Regenerate payloads via `build_dashboard_payload` if structure changes.
3. Adjust the dashboard or FastAPI server to expose new insights.
4. Run `pytest` to verify economy invariants and API contracts before committing.

## 📄 License

BeCoin EcoSim is released under the MIT License. See [`LICENSE`](LICENSE) for details.
