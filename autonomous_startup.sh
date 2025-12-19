#!/bin/bash

# BeCoin Autonomous Startup Script
# This script starts the autonomous economy simulation

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🤖 BeCoin Autonomous Economy - Startup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. Check Ollama
echo -e "${BLUE}[1/4] Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}  ⚠ Ollama not running, starting...${NC}"
    systemctl --user start ollama 2>/dev/null || ollama serve > /dev/null 2>&1 &
    sleep 3
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Ollama started${NC}"
    else
        echo -e "${RED}  ✗ Failed to start Ollama${NC}"
        exit 1
    fi
fi

# 2. Check Model
echo -e "${BLUE}[2/4] Checking AI Model...${NC}"
if ollama list | grep -q "qwen2.5-coder:7b"; then
    echo -e "${GREEN}  ✓ Model qwen2.5-coder:7b available${NC}"
else
    echo -e "${YELLOW}  ⚠ Model not found, downloading...${NC}"
    ollama pull qwen2.5-coder:7b
    echo -e "${GREEN}  ✓ Model downloaded${NC}"
fi

# 3. Generate Dashboard Data
echo -e "${BLUE}[3/4] Generating Economy Data...${NC}"
python3 << 'PYTHON_SCRIPT'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from becoin_economy import BecoinEconomy, Agent, Project, Treasury, build_dashboard_payload

    # Create economy instance
    treasury = Treasury(start_capital=10000, balance=8500)

    agents = [
        Agent(id="agent-001", name="Frontend Developer", role="Frontend", status="active", equity_share=0.25),
        Agent(id="agent-002", name="Backend Architect", role="Backend", status="active", equity_share=0.25),
        Agent(id="agent-003", name="AI Engineer", role="AI/ML", status="idle", equity_share=0.25),
        Agent(id="agent-004", name="DevOps Automator", role="DevOps", status="active", equity_share=0.25),
    ]

    projects = [
        Project(id="proj-001", name="Dashboard Redesign", stage="active", cost=2000, value=3000, impact_score=85, team=["agent-001"]),
        Project(id="proj-002", name="API Integration", stage="completed", cost=1500, value=2500, impact_score=92, team=["agent-002"]),
        Project(id="proj-003", name="CI/CD Pipeline", stage="active", cost=1800, value=2700, impact_score=78, team=["agent-004"]),
        Project(id="proj-004", name="LLM Integration", stage="pipeline", cost=2500, value=4000, impact_score=95, team=[]),
    ]

    economy = BecoinEconomy(
        treasury=treasury,
        agents=agents,
        projects=projects,
        baseline_hourly_burn=120.0
    )

    # Generate dashboard payload
    payload = build_dashboard_payload(economy)

    # Save to dashboard directory
    output_dir = Path("dashboard/becoin-economy")
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, data in payload.items():
        output_path = output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    print(f"  ✓ Generated {len(payload)} dashboard files")

except Exception as e:
    print(f"  ⚠ Could not generate economy data: {e}")
    print("    Using existing sample data")
PYTHON_SCRIPT
echo ""

# 4. Start Continuous Simulation
echo -e "${BLUE}[4/4] Starting Autonomous Simulation...${NC}"
echo -e "${GREEN}  ✓ System ready${NC}"
echo ""
echo -e "${YELLOW}📊 Dashboard:${NC} https://becoin-ecosim-llm.fly.dev/"
echo -e "${YELLOW}🔧 Local API:${NC} http://localhost:3000/api/status"
echo -e "${YELLOW}📁 Logs:${NC} autonomous_agents/logs/"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start continuous simulation loop
echo -e "${GREEN}Starting continuous simulation loop...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Run continuous economy simulation
python3 << 'PYTHON_LOOP'
import time
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from becoin_economy import BecoinEconomy, Agent, Project, Treasury, build_dashboard_payload

print("🔄 Autonomous economy simulation running...")
print("")

# Initialize economy
treasury = Treasury(start_capital=10000, balance=8500)
agents = [
    Agent(id="agent-001", name="Frontend Developer", role="Frontend", status="active", equity_share=0.25),
    Agent(id="agent-002", name="Backend Architect", role="Backend", status="active", equity_share=0.25),
    Agent(id="agent-003", name="AI Engineer", role="AI/ML", status="idle", equity_share=0.25),
    Agent(id="agent-004", name="DevOps Automator", role="DevOps", status="active", equity_share=0.25),
]
projects = [
    Project(id="proj-001", name="Dashboard Redesign", stage="active", cost=2000, value=3000, impact_score=85, team=["agent-001"]),
    Project(id="proj-002", name="API Integration", stage="completed", cost=1500, value=2500, impact_score=92, team=["agent-002"]),
    Project(id="proj-003", name="CI/CD Pipeline", stage="active", cost=1800, value=2700, impact_score=78, team=["agent-004"]),
    Project(id="proj-004", name="LLM Integration", stage="pipeline", cost=2500, value=4000, impact_score=95, team=[]),
]

economy = BecoinEconomy(treasury=treasury, agents=agents, projects=projects, baseline_hourly_burn=120.0)
cycle = 0

output_dir = Path("dashboard/becoin-economy")
output_dir.mkdir(parents=True, exist_ok=True)

try:
    while True:
        cycle += 1
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")

        # Simulate economy tick
        print(f"[{timestamp}] Cycle {cycle}: Balance=${economy.treasury.balance:.0f}, Active Projects={len([p for p in economy.projects.values() if p.stage == 'active'])}")

        # Random events (simulating agent activity)
        if random.random() < 0.2:  # 20% chance of project completion
            active_projects = [p for p in economy.projects.values() if p.stage == "active"]
            if active_projects:
                proj = random.choice(active_projects)
                print(f"    ├─ Working on: {proj.name}")

                # Complete project with value
                try:
                    economy.complete_project(proj.id)
                    print(f"    └─ ✓ {proj.name} completed! Value: ${proj.value}")
                except Exception as e:
                    print(f"    └─ ⚠ Could not complete project: {e}")

        # Advance time (burn treasury)
        economy.advance_time(hours=1)

        # Export dashboard data
        payload = build_dashboard_payload(economy)
        for filename, data in payload.items():
            with open(output_dir / filename, 'w') as f:
                json.dump(data, f, indent=2)

        # Wait for next cycle (5 seconds = 1 simulated hour)
        time.sleep(5)

except KeyboardInterrupt:
    print("\n\n🛑 Simulation stopped by user")
    print(f"Final balance: ${economy.treasury.balance:.2f}")
    print(f"Total cycles: {cycle}")
PYTHON_LOOP
