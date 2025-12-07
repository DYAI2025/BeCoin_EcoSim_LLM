#!/bin/bash

# BeCoin Post-Deployment Script
# This script automatically starts the BeCoin system after deployment
#
# Usage:
#   ./post_deploy.sh              # Run both startup and service installation
#   ./post_deploy.sh --startup    # Only run autonomous_startup.sh (foreground)
#   ./post_deploy.sh --service    # Only install and start the service
#   ./post_deploy.sh --background # Start simulation in background (no service)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# Parse arguments
MODE="${1:-all}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}BeCoin Post-Deployment Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to check if running as root or with sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}Note: Service installation requires sudo privileges${NC}"
        return 1
    fi
    return 0
}

# Function to check if scripts exist
check_scripts() {
    if [ ! -f "$PROJECT_DIR/autonomous_startup.sh" ]; then
        echo -e "${RED}Error: autonomous_startup.sh not found${NC}"
        exit 1
    fi
    if [ ! -f "$PROJECT_DIR/install_service.sh" ]; then
        echo -e "${RED}Error: install_service.sh not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}Scripts found${NC}"
}

# Function to run autonomous startup in foreground
run_startup_foreground() {
    echo -e "${BLUE}[1/1] Starting BeCoin autonomous simulation (foreground)...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    exec "$PROJECT_DIR/autonomous_startup.sh"
}

# Function to run autonomous startup in background
run_startup_background() {
    echo -e "${BLUE}Starting BeCoin autonomous simulation (background)...${NC}"

    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_DIR/autonomous_agents/logs"

    # Start in background with nohup
    nohup "$PROJECT_DIR/autonomous_startup.sh" \
        > "$PROJECT_DIR/autonomous_agents/logs/startup.log" 2>&1 &

    local PID=$!
    echo "$PID" > "$PROJECT_DIR/autonomous_agents/logs/startup.pid"

    echo -e "${GREEN}Started with PID: $PID${NC}"
    echo -e "${YELLOW}Logs: $PROJECT_DIR/autonomous_agents/logs/startup.log${NC}"
    echo -e "${YELLOW}PID file: $PROJECT_DIR/autonomous_agents/logs/startup.pid${NC}"
}

# Function to install and start service
install_service() {
    echo -e "${BLUE}Installing BeCoin as systemd service...${NC}"

    if check_sudo; then
        "$PROJECT_DIR/install_service.sh"
    else
        echo -e "${YELLOW}Running with sudo...${NC}"
        sudo "$PROJECT_DIR/install_service.sh"
    fi
}

# Function to run both (service mode - recommended for production)
run_all() {
    echo -e "${BLUE}[1/2] Checking prerequisites...${NC}"
    check_scripts
    echo ""

    echo -e "${BLUE}[2/2] Installing and starting BeCoin service...${NC}"
    install_service
    echo ""

    echo -e "${GREEN}Post-deployment complete!${NC}"
    echo ""
    echo -e "${YELLOW}The BeCoin autonomous simulation is now running as a service.${NC}"
    echo -e "${YELLOW}Use 'sudo systemctl status becoin-autonomous' to check status.${NC}"
}

# Main execution
case "$MODE" in
    --startup|-s)
        check_scripts
        run_startup_foreground
        ;;
    --service|-i)
        check_scripts
        install_service
        ;;
    --background|-b)
        check_scripts
        run_startup_background
        ;;
    --help|-h)
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --startup, -s     Run autonomous_startup.sh in foreground"
        echo "  --service, -i     Install and start as systemd service"
        echo "  --background, -b  Start simulation in background (no service)"
        echo "  --help, -h        Show this help message"
        echo ""
        echo "Default (no option): Install and start as systemd service"
        ;;
    all|*)
        run_all
        ;;
esac
