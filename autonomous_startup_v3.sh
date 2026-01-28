#!/bin/bash

# BeCoin Economy v3.0 - Autonomous Startup Script
# This script starts the economy simulation with balanced parameters

set -e

echo "🚀 Starting BeCoin Economy v3.0"
echo "================================="

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ECONOMY_ENGINE="$PROJECT_DIR/becoin_economy/engine_v3.py"
DASHBOARD_DIR="$PROJECT_DIR/dashboard"
DATA_DIR="$DASHBOARD_DIR/becoin-economy"
LOG_FILE="$PROJECT_DIR/logs/economy_v3.log"
PID_FILE="$PROJECT_DIR/economy_v3.pid"

# Create necessary directories
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$DATA_DIR"

# Function to check if process is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        if ps -p "$(cat "$PID_FILE")" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Function to start the economy
start_economy() {
    echo "Starting economy engine..."

    if is_running; then
        echo "❌ Economy is already running (PID: $(cat "$PID_FILE"))"
        exit 1
    fi

    # Start Python economy engine in background
    nohup python3 "$ECONOMY_ENGINE" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    echo "✅ Economy started (PID: $(cat "$PID_FILE"))"

    # Wait a moment for initialization
    sleep 2

    # Check if it's still running
    if ! is_running; then
        echo "❌ Economy failed to start. Check logs: $LOG_FILE"
        exit 1
    fi
}

# Function to stop the economy
stop_economy() {
    echo "Stopping economy engine..."

    if ! is_running; then
        echo "❌ Economy is not running"
        return
    fi

    kill "$(cat "$PID_FILE")"
    rm -f "$PID_FILE"

    echo "✅ Economy stopped"

    # Wait for clean shutdown
    sleep 1
}

# Function to show status
show_status() {
    if is_running; then
        echo "✅ Economy is running (PID: $(cat "$PID_FILE"))"

        # Show basic stats if data exists
        TREASURY_FILE="$DATA_DIR/treasury.json"
        if [ -f "$TREASURY_FILE" ]; then
            BALANCE=$(jq -r '.balance' "$TREASURY_FILE")
            HOURS=$(jq -r '.hours_elapsed' "$DATA_DIR/autonomous_loop.json" 2>/dev/null || echo "0")
            echo "   Balance: \$$BALANCE"
            echo "   Hours elapsed: $HOURS"
        fi
    else
        echo "❌ Economy is not running"
    fi
}

# Function to reset economy
reset_economy() {
    echo "Resetting economy to initial state..."

    if is_running; then
        stop_economy
    fi

    # Remove all data files
    rm -f "$DATA_DIR"/*.json

    echo "✅ Economy reset complete"
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -n 50 "$LOG_FILE"
    else
        echo "No logs found"
    fi
}

# Function to run simulation cycles
run_cycles() {
    local cycles=${1:-1}
    echo "Running $cycles simulation cycles..."

    if ! is_running; then
        echo "❌ Economy is not running. Start it first."
        exit 1
    fi

    # Run cycles by triggering advance_time
    for ((i=1; i<=cycles; i++)); do
        echo "Running cycle $i..."

        # This would need to be implemented via API call
        # For now, we'll just wait and check status
        sleep 1

        if [ -f "$DATA_DIR/treasury.json" ]; then
            BALANCE=$(jq -r '.balance' "$DATA_DIR/treasury.json")
            echo "   Cycle $i - Balance: \$$BALANCE"
        fi
    done

    echo "✅ Completed $cycles cycles"
}

# Function to start web dashboard
start_dashboard() {
    echo "Starting web dashboard..."

    # Check if we have a web server
    if command -v python3 &> /dev/null; then
        cd "$DASHBOARD_DIR"
        nohup python3 -m http.server 8000 >> "$PROJECT_DIR/logs/dashboard.log" 2>&1 &
        echo $! > "$PROJECT_DIR/dashboard.pid"
        echo "✅ Dashboard started on http://localhost:8000"
        echo "   Dashboard PID: $(cat "$PROJECT_DIR/dashboard.pid")"
    else
        echo "❌ Python3 not found for dashboard server"
        exit 1
    fi
}

# Function to stop dashboard
stop_dashboard() {
    if [ -f "$PROJECT_DIR/dashboard.pid" ]; then
        kill "$(cat "$PROJECT_DIR/dashboard.pid")" 2>/dev/null || true
        rm -f "$PROJECT_DIR/dashboard.pid"
        echo "✅ Dashboard stopped"
    else
        echo "❌ Dashboard is not running"
    fi
}

# Parse command line arguments
case "${1:-start}" in
    start)
        start_economy
        start_dashboard
        echo ""
        echo "🌐 Dashboard: http://localhost:8000/economy-dashboard.html"
        echo "📊 Economy running autonomously"
        ;;
    stop)
        stop_dashboard
        stop_economy
        ;;
    restart)
        stop_dashboard
        stop_economy
        sleep 1
        start_economy
        start_dashboard
        ;;
    status)
        show_status
        ;;
    reset)
        reset_economy
        ;;
    logs)
        show_logs
        ;;
    cycles)
        run_cycles "${2:-1}"
        ;;
    dashboard)
        case "${2:-start}" in
            start)
                start_dashboard
                ;;
            stop)
                stop_dashboard
                ;;
            *)
                echo "Usage: $0 dashboard {start|stop}"
                exit 1
                ;;
        esac
        ;;
    test)
        echo "Running economy test..."
        if is_running; then
            stop_economy
        fi

        # Start economy and run a few cycles
        start_economy
        sleep 3
        run_cycles 3
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|reset|logs|cycles N|dashboard {start|stop}|test}"
        echo ""
        echo "Commands:"
        echo "  start      - Start economy and dashboard"
        echo "  stop       - Stop economy and dashboard"
        echo "  restart    - Restart economy and dashboard"
        echo "  status     - Show economy status"
        echo "  reset      - Reset economy to initial state"
        echo "  logs       - Show recent logs"
        echo "  cycles N   - Run N simulation cycles"
        echo "  dashboard  - Control dashboard server"
        echo "  test       - Run a quick test (3 cycles)"
        echo ""
        echo "Examples:"
        echo "  $0 start          # Start everything"
        echo "  $0 cycles 10      # Run 10 simulation cycles"
        echo "  $0 dashboard stop # Stop only dashboard"
        exit 1
        ;;
esac