#!/usr/bin/env bash
# Start ariatuc with separate log viewer

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Log file path
LOG_FILE="${ARIATUC_LOG_FILE:-logs/ariatuc.log}"

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  ariatuc - Dual Terminal Setup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Ensure logs directory exists
mkdir -p logs

# Check if running in tmux
if [ -n "$TMUX" ]; then
    echo -e "${GREEN}✓ Running in tmux${NC}"
    echo -e "${YELLOW}Starting application in split pane...${NC}"
    echo ""

    # Split window horizontally (top: app, bottom: logs)
    tmux split-window -v -p 30

    # Start log viewer in bottom pane
    tmux send-keys -t 1 "cd '$PROJECT_ROOT' && tail -f '$LOG_FILE'" C-m

    # Start app in top pane (current pane)
    tmux select-pane -t 0

    # Set log level from environment or default to INFO
    export ARIATUC_LOG_LEVEL="${ARIATUC_LOG_LEVEL:-INFO}"
    export ARIATUC_LOG_CONSOLE="false"

    echo -e "${GREEN}✓ Log viewer started in bottom pane${NC}"
    echo -e "${GREEN}✓ Starting ariatuc...${NC}"
    echo ""

    # Start the application
    poetry run python -m ariatuc

elif command -v tmux &> /dev/null; then
    echo -e "${YELLOW}Not in tmux session${NC}"
    echo -e "${YELLOW}Starting new tmux session...${NC}"
    echo ""

    # Start new tmux session
    tmux new-session -d -s ariatuc -c "$PROJECT_ROOT"

    # Split window
    tmux split-window -v -p 30 -t ariatuc

    # Start log viewer in bottom pane
    tmux send-keys -t ariatuc:0.1 "tail -f '$LOG_FILE'" C-m

    # Start app in top pane
    tmux send-keys -t ariatuc:0.0 "export ARIATUC_LOG_LEVEL='${ARIATUC_LOG_LEVEL:-INFO}' && export ARIATUC_LOG_CONSOLE='false' && poetry run python -m ariatuc" C-m

    # Attach to session
    echo -e "${GREEN}✓ Tmux session created${NC}"
    echo -e "${BLUE}Attaching to session...${NC}"
    echo ""
    tmux attach-session -t ariatuc

else
    echo -e "${YELLOW}⚠ tmux not found${NC}"
    echo ""
    echo "Please install tmux or use the manual two-terminal workflow:"
    echo ""
    echo -e "${BLUE}Terminal 1 (Application):${NC}"
    echo "  $ cd $PROJECT_ROOT"
    echo "  $ mise run dev"
    echo ""
    echo -e "${BLUE}Terminal 2 (Logs):${NC}"
    echo "  $ cd $PROJECT_ROOT"
    echo "  $ mise run logs:tail"
    echo ""
    exit 1
fi
