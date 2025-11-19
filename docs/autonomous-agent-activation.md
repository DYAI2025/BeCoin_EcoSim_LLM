# Autonomous Agent Installation & Activation Guide

This guide captures how to bring the BeCoin autonomous agents online, configure them,
and understand the engagement rituals they follow the moment they wake up.

## 1. Installation Pipeline

1. **One-click bootstrap** – Run `./autonomous_agents/setup_autonomous_agents.sh` to
   install Ollama, download the Qwen2.5-Coder 7B model, load all 51 personalities,
   and verify the environment before any plan runs. 【F:autonomous_agents/README.md†L40-L75】
2. **Manual setup scripts (optional)** – Each phase lives in
   `autonomous_agents/setup/` so you can reinstall or troubleshoot individual steps
   such as `install_ollama.sh`, `download_models.sh`, or `test_model.sh`. 【F:autonomous_agents/README.md†L15-L35】
3. **Runbooks for execution & monitoring** – After setup you can dry-run or execute
   any Markdown plan with `python3 autonomous_agents/orchestrator.py <plan.md>` and
   tail progress via `python3 autonomous_agents/monitor.py -f`. 【F:autonomous_agents/README.md†L52-L75】

## 2. Configuration & Model Tuning

* All LLM-specific settings live in `autonomous_agents/config/models.json` so
  operators can swap models, endpoints, or decoding parameters without touching the
  orchestrator. 【F:autonomous_agents/README.md†L136-L159】
* The default configuration points at a local Ollama endpoint with
  `qwen2.5-coder:7b`, includes a fallback model, and exposes temperature/`top_p`
  knobs for determinism vs. creativity. 【F:autonomous_agents/config/models.json†L1-L9】
* Personality loading pulls 51 specialized prompts from Agency_of_Agents and caches
  them automatically, ensuring every task is routed to the right specialist without
  extra configuration. 【F:autonomous_agents/README.md†L123-L135】

## 3. Activation & User-First Behaviors

When `orchestrator.py` runs, it now performs an activation briefing **before** any
code generation starts:

1. **Prototype interview kickoff** – The orchestrator logs that agents will reach out
   for a first interview or prototype pitch to keep the stakeholder enthusiastic
   about the idea. 【F:autonomous_agents/orchestrator.py†L257-L314】
2. **Permission requests** – If the session is interactive, the CLI explicitly asks
   whether agents may review local files, Google Drive assets, and email threads,
   storing each answer in the activation context. Non-interactive sessions get a
   reminder to capture those approvals manually. 【F:autonomous_agents/orchestrator.py†L269-L321】
3. **Enthusiasm and research cues** – The activation context records the prototype
   focus plus the tone that should excite the user, then the execution loop reiterates
   those cues and lists which data surfaces were approved so every task stays aligned
   with the stakeholder conversation. 【F:autonomous_agents/orchestrator.py†L528-L552】

These rituals make it clear that every autonomous run begins with human-aligned
intent, explicit data permissions, and a promise to make the user feel energized about
what comes next.
