# Release Readiness Task List

This checklist translates the current simulation, dashboard, and autonomous-agent
capabilities into release-grade requirements. Tasks are grouped so that each
stream can be owned independently but still converge on a releasable build.

## 1. Simulation Core & Treasury Safety
- [ ] Finalize starter datasets for founders, employees, and projects so QA can
      run deterministic smoke tests.
- [ ] Provide a CLI entrypoint (`python -m becoin_economy.scenarios`) that seeds
      the engine, advances time, and exports payloads for the dashboard.
- [ ] Stress-test `advance_time` against multi-day runs (>= 10k simulated hours)
      and persist randomized seeds that reproduce any failures.
- [ ] Document treasury invariants (no negative balance, chronological
      transactions, ROI sanity checks) inside `docs/` and link them from the
      README so partners know how financial safety is enforced.

## 2. Dashboard APIs & Data Bridge
- [ ] Harden `/api/ceo/*` endpoints with structured validation errors and rate
      limits for untrusted networks.
- [x] Add caching to `CEODataBridge` to avoid re-reading the same discovery file
      on every request and to smooth over short write windows.
- [x] Stream the latest discovery session snapshot to WebSocket clients so the
      UI updates even when no manual proposal events fire.
- [ ] Add synthetic fixtures for status/proposal/pattern payloads and publish
      them as part of the test suite for integrators.

## 3. Dashboard UX/UI Delivery
- [ ] Ship a single `npm run build` bundle (or equivalent) for the pixel office
      UI and document how to deploy alongside the FastAPI service.
- [ ] Add a responsive layout state for tablet screens and confirm at least one
      accessibility scan (WCAG AA color contrast + focus order).
- [ ] Provide empty/error states for each panel (treasury, proposals, patterns)
      so leadership is never looking at a blank grid.

## 4. Autonomous Execution Surface
- [ ] Package `autonomous_agents/setup_autonomous_agents.sh` as an installable
      Make target (`make setup-agents`) and add health checks for Ollama models.
- [ ] Add smoke tests that spawn a dry-run orchestrator execution on CI to catch
      plan parsing regressions early.
- [ ] Surface orchestrator health (connected agents, queue depth, last plan)
      through the dashboard so ops can see when autonomous work is blocked.

## 5. Observability, Ops, & Security
- [ ] Publish a `docker-compose.yml` (or Fly.io app manifest) showing how to run
      the API, dashboard, and file watcher together with minimal env vars.
- [ ] Pipe FastAPI access/error logs plus economy metrics into a single
      structured log stream (e.g., OpenTelemetry / OTLP exporter).
- [ ] Provide a secrets-management recipe (1Password/Bitwarden + `.env` templates)
      and document the rotating credential schedule for AUTH_USERNAME/PASSWORD.
- [ ] Define clear SLOs: dashboard median response time < 200ms, session file
      polling within 5s, economy snapshot generation < 1s.

Owning teams should update this list in their weekly cadence review. When every
checkbox is green we have a releasable, observable product that meets the CEO's
real-time monitoring expectations.
