# Autonomous Agent Installation & Activation Guide

This guide captures how to bring the BeCoin autonomous agents online, configure
them, and understand the activation rituals they run before touching the codebase.

## 1. Installation Pipeline

1. **One-click bootstrap** – Run `./autonomous_agents/setup_autonomous_agents.sh` to
   install Ollama, download the Qwen2.5-Coder 7B model, load all 51 personalities,
   and verify the environment before any plan runs.
2. **Targeted setup scripts** – Each phase lives in `autonomous_agents/setup/` so you
   can reinstall or troubleshoot specific steps like `install_ollama.sh`,
   `download_models.sh`, or `test_model.sh` without re-running the full bootstrap.
3. **Runbooks for execution & monitoring** – After setup you can dry-run or execute
   any Markdown plan with `python3 autonomous_agents/orchestrator.py <plan.md>` and
   tail progress via `python3 autonomous_agents/monitor.py -f`.

## 2. Configuration & Model Tuning

* LLM settings live in `autonomous_agents/config/models.json`, making it easy to swap
  models, endpoints, or decoding parameters without changing code.
* The default configuration points at a local Ollama endpoint with
  `qwen2.5-coder:7b`, includes a fallback model, and exposes temperature/`top_p`
  knobs for determinism vs. creativity.
* Personality loading pulls 51 specialized prompts from Agency_of_Agents and caches
  them automatically so every task is routed to the right specialist.

## 3. Activation & User-First Behaviors

When `orchestrator.py` runs, it performs an activation briefing **before** any code
changes are generated:

1. **Prototype interview kickoff** – The orchestrator logs that agents will reach out
   for a first interview or prototype pitch so the user stays energized about the
   idea.
2. **Permission requests** – Interactive runs ask whether agents may review local
   files, Google Drive assets, and email threads; the answers are saved in the
   activation context. Non-interactive runs record that permissions are pending so
   humans can capture approvals manually.
3. **Enthusiasm and research cues** – The activation context stores the prototype
   focus plus the tone that should excite the user. The execution loop reiterates
   those cues and lists which data surfaces were approved so every task stays aligned
   with the stakeholder conversation.

These rituals make it clear that every autonomous run begins with human-aligned
intent, explicit data permissions, and a promise to make the user feel energized
about what comes next.
