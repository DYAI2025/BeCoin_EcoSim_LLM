# Autonomous Agents System

> 🤖 Self-executing AI agents powered by local LLMs and specialized personalities

## Overview

This autonomous agent system executes implementation plans independently using:

- **Local LLMs** via Ollama (Qwen2.5-Coder 7B)
- **51 Specialized Agent Personalities** from [Agency_of_Agents](https://github.com/msitarzewski/agency-agents)
- **Markdown-Based Plans** from `docs/plans/`
- **Automated Code Generation** with file operations
- **Real-Time Monitoring** with progress tracking

## Architecture

```
autonomous_agents/
├── orchestrator.py          # Main orchestrator with LLM integration
├── monitor.py               # Real-time execution monitor
├── setup_autonomous_agents.sh  # One-click setup script
├── setup/                   # Installation scripts
│   ├── install_ollama.sh    # Ollama installation
│   ├── verify_ollama.sh     # Verification checks
│   ├── download_models.sh   # Model download
│   ├── test_model.sh        # Model testing
│   └── README.md            # Setup documentation
├── personalities/           # Agent personality loader
│   ├── loader.py            # Loads 51 Agency_of_Agents personalities
│   ├── __init__.py
│   └── README.md
├── config/                  # Configuration files
│   └── models.json          # LLM model configuration
└── logs/                    # Execution logs
    └── execution_*.log      # Timestamped logs
```

## Quick Start

### 1. One-Click Setup

```bash
./autonomous_agents/setup_autonomous_agents.sh
```

This will:
1. ✅ Install Ollama
2. ✅ Download Qwen2.5-Coder 7B model (~4.7 GB)
3. ✅ Load 51 agent personalities
4. ✅ Verify everything works

### 2. Run Your First Autonomous Execution

```bash
# Dry run (no actual execution)
python3 autonomous_agents/orchestrator.py \
  docs/plans/2025-11-06-schema-driven-dashboard-production.md \
  --dry-run

# Actual execution
python3 autonomous_agents/orchestrator.py \
  docs/plans/2025-11-06-schema-driven-dashboard-production.md
```

### 3. Monitor Progress (Optional)

In a separate terminal:

```bash
# Follow live progress
python3 autonomous_agents/monitor.py -f

# View specific log
python3 autonomous_agents/monitor.py --log-file autonomous_agents/logs/execution_20251106_120000.log
```

## How It Works

### 1. Implementation Plans

Plans are markdown files in `docs/plans/` with this structure:

```markdown
# Plan Title

## Overview
Brief description of what will be built.

## Task 1: First Task
Description of task 1.

**File: path/to/file.py**
```python
# Code example
```

## Task 2: Second Task
...
```

### 2. Task Execution Flow

```
Plan File
    ↓
PlanParser → Extracts tasks, code snippets, files
    ↓
Orchestrator → Assigns agent personalities to tasks
    ↓
For each task:
    ↓
    Personality Loader → Gets specialized agent prompt
    ↓
    OllamaClient → Generates code using local LLM
    ↓
    File Operations → Applies changes to codebase
    ↓
    Testing → Runs tests if applicable
    ↓
    Logging → Records progress
```

### 3. Agent Personalities

The system automatically routes tasks to specialized agents:

- **Frontend tasks** → Frontend Developer
- **Backend tasks** → Backend Architect
- **AI/ML tasks** → AI Engineer
- **Testing tasks** → QA Analyst
- **DevOps tasks** → DevOps Automator
- **General tasks** → Senior Developer

See `autonomous_agents/personalities/README.md` for the full roster of 51 agents.

## Configuration

### Model Configuration

Edit `autonomous_agents/config/models.json`:

```json
{
  "primary_model": "qwen2.5-coder:7b",
  "backup_model": "llama3.1:8b",
  "endpoint": "http://localhost:11434",
  "options": {
    "temperature": 0.2,
    "num_ctx": 8192,
    "top_p": 0.9
  }
}
```

### LLM Parameters

- **temperature**: 0.2 (low = more focused/deterministic)
- **num_ctx**: 8192 (context window size)
- **top_p**: 0.9 (nucleus sampling)

### Custom Personalities

To use custom agent personalities:

1. Clone Agency_of_Agents: `git clone https://github.com/msitarzewski/agency-agents.git`
2. Update path in `autonomous_agents/personalities/loader.py`
3. Add custom agents to any category directory

## Command Reference

### Orchestrator

```bash
# Show help
python3 autonomous_agents/orchestrator.py --help

# Dry run (shows what would happen without executing)
python3 autonomous_agents/orchestrator.py <plan.md> --dry-run

# Execute plan
python3 autonomous_agents/orchestrator.py <plan.md>
```

### Monitor

```bash
# Show help
python3 autonomous_agents/monitor.py --help

# View latest log once
python3 autonomous_agents/monitor.py

# Follow log in real-time
python3 autonomous_agents/monitor.py -f

# View specific log
python3 autonomous_agents/monitor.py --log-file <path>
```

### Ollama

```bash
# List models
ollama list

# Test model directly
ollama run qwen2.5-coder:7b "Write a Python function to reverse a string"

# Check service status
curl http://localhost:11434/api/tags
```

## Logs

### Log Format

```
[2025-11-06 12:00:00] [INFO] 📖 Loading plan from docs/plans/example.md
[2025-11-06 12:00:01] [INFO] ✅ Loaded 7 tasks
[2025-11-06 12:00:02] [INFO] 🚀 Executing Task 1: Add Error Boundaries
[2025-11-06 12:00:10] [INFO] ✅ Task 1 completed successfully
```

### Log Locations

- All logs: `autonomous_agents/logs/execution_*.log`
- Latest log: `autonomous_agents/logs/` (sorted by timestamp)

## Testing

### Test the Full System

```bash
# Run all setup tests
cd autonomous_agents/setup
./install_ollama.sh
./verify_ollama.sh
./download_models.sh
./test_model.sh

# Test personality loader
cd ..
python3 personalities/loader.py

# Test orchestrator
python3 orchestrator.py --help

# Test monitor
python3 monitor.py --help
```

### Test with Dry Run

```bash
# Test parsing and personality assignment without execution
python3 autonomous_agents/orchestrator.py \
  docs/plans/2025-11-06-autonomous-agents-one-click-setup.md \
  --dry-run
```

## Troubleshooting

### Ollama Not Running

```bash
# Linux
systemctl --user start ollama

# macOS
ollama serve &

# Check status
curl http://localhost:11434/api/tags
```

### Model Not Downloaded

```bash
# Download manually
ollama pull qwen2.5-coder:7b

# Verify
ollama list
```

### Agency_of_Agents Not Found

```bash
# Clone the repo
git clone https://github.com/msitarzewski/agency-agents.git \
  /home/dyai/Dokumente/DYAI_home/DEV/AI_LLM/Agency_of_Agents

# Or update path in personalities/loader.py
```

### Execution Fails Mid-Task

Check the log file for error messages:

```bash
# View latest log
ls -lth autonomous_agents/logs/ | head -5
tail -50 autonomous_agents/logs/execution_*.log
```

### Out of Memory

Qwen2.5-Coder 7B requires ~8GB RAM. To use a smaller model:

```bash
# Download smaller model
ollama pull qwen2.5-coder:3b

# Update config
vim autonomous_agents/config/models.json
# Change "primary_model": "qwen2.5-coder:3b"
```

## Performance

### Benchmarks

- **Setup Time**: 5-10 minutes (model download)
- **Task Execution**: 10-60 seconds per task (depends on complexity)
- **Memory Usage**: ~8GB RAM (Qwen2.5-Coder 7B)
- **Disk Space**: ~5GB (model + dependencies)

### Optimization Tips

1. **Use GPU**: If available, Ollama will automatically use GPU acceleration
2. **Increase Context**: Raise `num_ctx` in config for larger tasks
3. **Lower Temperature**: Set to 0.1 for more deterministic output
4. **Parallel Execution**: Run multiple orchestrators in different directories

## Integration

### With CI/CD

```yaml
# .github/workflows/autonomous-execution.yml
name: Autonomous Execution
on: [push]
jobs:
  execute:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Autonomous Agents
        run: ./autonomous_agents/setup_autonomous_agents.sh
      - name: Execute Plan
        run: python3 autonomous_agents/orchestrator.py docs/plans/my-plan.md
```

### With BeCoin Simulation

The orchestrator can generate code for the BeCoin simulation:

```bash
# Create a plan for new simulation features
python3 autonomous_agents/orchestrator.py \
  docs/plans/becoin-add-market-volatility.md
```

### With Schema-Driven Dashboard

Use autonomous agents to implement dashboard features:

```bash
python3 autonomous_agents/orchestrator.py \
  docs/plans/2025-11-06-schema-driven-dashboard-production.md
```

## Development

### Adding New Features

1. Create a plan in `docs/plans/`
2. Run orchestrator with `--dry-run` to verify parsing
3. Execute plan: `python3 autonomous_agents/orchestrator.py <plan.md>`
4. Monitor progress: `python3 autonomous_agents/monitor.py -f`

### Extending the Orchestrator

The orchestrator is modular. Key extension points:

- `OllamaClient`: Swap LLM provider
- `PlanParser`: Support new plan formats
- `PersonalityLoader`: Add custom personalities
- `Orchestrator._apply_file_changes()`: Custom file operations

### Testing Changes

```bash
# Test personality loading
python3 -c "from autonomous_agents.personalities import load_personalities; load_personalities()"

# Test plan parsing
python3 -c "from autonomous_agents.orchestrator import PlanParser; p = PlanParser('docs/plans/example.md'); print(len(p.parse()))"

# Test LLM connection
curl -s http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"test","stream":false}'
```

## Security Considerations

⚠️ **Important**: The orchestrator executes AI-generated code. Always:

1. **Review plans** before execution
2. **Use dry-run** first: `--dry-run`
3. **Check logs** after execution
4. **Version control** everything: `git commit` before running
5. **Sandbox** sensitive operations

## License

This autonomous agent system is part of the BeCoin EcoSim LLM project.

The Agency_of_Agents personalities are MIT licensed (© msitarzewski).

## Credits

- **Ollama**: [ollama.com](https://ollama.com)
- **Qwen2.5-Coder**: [Qwen Team](https://github.com/QwenLM/Qwen2.5-Coder)
- **Agency_of_Agents**: [msitarzewski](https://github.com/msitarzewski/agency-agents)

## Support

- **Issues**: Create issues in the GitHub repository
- **Logs**: Check `autonomous_agents/logs/` for debugging
- **Documentation**: See `docs/plans/` for examples

---

**Built with ❤️ for autonomous AI development**
