# 🪙 BeCoin EcoSim

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
- **Stress-tested safety rails** – randomized burn/payroll scenarios ensure the
  treasury never silently drops below zero and that hand-offs between components are
  verified by unit tests.

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

## 🧪 Testing & Quality Gates

Every critical handover is covered by automated tests:

- `test_engine_transactions.py` validates project kick-off, completion, payroll, and
  treasury reconciliation logic.
- `test_exporter.py` confirms JSON payloads remain dashboard-compatible and free of
  non-serializable data.
- `test_stress_simulation.py` runs randomized start/complete/pay/advance cycles to
  prove invariants (`balance >= 0`, chronological transactions, valid metrics).
- Existing dashboard tests guarantee REST and WebSocket endpoints stay functional.

Run the full suite from the repository root:

```bash
pytest
```

## 🚀 Running the Dashboard

1. Install dashboard dependencies:

   ```bash
   cd dashboard
   pip install -r requirements.txt
   ```

2. Start the FastAPI server:

   ```bash
   uvicorn server:app --reload --port 3000
   ```

3. Serve the static dashboard (separate terminal):

   ```bash
   python3 -m http.server 8080
   ```

4. Open `http://localhost:8080/dashboard/office-ui.html` and watch the BeCoin office
   in action. The page polls the FastAPI endpoints and listens for WebSocket events.

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
