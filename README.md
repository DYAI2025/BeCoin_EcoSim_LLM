# BeCoin EcoSim LLM

> **An autonomous startup economy simulator powered by local LLMs, multi-agent orchestration, and a real-time FastAPI dashboard.**

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com)
[![Fly.io](https://img.shields.io/badge/Deployed-Fly.io-purple.svg)](https://fly.io)

---

## Table of Contents

1. [What Is BeCoin EcoSim?](#what-is-becoin-ecosim)
2. [Key Features](#key-features)
3. [Architecture Overview](#architecture-overview)
4. [Project Structure](#project-structure)
5. [Quick Start](#quick-start)
6. [Configuration & Environment Variables](#configuration--environment-variables)
7. [API Reference](#api-reference)
8. [Autonomous Agents](#autonomous-agents)
9. [Deployment](#deployment)
10. [Testing](#testing)
11. [Dependencies & Licenses](#dependencies--licenses)
12. [Contributing](#contributing)
13. [License](#license)

---

## What Is BeCoin EcoSim?

**BeCoin EcoSim LLM** is a self-contained simulation of an autonomous startup economy. It models a fictional company (the "BeCoin Agency") consisting of AI agents who work on projects, earn salaries, generate leads, complete client work, and manage a shared treasury — all without human intervention.

The system combines three major components:

- **Economy Engine** — A Python simulation core that tracks the treasury, agents, projects, transactions, and financial metrics. It enforces strict invariants (e.g., the treasury balance can never go below zero).
- **Real-Time Dashboard** — A FastAPI web server with REST and WebSocket endpoints, serving an HTML dashboard that visualises the live state of the economy (treasury balance, agent productivity, project pipeline, sales leads, CEO questions).
- **Autonomous Agent System** — A local-LLM-powered orchestrator (using [Ollama](https://ollama.com) with the `qwen2.5-coder:7b` model) that can read Markdown execution plans, route tasks to one of 51 specialized AI agent personalities, generate and write code, and improve the simulation itself — without any cloud API keys.

The project is also a research artefact: it documents the economic problems of a naive agent-based simulation (`beCoinCycle.md`, `SPEX.md`) and tracks iterative solutions (engine v1 → v2 → v3 → v3.1) that make the economy self-sustaining.

---

## Key Features

### 🏦 Treasury-Safe Economy Engine
- Immutable `EconomySnapshot` dataclasses frozen at each simulation tick
- Strict `InsufficientFundsError` — no operation can drain the treasury below zero
- Full audit trail: every financial event creates a `Transaction` record
- Project lifecycle enforcement: `pipeline → active → completed` (or `paused`)
- Hourly `advance_time()` loop with configurable burn rates, agent salaries, and project revenues

### 🤖 51 Specialized AI Agent Personalities
The autonomous system includes a roster of 51 AI agents across 9 professional categories:

| Category | Agents | Count |
|---|---|---|
| Engineering | Frontend, Backend, DevOps, AI/ML, Mobile, … | 7 |
| Design | UX Architect, UI Designer, Brand Guardian, … | 6 |
| Marketing | Growth, Social Media, Content, App Store, … | 8 |
| Product | Sprint Prioritizer, Trend Researcher, Feedback Synthesizer | 3 |
| Project Management | Senior PM, Studio Producer, Experiment Tracker, … | 5 |
| Testing | Reality Checker, Performance, API Testing, … | 7 |
| Support | Finance, Legal, Analytics, Infrastructure, … | 6 |
| Spatial Computing | VisionOS, XR, Metal, Terminal Integration, … | 6 |
| Specialized | Orchestrator, LSP Engineer, Data Analytics | 3 |

Each agent has a distinct personality, area of expertise, and communication style.

### 📊 Real-Time Dashboard
- HTML dashboard (`dashboard/office-ui.html` and `dashboard/economy-dashboard.html`)
- FastAPI backend serving live JSON data from the economy engine
- WebSocket endpoints for live push updates (no polling needed)
- CEO Discovery view: proposals, operational patterns, pain points
- Interactive two-way chat with agents persisted in `chat_history.json`
- Optional HTTP Basic Auth via environment variables

### 🔄 Autonomous Operation Loop
- `autonomous_becoin_system.py` runs a continuous watchdog loop:
  - Checks if Ollama is running and restarts it via Docker if needed
  - Checks if the economy simulation is active (via `treasury.json` file freshness)
  - Logs status to `autonomous_agents/logs/autonomous_system.log`
- Startup scripts (`autonomous_startup.sh` / `v2` / `v3`) for one-command launch
- Linux systemd service file (`becoin-autonomous.service`) for background operation

### 🚀 CI/CD & Cloud Deployment
- GitHub Actions pipeline: Black formatting → flake8 linting → pytest → Fly.io deploy
- Containerised with Docker (Python 3.11-slim, single-stage build)
- Deployed to [Fly.io](https://fly.io) in the `fra` (Frankfurt) region
- Health-check endpoint at `/api/status`
- Post-deploy initialisation script (`scripts/fly_post_deploy.py`)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        BeCoin EcoSim LLM                        │
│                                                                 │
│  ┌──────────────────┐    ┌─────────────────┐    ┌───────────┐  │
│  │  Economy Engine  │    │    Dashboard     │    │Autonomous │  │
│  │ becoin_economy/  │───▶│  dashboard/      │    │  Agents   │  │
│  │                  │    │  server.py       │    │autonomous_│  │
│  │  models.py       │    │  office-ui.html  │    │agents/    │  │
│  │  engine_v3.py    │    │  WebSocket /ws/  │    │           │  │
│  │  exporter.py     │    │  REST /api/      │    │orchestrat │  │
│  └──────────────────┘    └─────────────────┘    │or.py      │  │
│          │                        ▲              │chat_      │  │
│          │  JSON snapshots        │              │session.py │  │
│          └────────────────────────┘              └─────┬─────┘  │
│                                                        │        │
│                                             ┌──────────▼──────┐ │
│                                             │  Ollama (local) │ │
│                                             │  qwen2.5-coder  │ │
│                                             │  :7b            │ │
│                                             └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Three-Layer Design

**1. Economy Engine (`becoin_economy/`)**

The core simulation layer. Pure Python, no web dependencies.

```
becoin_economy/
├── models.py        # Immutable dataclasses: Treasury, Agent, Project,
│                    #   Transaction, EconomySnapshot, ImpactRecord
├── engine.py        # BecoinEconomy class (v1 — basic operations)
├── engine_v2.py     # v2 — passive time advance, basic projects
├── engine_v3.py     # v3 — work assignment, lead generation, pipeline mgmt
├── engine_v31.py    # v3.1 — economics balancing refinements
├── exporter.py      # build_dashboard_payload() → JSON files
└── tests/           # pytest test suite
```

**2. Dashboard (`dashboard/`)**

FastAPI web server + HTML frontend.

```
dashboard/
├── server.py              # FastAPI app (REST + WebSocket)
├── ceo_data_bridge.py     # Reads .claude-flow/discovery-sessions/
├── websocket_manager.py   # WebSocket connection pool
├── office-ui.html         # Main CEO/office dashboard
├── economy-dashboard.html # Economy metrics dashboard
├── requirements.txt       # Python dependencies
├── becoin-economy/        # Runtime JSON data files (treasury, agents, …)
└── tests/                 # pytest async test suite
```

**3. Autonomous Agents (`autonomous_agents/`)**

LLM-powered orchestration layer.

```
autonomous_agents/
├── orchestrator.py        # Parses Markdown plans, routes tasks to agents
├── chat_session.py        # Interactive CLI chat with economy context
├── economy_context.py     # Builds economy summaries for agent prompts
├── monitor.py             # Real-time log watcher
├── personalities/
│   └── loader.py          # Loads 51 agent personality JSON files
├── config/
│   └── models.json        # LLM provider configuration
└── logs/                  # Execution logs
```

---

## Project Structure

```
BeCoin_EcoSim_LLM/
├── .github/
│   └── workflows/
│       ├── ci.yml               # Lint + test pipeline
│       └── deploy.yml           # Auto-deploy to Fly.io
├── autonomous_agents/           # LLM orchestration (see above)
├── becoin_economy/              # Simulation engine (see above)
├── dashboard/                   # FastAPI + HTML frontend (see above)
├── design/                      # Design agent personalities
├── docs/
│   └── plans/                   # Autonomous execution plan files (.md)
├── engineering/                 # Engineering agent personalities
├── marketing/                   # Marketing agent personalities
├── product/                     # Product agent personalities
├── project-management/          # PM agent personalities
├── scripts/
│   └── fly_post_deploy.py       # Post-deployment initialisation
├── spatial-computing/           # Spatial computing agent personalities
├── specialized/                 # Specialized agent personalities
├── support/                     # Support agent personalities
├── testing/                     # Testing agent personalities
│
├── api_server.py                # Standalone FastAPI entry point (v3)
├── autonomous_becoin_system.py  # Autonomous watchdog system
├── autonomous_startup.sh        # One-command startup (v1/v2/v3)
├── autonomous_startup_v2.sh
├── autonomous_startup_v3.sh
├── becoin-autonomous.service    # systemd service definition
├── beCoinCycle.md               # Economy cycle analysis report
├── CLAUDE.md                    # AI agent instructions for this repo
├── CONTRIBUTING.md              # Contribution guide
├── DEPLOYMENT.md                # Deployment guide
├── Dockerfile                   # Docker build definition
├── fly.toml                     # Fly.io configuration
├── install_service.sh           # systemd service installer
├── post_deploy.sh               # Post-deploy helper
├── pyproject.toml               # Black/tool configuration
├── SPEX.md                      # Solution Proposal EXchange document
├── TODO.md                      # Open task list
├── TROUBLESHOOTING.md           # Common issues & solutions
└── LICENSE                      # MIT License
```

---

## Quick Start

### Prerequisites

- **Python 3.12** (or 3.11 for Docker)
- **[Ollama](https://ollama.com)** installed and running (for autonomous agent features)
- ~8–16 GB RAM recommended for local LLM execution

### 1. Clone the repository

```bash
git clone https://github.com/DYAI2025/BeCoin_EcoSim_LLM.git
cd BeCoin_EcoSim_LLM
```

### 2. Install dashboard dependencies

```bash
cd dashboard
pip install -r requirements.txt
cd ..
```

### 3. Configure environment variables (optional)

```bash
cp .env.example .env
# Edit .env — set AUTH_USERNAME, AUTH_PASSWORD, LLM_PROVIDER, etc.
```

### 4. Start the dashboard server

```bash
uvicorn dashboard.server:app --reload --port 3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 5. Set up autonomous agents (optional, requires Ollama)

```bash
# One-click setup: installs Ollama, downloads qwen2.5-coder:7b, loads 51 personalities
./autonomous_agents/setup_autonomous_agents.sh
```

### 6. Run the autonomous system

```bash
# Start the full autonomous loop (economy + agents)
./autonomous_startup_v3.sh

# Or run the Python watchdog directly
python3 autonomous_becoin_system.py
```

### 7. Interactive chat with an agent

```bash
# Start interactive chat with the default agent
python3 autonomous_agents/chat_session.py

# Chat with a specific personality
python3 autonomous_agents/chat_session.py --personality "frontend-developer"

# One-off query
python3 autonomous_agents/chat_session.py --message "What is the current treasury balance?"
```

---

## Configuration & Environment Variables

Copy `.env.example` to `.env` and set the following variables as needed:

### Dashboard

| Variable | Default | Description |
|---|---|---|
| `AUTH_USERNAME` | _(unset)_ | HTTP Basic Auth username. Auth disabled if unset. |
| `AUTH_PASSWORD` | _(unset)_ | HTTP Basic Auth password. |
| `DISCOVERY_SESSIONS_PATH` | `../.claude-flow/discovery-sessions` | Path to CEO discovery session JSON files. |
| `CEO_DASHBOARD_WS_POLL_INTERVAL` | `5` | WebSocket polling interval in seconds. |

### LLM Provider

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | LLM backend: `ollama`, `anthropic`, `openai`, `together` |
| `OLLAMA_ENDPOINT` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Ollama model name |
| `ANTHROPIC_API_KEY` | _(unset)_ | Anthropic API key (if using Claude) |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | Anthropic model name |
| `OPENAI_API_KEY` | _(unset)_ | OpenAI API key (if using GPT) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model name |
| `TOGETHER_API_KEY` | _(unset)_ | Together.ai API key |
| `TOGETHER_MODEL` | `Qwen/Qwen2.5-Coder-32B-Instruct` | Together.ai model name |

> **Note:** Local development defaults to Ollama. No API keys are required for full functionality if Ollama is installed.

---

## API Reference

### CEO Discovery (REST)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/ceo/status` | Latest discovery session overview |
| `GET` | `/api/ceo/proposals?min_roi={float}` | Proposals filtered by minimum ROI |
| `GET` | `/api/ceo/patterns?type={type}` | Operational patterns by type |
| `GET` | `/api/ceo/pain-points` | Aggregated pain points and blockers |
| `GET` | `/api/ceo/history` | All discovery session summaries |

### Chat (REST)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/send` | Send a message: `{type, content, target_agent, sender}` |
| `GET` | `/api/chat/history?limit={int}` | Retrieve chat history (default: 50 messages) |

### Economy (REST — `api_server.py` / standalone mode)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/status` | System health |
| `GET` | `/api/treasury` | Treasury data and transactions |
| `GET` | `/api/agents` | Agent roster and performance |
| `GET` | `/api/projects` | Project pipeline |
| `GET` | `/api/pipeline` | Sales leads |
| `GET` | `/api/questions` | Pending CEO questions |
| `POST` | `/api/advance` | Advance simulation by N hours |
| `POST` | `/api/accept-lead/{lead_id}` | Accept a lead and create a project |
| `POST` | `/api/reject-lead/{lead_id}` | Reject a lead |
| `POST` | `/api/start-autonomous` | Start the autonomous simulation loop |
| `POST` | `/api/stop-autonomous` | Stop the autonomous simulation loop |

### WebSocket

| Endpoint | Description |
|---|---|
| `WS /ws/ceo` | Live discovery session updates |
| `WS /ws/chat` | Real-time chat messages (broadcast to all clients) |

### Authentication

All endpoints support **HTTP Basic Auth** when `AUTH_USERNAME` and `AUTH_PASSWORD` are set.
WebSocket connections authenticate via query parameters: `?username=...&password=...`

---

## Autonomous Agents

### Execution Flow

```
Markdown Plan
     │
     ▼
 PlanParser  ──▶  Orchestrator  ──▶  Personality Loader
                       │
                       ▼
                  Ollama LLM (qwen2.5-coder:7b)
                       │
                       ▼
               Code Generation / File Changes
```

### Running Plans

```bash
# Preview without executing
python3 autonomous_agents/orchestrator.py docs/plans/<plan-name>.md --dry-run

# Execute a plan
python3 autonomous_agents/orchestrator.py docs/plans/<plan-name>.md

# Monitor live
python3 autonomous_agents/monitor.py -f
```

### ⚠️ LLM Availability by Environment

| Feature | Local (Ollama) | Fly.io (2 GB RAM) |
|---|---|---|
| Dashboard + REST API | ✅ | ✅ |
| CEO Discovery / WebSocket | ✅ | ✅ |
| Chat UI | ✅ | ✅ (static context only) |
| Real AI chat responses | ✅ | ❌ (no Ollama) |
| Autonomous code generation | ✅ | ❌ |
| All 51 agent personalities | ✅ | ❌ |

To enable real AI on Fly.io, set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=sk-ant-...` (costs ~$15–25/month). See `docs/FLY_IO_LLM_INTEGRATION.md` for all options.

---

## Deployment

### Docker (local)

```bash
docker build -t becoin-ecosim .
docker run -p 3000:3000 \
  -e AUTH_USERNAME=admin \
  -e AUTH_PASSWORD=secret \
  becoin-ecosim
```

### Fly.io (production)

```bash
# Install Fly CLI: https://fly.io/docs/hands-on/install-flyctl/
fly auth login

# Deploy
fly deploy

# Set authentication secrets
fly secrets set AUTH_USERNAME="admin" AUTH_PASSWORD="secure_password"

# View logs
fly logs
fly status
```

The `fly.toml` is pre-configured for the `fra` (Frankfurt) region with:
- 4 shared vCPUs, 2 GB RAM
- Auto-start/stop machines based on traffic
- HTTPS enforced
- Post-deploy initialisation via `scripts/fly_post_deploy.py`

### systemd Service (Linux server)

```bash
./install_service.sh
systemctl start becoin-autonomous
systemctl enable becoin-autonomous
journalctl -u becoin-autonomous -f
```

### CI/CD Pipeline

Every push to `main` triggers the GitHub Actions workflow:

```
git push → Black check → flake8 → pytest → fly deploy
```

---

## Testing

```bash
# Run all tests
pytest

# Run economy engine tests only
pytest becoin_economy/tests/ -v

# Run dashboard tests only
pytest dashboard/tests/ -v

# Run specific test file
pytest becoin_economy/tests/test_engine_transactions.py

# Run CI checks locally (mirrors GitHub Actions)
black --check .
flake8 .
pytest -q becoin_economy
```

### Test Coverage

| Test Suite | File(s) | What Is Tested |
|---|---|---|
| Engine transactions | `test_engine_transactions.py` | Core operations, treasury safety, project state transitions |
| Stress simulation | `test_stress_simulation.py` | Invariants under randomised load |
| Exporter | `test_exporter.py` | JSON payload serialisability |
| Dashboard server | `test_server.py` | Server health and startup |
| API endpoints | `test_api_endpoints.py` | REST endpoints for CEO data |
| Chat | `test_chat.py` | Message persistence, history, formatting |
| WebSocket | `test_websocket.py` | Connection, broadcast, disconnection |
| Data bridge | `test_data_bridge.py` | Discovery session loading and parsing |

---

## Dependencies & Licenses

This project uses the following open-source libraries. All licenses are reproduced in full in the linked sources and are compatible with the MIT license of this project.

### Runtime Dependencies

| Package | Version | License | License URL |
|---|---|---|---|
| [FastAPI](https://github.com/tiangolo/fastapi) | 0.109.0 | **MIT** | https://github.com/tiangolo/fastapi/blob/master/LICENSE |
| [Uvicorn](https://github.com/encode/uvicorn) | 0.27.0 | **BSD 3-Clause** | https://github.com/encode/uvicorn/blob/master/LICENSE.md |
| [Pydantic](https://github.com/pydantic/pydantic) | 2.5.3 | **MIT** | https://github.com/pydantic/pydantic/blob/main/LICENSE |
| [pydantic-settings](https://github.com/pydantic/pydantic-settings) | 2.1.0 | **MIT** | https://github.com/pydantic/pydantic-settings/blob/main/LICENSE |
| [websockets](https://github.com/python-websockets/websockets) | 12.0 | **BSD 3-Clause** | https://github.com/python-websockets/websockets/blob/main/LICENSE |
| [python-multipart](https://github.com/Kludex/python-multipart) | 0.0.6 | **Apache 2.0** | https://github.com/Kludex/python-multipart/blob/master/LICENSE.txt |
| [python-dateutil](https://github.com/dateutil/dateutil) | 2.8.2 | **Apache 2.0 / BSD 3-Clause (dual)** | https://github.com/dateutil/dateutil/blob/master/LICENSE |
| [anthropic](https://github.com/anthropics/anthropic-sdk-python) | 0.18.1 | **MIT** | https://github.com/anthropics/anthropic-sdk-python/blob/main/LICENSE |

### Development & Testing Dependencies

| Package | Version | License | License URL |
|---|---|---|---|
| [pytest](https://github.com/pytest-dev/pytest) | 7.4.4 | **MIT** | https://github.com/pytest-dev/pytest/blob/main/LICENSE |
| [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) | 0.23.3 | **Apache 2.0** | https://github.com/pytest-dev/pytest-asyncio/blob/master/LICENSE |
| [httpx](https://github.com/encode/httpx) | 0.26.0 | **BSD 3-Clause** | https://github.com/encode/httpx/blob/master/LICENSE.md |
| [Black](https://github.com/psf/black) | latest | **MIT** | https://github.com/psf/black/blob/main/LICENSE |
| [flake8](https://github.com/PyCQA/flake8) | latest | **MIT** | https://github.com/PyCQA/flake8/blob/main/LICENSE |

### External Tools & Models

| Tool | License | Notes |
|---|---|---|
| [Ollama](https://github.com/ollama/ollama) | **MIT** | Local LLM runtime. Must be installed separately. https://github.com/ollama/ollama/blob/main/LICENSE |
| [Qwen2.5-Coder 7B](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | **Apache 2.0** | LLM model weights. Downloaded automatically by Ollama. Model card: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct |
| [Docker base image python:3.11-slim](https://hub.docker.com/_/python) | **MIT / various** | The `python:3.11-slim` image is based on Debian and Python. https://github.com/docker-library/python/blob/master/LICENSE |

> **License compliance notice:**
> - **MIT-licensed packages** (FastAPI, Pydantic, pytest, Black, Ollama, anthropic SDK, …): Permission is granted to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies. The copyright notice and permission notice must be included in all copies or substantial portions of the Software.
> - **BSD 3-Clause packages** (Uvicorn, websockets, httpx): Use is permitted with attribution; you may not use the name of the contributors to endorse or promote derived products without written permission.
> - **Apache 2.0 packages** (python-multipart, pytest-asyncio, python-dateutil, Qwen2.5-Coder model): Use is permitted with preservation of the NOTICE file (if any) and the Apache 2.0 license text. Patent rights are expressly granted.
> - This project itself is released under the **MIT License** (see [LICENSE](LICENSE)), which is compatible with all dependency licenses listed above.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

### Development Workflow

```bash
# 1. Fork the repo and clone your fork
git clone https://github.com/<your-username>/BeCoin_EcoSim_LLM.git

# 2. Install dependencies
pip install -r dashboard/requirements.txt

# 3. Make your changes

# 4. Run quality checks before committing
black .
flake8 .
pytest

# 5. Open a pull request against main
```

### Code Style

- **Formatter:** [Black](https://github.com/psf/black) with `line-length = 88`, target `py312`
- **Linter:** flake8 (config in `.flake8`)
- **Type hints:** Required on all public functions and class methods
- **Docstrings:** Required on all public classes and functions

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 DYAI2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

See [LICENSE](LICENSE) for the full text.

---

*Last updated: 2026-02-26 — generated and maintained with the help of the BeCoin autonomous agent system.*