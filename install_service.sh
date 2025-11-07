#!/bin/bash

# Install BeCoin Autonomous Service

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🔧 Installing BeCoin Autonomous Service${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Copy service file
echo -e "${BLUE}[1/4] Installing systemd service...${NC}"
sudo cp "$PROJECT_DIR/becoin-autonomous.service" /etc/systemd/system/
sudo systemctl daemon-reload
echo -e "${GREEN}  ✓ Service file installed${NC}"
echo ""

# Enable service
echo -e "${BLUE}[2/4] Enabling service...${NC}"
sudo systemctl enable becoin-autonomous.service
echo -e "${GREEN}  ✓ Service enabled (will start on boot)${NC}"
echo ""

# Start service
echo -e "${BLUE}[3/4] Starting service...${NC}"
sudo systemctl start becoin-autonomous.service
sleep 2
echo -e "${GREEN}  ✓ Service started${NC}"
echo ""

# Check status
echo -e "${BLUE}[4/4] Checking status...${NC}"
if systemctl is-active --quiet becoin-autonomous.service; then
    echo -e "${GREEN}  ✓ Service is running${NC}"
else
    echo -e "${YELLOW}  ⚠ Service may not be running properly${NC}"
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo ""
echo -e "  ${GREEN}sudo systemctl status becoin-autonomous${NC}  - Check service status"
echo -e "  ${GREEN}sudo systemctl stop becoin-autonomous${NC}    - Stop service"
echo -e "  ${GREEN}sudo systemctl start becoin-autonomous${NC}   - Start service"
echo -e "  ${GREEN}sudo systemctl restart becoin-autonomous${NC} - Restart service"
echo -e "  ${GREEN}sudo journalctl -u becoin-autonomous -f${NC}  - View live logs"
echo ""
echo -e "${YELLOW}Dashboard:${NC} https://becoin-ecosim-llm.fly.dev/"
echo ""
