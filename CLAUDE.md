# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BeCoin EcoSim is a self-contained simulation of an autonomous startup economy with treasury-aware accounting, agent productivity modeling, and a FastAPI dashboard. It includes an autonomous agent execution system powered by local LLMs (Ollama) that can implement feature plans independently. The system features real-time two-way chat with specialized AI agents, live WebSocket updates, and comprehensive deployment automation to Fly.io.

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

### Interactive Chat System
```bash
# Start interactive chat with default agent
python3 autonomous_agents/chat_session.py

# Chat with specific personality
python3 autonomous_agents/chat_session.py --personality "frontend-developer"

# Chat with plan context
python3 autonomous_agents/chat_session.py --plan docs/plans/2025-11-05-ceo-dashboard-integration.md

# Send single message (non-interactive)
python3 autonomous_agents/chat_session.py --message "Analyze the dashboard performance"
```

### CI/CD and Deployment
```bash
# Run CI checks locally (same as GitHub Actions)
black --check .
flake8 .
pytest -q becoin_economy

# Deploy to Fly.io
fly deploy

# Check deployment status
fly status
fly logs

# Set secrets for authentication
fly secrets set AUTH_USERNAME="admin"
fly secrets set AUTH_PASSWORD="secure_password"
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
     - REST APIs: `/api/ceo/*` (discovery data), `/api/chat/*` (chat history)
     - WebSocket: `/ws/ceo` (live updates), `/ws/chat` (real-time chat)
     - Static: Serves `office-ui.html` and economy JSON files
   - `ceo_data_bridge.py`: Reads discovery sessions from `.claude-flow/discovery-sessions/`
   - `websocket_manager.py`: Manages WebSocket clients for live updates
   - `chat_history.json`: Persisted chat messages (auto-created)
   - Authentication: Uses HTTP Basic Auth if `AUTH_USERNAME` and `AUTH_PASSWORD` env vars set
   - Tests: `dashboard/tests/` with full coverage of REST, WebSocket, and data bridge

3. **Autonomous Agents** (`autonomous_agents/`)
   - `orchestrator.py`: Main execution engine (parses plans, routes tasks, executes via LLM)
   - `chat_session.py`: Interactive chat interface with economy-aware context
   - `economy_context.py`: Builds economy snapshots and summaries for agent context
   - `personalities/loader.py`: Loads 51 specialized agent personalities from Agency_of_Agents
   - `monitor.py`: Real-time log monitoring
   - `config/models.json`: LLM model configuration
   - Logs: `autonomous_agents/logs/execution_*.log`

4. **Specialized Agent Personalities** (51 agents across 9 categories)
   - `engineering/`: Frontend, Backend, DevOps, AI/ML, Mobile (7 agents)
   - `design/`: UX Architect, UI Designer, Brand Guardian, etc. (6 agents)
   - `marketing/`: Growth, Social Media, Content, App Store (8 agents)
   - `product/`: Sprint Prioritizer, Trend Researcher, Feedback Synthesizer (3 agents)
   - `project-management/`: Senior PM, Studio Producer, Experiment Tracker (5 agents)
   - `testing/`: Reality Checker, Performance, API Testing (7 agents)
   - `support/`: Finance, Legal, Analytics, Infrastructure (6 agents)
   - `spatial-computing/`: VisionOS, XR, Metal, Terminal Integration (6 agents)
   - `specialized/`: Orchestrator, LSP Engineer, Data Analytics (3 agents)

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

**Interactive Chat Flow**:
```
User Message → chat_session.py → Economy Context + Personality → Ollama LLM → Agent Response
                                                                                    ↓
Dashboard UI → REST /api/chat/send → server.py → chat_history.json → WebSocket /ws/chat → Live Updates
```

**Deployment Pipeline**:
```
Git Push → GitHub Actions (.github/workflows/deploy.yml) → CI Tests → Fly.io Deploy → Post-Deploy Script → Live Dashboard
```

## Key Design Decisions

1. **Immutable Snapshots**: `EconomySnapshot` freezes state at a point in time (uses dataclasses with `frozen=True` where appropriate)

2. **Dashboard JSON Schema**: Six files expected by `office-ui.html`:
   - `treasury.json`: Balance, transactions, burn rate
   - `agent-roster.json`: Agent list with productivity metrics
   - `projects.json`: Project pipeline with stages
   - `impact-ledger.json`: Historical impact records
   - `orchestrator-status.json`: Orchestrator health metrics
   - `customer-market.json`: Customer and market data

3. **CEO Discovery Integration**: FastAPI reads JSON sessions from `.claude-flow/discovery-sessions/` and broadcasts over WebSocket (`/ws/ceo`)

4. **Local-First Autonomous Agents**: Uses Ollama for zero-API-key execution with specialized personalities for task routing

5. **Two-Way Real-Time Chat**:
   - REST endpoints for sending/receiving messages
   - WebSocket for live chat updates to all connected clients
   - Persistent storage in `chat_history.json`
   - Economy-aware context injection for grounded responses

6. **Continuous Integration & Deployment**:
   - GitHub Actions runs on every push/PR: Black formatting, flake8 linting, pytest
   - Automated deployment to Fly.io on main branch pushes
   - Post-deployment script (`scripts/fly_post_deploy.py`) initializes dashboard data
   - Environment-based authentication via secrets (AUTH_USERNAME, AUTH_PASSWORD)

## Testing Strategy

- **Engine tests** (`becoin_economy/tests/`): Verify transaction logic, treasury safety, project lifecycle
  - `test_engine_transactions.py`: Core economy operations, treasury safety, project state transitions
  - `test_stress_simulation.py`: Randomized operations to prove invariants hold under load
  - `test_exporter.py`: Ensure JSON payloads are serializable and dashboard-compatible
  - Uses `conftest.py` for shared fixtures (sample treasuries, agents, projects)

- **Dashboard tests** (`dashboard/tests/`): Full API coverage with async testing
  - `test_server.py`: Basic server health and initialization
  - `test_api_endpoints.py`: REST endpoints for CEO data, status, proposals, patterns
  - `test_chat.py`: Chat message persistence, history retrieval, message formatting
  - `test_websocket.py`: WebSocket connections, broadcasting, client management
  - `test_data_bridge.py`: Discovery session loading, data parsing, session history
  - Uses `pytest-asyncio` for async endpoint testing
  - Mock fixtures in `dashboard/tests/fixtures/`

- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Runs on every push and pull request
  - Python 3.12 with pip caching for speed
  - Black formatting check (enforces code style)
  - flake8 linting (catches code quality issues)
  - pytest on `becoin_economy` module (core functionality)
  - Must pass before PR can be merged

All tests must pass before merging (`pytest` from repo root).

## Environment Variables

**Dashboard Configuration**:
- `AUTH_USERNAME`: HTTP Basic Auth username (optional, disables auth if unset)
- `AUTH_PASSWORD`: HTTP Basic Auth password (optional, disables auth if unset)
- `DISCOVERY_SESSIONS_PATH`: Path to discovery sessions (default: `../.claude-flow/discovery-sessions`)
- `CEO_DASHBOARD_WS_POLL_INTERVAL`: WebSocket polling interval in seconds (default: `5`)

**Deployment** (Fly.io secrets):
- Set via `fly secrets set AUTH_USERNAME="..." AUTH_PASSWORD="..."`
- Secrets are encrypted and injected at runtime
- See `DEPLOYMENT.md` for full deployment guide

**Local Development**:
- Copy `.env.example` to `.env` for local configuration
- Dashboard runs without auth by default (shows warning)
- Enable auth by setting both USERNAME and PASSWORD

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

### Using the Interactive Chat System
1. Ensure Ollama is running (`./autonomous_agents/setup_autonomous_agents.sh` for first-time setup)
2. Start chat session with desired personality:
   ```python
   from autonomous_agents.chat_session import AgentChatSession

   session = AgentChatSession(personality_name="frontend-developer")
   session.interact()  # starts CLI loop
   ```
3. Chat interface automatically injects economy context for grounded responses
4. Use `--message` flag for one-off queries without interactive loop
5. Chat history persists in `dashboard/chat_history.json` when using dashboard endpoints

### Deploying to Production
1. Ensure all tests pass: `pytest`
2. Commit changes to main branch
3. GitHub Actions automatically:
   - Runs CI checks (black, flake8, pytest)
   - Deploys to Fly.io if CI passes
   - Runs post-deployment script to initialize data
4. Monitor deployment: `fly logs` or check dashboard at deployed URL
5. Manual deployment: `fly deploy` (requires Fly CLI and authentication)

## Dependencies

**Dashboard** (`dashboard/requirements.txt`):
- `fastapi==0.109.0` - REST and WebSocket API framework
- `uvicorn[standard]==0.27.0` - ASGI server with WebSocket support
- `websockets==12.0` - WebSocket protocol implementation
- `pydantic==2.5.3`, `pydantic-settings==2.1.0` - Data validation and settings management
- `pytest==7.4.4`, `pytest-asyncio==0.23.3` - Testing framework with async support
- `httpx==0.26.0` - Async HTTP client for testing
- `anthropic==0.18.1` - Claude API integration (for future features)
- `python-multipart==0.0.6` - Form data parsing
- `python-dateutil==2.8.2` - Date/time utilities

**Development Tools** (installed separately):
- `black` - Code formatter (line-length: 88, target: py312)
- `flake8` - Linting (configured via `.flake8`)
- `pytest` - Test runner

**Autonomous Agents**:
- Ollama running locally with `qwen2.5-coder:7b` model
- Setup via `./autonomous_agents/setup_autonomous_agents.sh`
- Requires internet connection for initial model download (~4.7GB)

**Python Version**: 3.12 (as specified in CI/CD and pyproject.toml)

## File Locations

**Core Implementation**:
- Economy engine: `becoin_economy/` (models, engine, exporter)
- Dashboard backend: `dashboard/server.py`, `ceo_data_bridge.py`, `websocket_manager.py`
- Dashboard frontend: `dashboard/office-ui.html`
- Autonomous orchestrator: `autonomous_agents/orchestrator.py`
- Chat system: `autonomous_agents/chat_session.py`, `autonomous_agents/economy_context.py`

**Tests & Quality**:
- Engine tests: `becoin_economy/tests/` (test_engine_transactions, test_stress_simulation, test_exporter)
- Dashboard tests: `dashboard/tests/` (test_server, test_api_endpoints, test_chat, test_websocket, test_data_bridge)
- Test fixtures: `dashboard/tests/fixtures/`, `becoin_economy/tests/conftest.py`
- CI/CD workflows: `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`
- Code style config: `.flake8`, `pyproject.toml` (Black settings)

**Data & Configuration**:
- Implementation plans: `docs/plans/` (markdown format)
- Discovery sessions: `.claude-flow/discovery-sessions/` (JSON files)
- Dashboard JSON data: `dashboard/becoin-economy/` (treasury, agents, projects, impact-ledger, orchestrator-status, customer-market)
- Chat history: `dashboard/chat_history.json` (auto-created)
- LLM config: `autonomous_agents/config/models.json`
- Execution logs: `autonomous_agents/logs/execution_*.log`

**Agent Personalities** (51 total):
- Engineering: `engineering/` (7 agents)
- Design: `design/` (6 agents)
- Marketing: `marketing/` (8 agents)
- Product: `product/` (3 agents)
- Project Management: `project-management/` (5 agents)
- Testing: `testing/` (7 agents)
- Support: `support/` (6 agents)
- Spatial Computing: `spatial-computing/` (6 agents)
- Specialized: `specialized/` (3 agents)
- Personality loader: `autonomous_agents/personalities/loader.py`

**Deployment & Scripts**:
- Dockerfile: Multi-stage Python 3.11 build
- Fly.io config: `fly.toml`
- Post-deployment: `scripts/fly_post_deploy.py`
- Service setup: `install_service.sh`, `becoin-autonomous.service`
- Startup script: `autonomous_startup.sh`, `post_deploy.sh`

**Documentation**:
- Project overview: `README.md`
- This file: `CLAUDE.md`
- Contributing guide: `CONTRIBUTING.md`
- Deployment guide: `DEPLOYMENT.md`
- Troubleshooting: `TROUBLESHOOTING.md`
- Autonomous setup: `AUTONOMOUS_SETUP.md`
- Deployment status: `DEPLOYMENT_STATUS.md`

## API Endpoints Reference

### CEO Discovery Endpoints (REST)
- `GET /api/ceo/status` - Latest discovery session overview (executive summary, active proposals count)
- `GET /api/ceo/proposals?min_roi={float}` - Filter proposals by minimum ROI threshold
- `GET /api/ceo/patterns?type={pattern_type}` - Operational patterns filtered by type
- `GET /api/ceo/pain-points` - Aggregated operational pain points and blockers
- `GET /api/ceo/history` - List of all discovery session summaries with timestamps

### Chat Endpoints (REST)
- `POST /api/chat/send` - Send message to agent (body: `{type, content, target_agent, sender}`)
- `GET /api/chat/history?limit={int}` - Retrieve chat history (default limit: 50)

### WebSocket Endpoints
- `WS /ws/ceo` - Live updates for discovery sessions (broadcasts proposals, patterns, status changes)
- `WS /ws/chat` - Real-time chat updates (broadcasts new messages to all connected clients)

### Static Files
- `GET /` - Serves `office-ui.html` dashboard
- `GET /becoin-economy/{filename}.json` - Dashboard data files (treasury, agent-roster, projects, etc.)

### Authentication
- All endpoints support HTTP Basic Auth when `AUTH_USERNAME` and `AUTH_PASSWORD` are set
- WebSocket connections use query parameter auth: `?username=...&password=...`
- Returns 401 Unauthorized if credentials are invalid when auth is enabled

## Development Best Practices

### Code Style & Quality
1. **Always run Black before committing**: `black .` (enforces 88-char line length, Python 3.12)
2. **Check linting**: `flake8 .` (must pass with zero errors)
3. **Run tests locally**: `pytest` or `pytest -v` for verbose output
4. **Use type hints**: Models use dataclasses, API uses Pydantic models
5. **Keep functions small**: Follow single responsibility principle
6. **Write docstrings**: All public functions/classes should have clear docstrings

### Testing Guidelines
1. **Test coverage required**: All new features must include tests
2. **Use async fixtures**: Dashboard tests require `pytest-asyncio` and async fixtures
3. **Mock external dependencies**: Use `conftest.py` fixtures for economy instances, mock Ollama
4. **Test edge cases**: Especially for treasury operations (negative balances, insufficient funds)
5. **Verify WebSocket behavior**: Test connection, disconnection, and broadcast scenarios
6. **Test authentication**: Both with and without credentials, valid and invalid

### Economy Engine Rules
1. **Never mutate snapshots**: EconomySnapshot should be immutable after creation
2. **Always check treasury balance**: Before any deduction, verify funds available
3. **Record all transactions**: Every financial operation must create a Transaction record
4. **Follow project lifecycle**: `pipeline → active → completed/paused` (no skipping)
5. **Maintain chronological order**: Transactions must be time-ordered
6. **Raise specific exceptions**: Use `InsufficientFundsError`, `UnknownProjectError`, `UnknownAgentError`

### Dashboard Development
1. **Use WebSocket for live updates**: Don't poll REST endpoints unnecessarily
2. **Handle disconnections gracefully**: Implement reconnection logic with exponential backoff
3. **Validate all inputs**: Use Pydantic models for request/response validation
4. **Store chat persistently**: Write to `chat_history.json` after each message
5. **Use async/await properly**: FastAPI endpoints should be async for WebSocket and I/O operations
6. **Log important events**: Use `logger.info()` for operations, `logger.warning()` for issues

### Autonomous Agents
1. **Test with --dry-run first**: Always validate plan parsing before execution
2. **Monitor logs during execution**: Use `monitor.py -f` to catch issues early
3. **Keep plans focused**: One task per section, clear file paths and code examples
4. **Use appropriate personalities**: Match agent specialty to task type
5. **Inject economy context**: Chat sessions should include economy snapshot for grounded responses
6. **Handle LLM failures gracefully**: Retry on network errors, validate LLM outputs

## Common Pitfalls & Solutions

### Problem: Tests failing with "ModuleNotFoundError"
**Solution**: Run pytest from repository root, not from subdirectories. Ensure `__init__.py` exists in module directories.

### Problem: WebSocket connections dropping
**Solution**: Implement ping/pong heartbeat in client. Server uses `WS_POLL_INTERVAL` for status checks. Check `ws_manager.py` for connection management.

### Problem: Chat history not persisting
**Solution**: Verify `chat_history.json` is writable. Check file permissions and that `chat_lock` is properly acquired before writes.

### Problem: Dashboard shows stale data
**Solution**: Regenerate JSON files using `build_dashboard_payload()`. Check that FastAPI is serving from correct directory. Verify no caching issues in browser.

### Problem: Ollama not responding
**Solution**: Check if Ollama is running (`curl http://localhost:11434/api/tags`). Restart with `ollama serve`. Verify model is downloaded (`ollama list`).

### Problem: Fly.io deployment fails
**Solution**: Check `fly logs` for errors. Verify secrets are set (`fly secrets list`). Ensure `Dockerfile` builds locally (`docker build .`). Check `fly.toml` configuration.

### Problem: CI pipeline failing on Black/flake8
**Solution**: Run `black .` locally to auto-format. Check `.flake8` config for ignored rules. Fix linting errors one by one with `flake8 --show-source`.

### Problem: Treasury balance goes negative
**Solution**: This should NEVER happen. If it does, there's a bug in the engine. Check that all deduction methods call `_check_sufficient_funds()` before modifying balance. Add tests to reproduce and fix.

## Quick Reference Commands

```bash
# Development
pytest                                    # Run all tests
pytest -v dashboard/tests/test_chat.py    # Run specific test file with verbose output
black .                                   # Auto-format all Python files
flake8 .                                  # Check linting
uvicorn dashboard.server:app --reload    # Start dashboard server

# Autonomous Agents
./autonomous_agents/setup_autonomous_agents.sh           # One-time setup
python3 autonomous_agents/orchestrator.py PLAN --dry-run # Preview execution
python3 autonomous_agents/orchestrator.py PLAN           # Execute plan
python3 autonomous_agents/monitor.py -f                  # Monitor logs
python3 autonomous_agents/chat_session.py                # Interactive chat

# Deployment
fly deploy                               # Deploy to Fly.io
fly logs                                 # View deployment logs
fly status                               # Check app status
fly secrets set KEY=VALUE                # Set environment secret

# Debugging
curl http://localhost:3000/api/ceo/status                    # Test CEO endpoint
curl http://localhost:11434/api/tags                         # Check Ollama status
git log --oneline --graph --decorate --all | head -20        # View recent commits
```

## Architecture Decision Records (ADRs)

### Why Ollama instead of cloud LLMs?
- **Zero API costs**: No per-token charges for development
- **Privacy**: Code never leaves local machine
- **Offline capable**: Works without internet after model download
- **Fast iteration**: No rate limits or network latency

### Why FastAPI over Flask?
- **Native async support**: Critical for WebSocket and concurrent requests
- **Automatic OpenAPI docs**: Built-in API documentation at `/docs`
- **Pydantic validation**: Type-safe request/response handling
- **Modern Python**: Uses Python 3.12 features, type hints throughout

### Why Fly.io for deployment?
- **Simple deployment**: `fly deploy` handles everything
- **Secrets management**: Built-in encrypted secrets
- **Auto-scaling**: Machines start/stop based on traffic
- **WebSocket support**: Works with long-lived connections
- **Free tier**: Suitable for demos and small deployments

### Why immutable snapshots?
- **Reproducibility**: Can replay economy state at any point in time
- **Testing**: Easy to create fixtures with known states
- **Debugging**: Snapshots capture exact state for bug reports
- **Audit trail**: Complete history of economy evolution

### Why 51 specialized agents?
- **Task routing**: Different tasks need different expertise
- **Personality consistency**: Each agent has distinct voice and approach
- **Parallel execution**: Multiple agents can work simultaneously
- **Extensibility**: Easy to add new agents for new domains
- **Real-world modeling**: Mirrors actual startup team structure
