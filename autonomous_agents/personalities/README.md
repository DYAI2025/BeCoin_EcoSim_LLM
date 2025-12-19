# Agent Personalities

This module integrates the [Agency_of_Agents](https://github.com/msitarzewski/agency-agents) personality system into our autonomous agent orchestrator.

## Overview

The Agency_of_Agents project provides 51 specialized AI agent personalities across multiple categories:

- **Engineering** (7 agents): Frontend, Backend, Mobile, AI, DevOps, Prototyping, Senior Dev
- **Design** (6 agents): UI, UX, Brand, Visual Storytelling, Whimsy
- **Marketing** (8 agents): Growth, Content, Social Media, Community
- **Product** (3 agents): Sprint Planning, Research, Feedback
- **Testing** (5 agents): QA, Automation, Performance, Security
- **Support** (4 agents): Technical, Customer Success, Documentation
- **Project Management** (6 agents): Scrum, Agile, Stakeholder, Technical PM
- **Specialized** (9 agents): Legal, Financial, Data Analysis, etc.

## Usage

```python
from autonomous_agents.personalities import load_personalities

# Load all personalities
loader = load_personalities()

# List all personalities
for personality in loader.list_personalities():
    print(f"{personality.name}: {personality.description}")

# Get specific personality
ai_engineer = loader.get_personality('engineering-ai-engineer')
print(ai_engineer.full_prompt)

# Search for personalities
frontend_agents = loader.search_personalities('frontend')

# Find best match for a task
task = "Build a React dashboard with WebSocket support"
best_match = loader.get_best_match(task)
print(f"Best match: {best_match.name}")
```

## Integration with Orchestrator

The orchestrator uses personalities to:

1. **Task Routing**: Match tasks to specialized agents
2. **Prompt Engineering**: Use agent prompts as system messages
3. **Quality Assurance**: Apply agent-specific success criteria
4. **Team Composition**: Build multi-agent teams for complex tasks

## Personality Structure

Each personality includes:

- **Name**: Unique identifier
- **Description**: Brief overview of capabilities
- **Category**: Domain specialization
- **Full Prompt**: Complete personality definition with:
  - Identity & Memory
  - Core Mission
  - Critical Rules
  - Core Capabilities
  - Workflow Process
  - Communication Style
  - Success Metrics

## Testing

Run the loader test:

```bash
python3 autonomous_agents/personalities/loader.py
```

This will:
- Load all 51 personalities
- Display statistics
- Test personality matching
- Create a cache file

## Cache

The loader creates a JSON cache at `autonomous_agents/config/personalities_cache.json` for faster loading. The cache is automatically regenerated when needed.

## Requirements

- Python 3.8+
- Agency_of_Agents repository located at one of:
  - `/home/dyai/Dokumente/DYAI_home/DEV/AI_LLM/Agency_of_Agents/agency-agents`
  - `~/Agency_of_Agents/agency-agents`
  - `../../../Agency_of_Agents/agency-agents`

Or specify a custom path:

```python
loader = load_personalities('/path/to/agency-agents')
```
