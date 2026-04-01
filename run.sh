#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# ============================================================
#  StockTracker — Development Startup Script
# ============================================================
#  Launches both the FastAPI backend (uvicorn, port 8000)
#  and the React frontend dev server (vite, port 5173).
#
#  Usage:
#      chmod +x run.sh
#      ./run.sh
#
#  Press Ctrl+C to stop both services gracefully.
# ============================================================

set -euo pipefail

# ── Color output helpers ─────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Resolve project root ─────────────────────────────────────

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

# ── Cleanup handler ──────────────────────────────────────────

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    info "Shutting down services..."

    if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
        info "Stopping backend (PID ${BACKEND_PID})..."
        kill "${BACKEND_PID}" 2>/dev/null || true
        wait "${BACKEND_PID}" 2>/dev/null || true
        ok "Backend stopped."
    fi

    if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
        info "Stopping frontend (PID ${FRONTEND_PID})..."
        kill "${FRONTEND_PID}" 2>/dev/null || true
        wait "${FRONTEND_PID}" 2>/dev/null || true
        ok "Frontend stopped."
    fi

    ok "All services stopped. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── Preflight checks ─────────────────────────────────────────

info "StockTracker — Development Mode"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    error "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION="$(python3 --version 2>&1 | awk '{print $2}')"
info "Python version: ${PYTHON_VERSION}"

# Check Node.js
if ! command -v node &>/dev/null; then
    error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

NODE_VERSION="$(node --version 2>&1)"
info "Node.js version: ${NODE_VERSION}"

# Check npm
if ! command -v npm &>/dev/null; then
    error "npm is not installed. Please install npm 9+ first."
    exit 1
fi

NPM_VERSION="$(npm --version 2>&1)"
info "npm version: ${NPM_VERSION}"

echo ""

# ── Backend setup ─────────────────────────────────────────────

info "Setting up backend..."

cd "${BACKEND_DIR}"

# Create virtual environment if it doesn't exist
if [[ ! -d ".venv" ]]; then
    info "Creating Python virtual environment..."
    python3 -m venv .venv
    ok "Virtual environment created."
fi

# Activate virtual environment
# shellcheck disable=SC1091
source .venv/bin/activate
ok "Virtual environment activated."

# Install/update dependencies
info "Installing Python dependencies..."
pip install -q -r requirements.txt
ok "Python dependencies installed."

echo ""

# ── Frontend setup ────────────────────────────────────────────

info "Setting up frontend..."

cd "${FRONTEND_DIR}"

# Install npm dependencies if node_modules is missing
if [[ ! -d "node_modules" ]]; then
    info "Installing npm dependencies..."
    npm install
    ok "npm dependencies installed."
else
    ok "npm dependencies already installed."
fi

echo ""

# ── Start services ────────────────────────────────────────────

info "Starting services..."
echo ""

# Start backend
cd "${BACKEND_DIR}"
# shellcheck disable=SC1091
source .venv/bin/activate

info "Starting backend server (uvicorn)..."
uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info &
BACKEND_PID=$!
ok "Backend started (PID ${BACKEND_PID}) → http://localhost:8000"

# Give the backend a moment to initialize
sleep 2

# Start frontend
cd "${FRONTEND_DIR}"

info "Starting frontend dev server (vite)..."
npm run dev &
FRONTEND_PID=$!
ok "Frontend started (PID ${FRONTEND_PID}) → http://localhost:5173"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  StockTracker is running!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Frontend${NC}  →  http://localhost:5173"
echo -e "  ${GREEN}Backend${NC}   →  http://localhost:8000"
echo -e "  ${GREEN}API Docs${NC}  →  http://localhost:8000/docs"
echo ""
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop all services."
echo ""

# Wait for both processes
wait
