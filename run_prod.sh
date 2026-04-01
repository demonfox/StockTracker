#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# ============================================================
#  StockTracker — Production Startup Script
# ============================================================
#  Builds the frontend into static assets, copies them into
#  backend/static/, and starts a single uvicorn process that
#  serves both the API and the web UI on one port.
#
#  Usage:
#      chmod +x run_prod.sh
#      ./run_prod.sh              # default: port 8000, 2 workers
#      ./run_prod.sh --port 80    # custom port
#      ./run_prod.sh --workers 4  # custom worker count
#
#  Press Ctrl+C to stop the server gracefully.
# ============================================================

set -euo pipefail

# ── Color output helpers ─────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Parse CLI arguments ──────────────────────────────────────

PORT=8000
WORKERS=2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)
            PORT="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--port PORT] [--workers N]"
            echo ""
            echo "Options:"
            echo "  --port PORT      Server port (default: 8000)"
            echo "  --workers N      Number of uvicorn workers (default: 2)"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            echo "Usage: $0 [--port PORT] [--workers N]"
            exit 1
            ;;
    esac
done

# ── Resolve project root ─────────────────────────────────────

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
STATIC_DIR="${BACKEND_DIR}/static"

# ── Cleanup handler ──────────────────────────────────────────

cleanup() {
    echo ""
    info "Shutting down production server..."
    ok "Server stopped. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── Preflight checks ─────────────────────────────────────────

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  StockTracker — Production Build & Deploy${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    error "Python 3 is not installed."
    exit 1
fi

# Check Node.js
if ! command -v node &>/dev/null; then
    error "Node.js is not installed."
    exit 1
fi

# ── Step 1: Backend dependencies ──────────────────────────────

info "Step 1/4: Setting up Python environment..."

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
    info "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
ok "Python dependencies ready."

# ── Step 2: Frontend dependencies ─────────────────────────────

info "Step 2/4: Installing frontend dependencies..."

cd "${FRONTEND_DIR}"

if [[ ! -d "node_modules" ]]; then
    npm install
else
    ok "npm dependencies already installed."
fi

# ── Step 3: Build frontend ────────────────────────────────────

info "Step 3/4: Building frontend for production..."

# Clean previous build artifacts
if [[ -d "${STATIC_DIR}" ]]; then
    rm -rf "${STATIC_DIR}"
    info "Cleaned previous static build."
fi

npm run build

if [[ ! -d "${STATIC_DIR}" ]]; then
    error "Frontend build failed — ${STATIC_DIR} was not created."
    exit 1
fi

# Count built files
FILE_COUNT=$(find "${STATIC_DIR}" -type f | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "${STATIC_DIR}" | awk '{print $1}')
ok "Frontend built: ${FILE_COUNT} files, ${TOTAL_SIZE} total."

# ── Step 4: Start production server ──────────────────────────

info "Step 4/4: Starting production server..."
echo ""

cd "${BACKEND_DIR}"
# shellcheck disable=SC1091
source .venv/bin/activate

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  StockTracker is running in production mode!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Application${NC}  →  http://localhost:${PORT}"
echo -e "  ${GREEN}API Docs${NC}     →  http://localhost:${PORT}/docs"
echo -e "  ${GREEN}Workers${NC}      →  ${WORKERS}"
echo ""
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop the server."
echo ""

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --log-level info
