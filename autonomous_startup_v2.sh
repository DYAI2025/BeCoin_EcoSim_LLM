#!/bin/bash

# BeCoin Economy v2.0 - Autonomous Startup Script
# This script runs the complete autonomous economy simulation

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
echo -e "${GREEN}💰 BeCoin Economy v2.0 - Autonomous System${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. Check Ollama
echo -e "${BLUE}[1/4] Checking Ollama LLM...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Ollama is running${NC}"
    curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; models=json.load(sys.stdin).get('models',[]); print(f'  ✓ {len(models)} models available')"
else
    echo -e "${YELLOW}  ⚠ Ollama not running (local AI disabled)${NC}"
fi

# 2. Check Economy
echo ""
echo -e "${BLUE}[2/4] Initializing Economy Engine v2.0...${NC}"

python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '.')

from becoin_economy.engine_v2 import BeCoinEconomy
from datetime import datetime

# Initialize economy
economy = BeCoinEconomy()
economy.running = True

# Save initial state
economy.export_dashboard()

print(f"  ✓ Treasury initialized: ${economy.treasury.balance}")
print(f"  ✓ Agents: {len(economy.agents)}")
print(f"  ✓ Projects: {len(economy.projects)}")
print(f"  ✓ Config: baseline_burn=${economy.BASELINE_BURN_PER_HOUR}/h, tax_rate={economy.TAX_RATE*100}%")

# Run one cycle
report = economy.advance_time(hours=1)
print(f"  ✓ First cycle completed:")
print(f"    - Agent costs: ${report['agent_payments']['total_cost']}")
print(f"    - Balance: ${report['balance_after']}")

# Show agent reports
print(f"  ✓ Agent Reports:")
for report in economy.get_agent_chat_reports():
    print(f"    - {report['agent']['name']}: {report['current_task']}")

# Save final state
economy.export_dashboard()

print(f"\n✅ Economy v2.0 is running!")
print(f"   Dashboard data: dashboard/becoin-economy/")
print(f"   Open office-ui.html in browser to view")
PYTHON_SCRIPT

# 3. Start continuous simulation
echo ""
echo -e "${BLUE}[3/4] Starting Autonomous Simulation Loop...${NC}"

python3 << 'PYTHON_LOOP'
import sys
import time
from pathlib import Path
sys.path.insert(0, '.')

from becoin_economy.engine_v2 import BeCoinEconomy

economy = BeCoinEconomy()
economy.running = True
economy.export_dashboard()

print("  ✓ Simulation loop starting...")
print("  ✓ Press Ctrl+C to stop")
print("")

cycle = 0
while economy.running:
    try:
        cycle += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Run one hour simulation
        report = economy.advance_time(hours=1)
        
        # Show status every 10 cycles
        if cycle % 10 == 0:
            balance = economy.treasury.balance
            active_agents = sum(1 for a in economy.agents.values() if a.status == 'active')
            active_projects = sum(1 for p in economy.projects.values() if p.stage == 'active')
            print(f"[{timestamp}] Cycle {cycle}: Balance=${balance}, Agents={active_agents}, Projects={active_projects}")
        
        time.sleep(5)  # 5 seconds = 1 simulated hour
        
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stopping simulation...")
        economy.running = False
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)

print("Simulation stopped.")
PYTHON_LOOP

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ BeCoin Economy v2.0 Shutdown${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
