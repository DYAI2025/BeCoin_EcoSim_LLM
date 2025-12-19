# Autonomous Agents Setup

This directory contains setup scripts for the autonomous agent system.

## Quick Start

Run the main setup script:

```bash
./setup_autonomous_agents.sh
```

## Manual Installation

If the automatic setup fails, follow these steps:

### 1. Install Ollama

```bash
cd autonomous_agents/setup
chmod +x install_ollama.sh
./install_ollama.sh
```

### 2. Verify Installation

```bash
chmod +x verify_ollama.sh
./verify_ollama.sh
```

### 3. Download Model

```bash
ollama pull qwen2.5-coder:7b
```

### 4. Run Orchestrator

```bash
cd ../..
python3 autonomous_agents/orchestrator.py
```

## Troubleshooting

### Ollama service not starting

- Linux: `systemctl --user start ollama`
- macOS: `ollama serve &`

### Model download fails

- Check disk space: `df -h`
- Retry: `ollama pull qwen2.5-coder:7b`

### Permission denied errors

- Make scripts executable: `chmod +x *.sh`
