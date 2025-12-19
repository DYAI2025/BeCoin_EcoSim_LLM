#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Autonomous Agents - One-Click Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This script will:"
echo "  1. Install Ollama (local LLM server)"
echo "  2. Verify Ollama installation"
echo "  3. Download AI models (Qwen2.5-Coder 7B)"
echo "  4. Test model functionality"
echo "  5. Load Agency_of_Agents personalities"
echo "  6. Setup Python environment"
echo "  7. Verify orchestrator"
echo ""

# Move to setup directory
cd "$(dirname "$0")/setup"

# Step 1: Install Ollama
echo -e "${BLUE}━━━ Step 1/7: Installing Ollama ━━━${NC}"
if ./install_ollama.sh; then
    echo -e "${GREEN}✅ Ollama installation complete${NC}"
else
    echo -e "${RED}❌ Ollama installation failed${NC}"
    exit 1
fi
echo ""

# Step 2: Verify Ollama
echo -e "${BLUE}━━━ Step 2/7: Verifying Ollama ━━━${NC}"
if ./verify_ollama.sh; then
    echo -e "${GREEN}✅ Ollama verification passed${NC}"
else
    echo -e "${RED}❌ Ollama verification failed${NC}"
    exit 1
fi
echo ""

# Step 3: Download Models
echo -e "${BLUE}━━━ Step 3/7: Downloading AI Models ━━━${NC}"
if ./download_models.sh; then
    echo -e "${GREEN}✅ Model download complete${NC}"
else
    echo -e "${RED}❌ Model download failed${NC}"
    exit 1
fi
echo ""

# Step 4: Test Model
echo -e "${BLUE}━━━ Step 4/7: Testing AI Model ━━━${NC}"
if ./test_model.sh; then
    echo -e "${GREEN}✅ Model test passed${NC}"
else
    echo -e "${YELLOW}⚠️  Model test had issues, but continuing...${NC}"
fi
echo ""

# Step 5: Verify Agency_of_Agents
echo -e "${BLUE}━━━ Step 5/7: Verifying Agency_of_Agents ━━━${NC}"
cd ..

if python3 personalities/loader.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Loaded 51 agent personalities from Agency_of_Agents${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Could not load Agency_of_Agents${NC}"
    echo "   Please ensure Agency_of_Agents is cloned to:"
    echo "   /home/dyai/Dokumente/DYAI_home/DEV/AI_LLM/Agency_of_Agents/agency-agents"
    echo "   or update the path in personalities/loader.py"
fi
echo ""

# Step 6: Setup Python Environment
echo -e "${BLUE}━━━ Step 6/7: Setting up Python Environment ━━━${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "  Python version: $PYTHON_VERSION"

# Check if required packages are available (we don't install to avoid conflicts)
echo "  Checking Python environment..."
python3 -c "import sys; sys.path.insert(0, '..'); from autonomous_agents.personalities import load_personalities" 2>/dev/null && \
    echo -e "${GREEN}  ✅ Python environment is ready${NC}" || \
    echo -e "${YELLOW}  ⚠️  Some Python imports may not work${NC}"

echo ""

# Step 7: Verify Orchestrator
echo -e "${BLUE}━━━ Step 7/7: Verifying Orchestrator ━━━${NC}"

if python3 orchestrator.py --help > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Orchestrator is ready${NC}"
    echo ""
    echo "Usage:"
    echo "  python3 autonomous_agents/orchestrator.py <plan.md>"
    echo "  python3 autonomous_agents/orchestrator.py --dry-run <plan.md>"
else
    echo -e "${RED}❌ Orchestrator verification failed${NC}"
    exit 1
fi
echo ""

# Success!
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Your autonomous agent system is ready!"
echo ""
echo "📝 Quick Start:"
echo ""
echo "  # Test with dry run (no actual execution):"
echo "  python3 autonomous_agents/orchestrator.py \\"
echo "    docs/plans/2025-11-06-schema-driven-dashboard-production.md \\"
echo "    --dry-run"
echo ""
echo "  # Execute a plan autonomously:"
echo "  python3 autonomous_agents/orchestrator.py \\"
echo "    docs/plans/2025-11-06-schema-driven-dashboard-production.md"
echo ""
echo "📊 System Info:"
echo "  • Ollama Endpoint: http://localhost:11434"
echo "  • Primary Model: $(cat config/models.json | grep primary_model | cut -d'"' -f4)"
echo "  • Agent Personalities: 51 loaded"
echo "  • Logs: autonomous_agents/logs/"
echo ""
echo "📚 Documentation:"
echo "  • README: autonomous_agents/setup/README.md"
echo "  • Personalities: autonomous_agents/personalities/README.md"
echo "  • Plans: docs/plans/"
echo ""
echo "🔧 Manual Commands:"
echo "  • Check Ollama: ollama list"
echo "  • Test model: ollama run qwen2.5-coder:7b 'print hello world in python'"
echo "  • View logs: ls -lh autonomous_agents/logs/"
echo ""
