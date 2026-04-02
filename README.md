# StockTracker 📈

A full-stack stock tracking application for monitoring **China A-share market** stocks in real time. Built with a Python backend that fetches live data from AkShare and a modern React dashboard that displays everything in a clean, sortable table with color-coded price changes.

---

## ✨ Features

- **Real-time stock data** — current price, open/high/low, volume, turnover, market cap, P/E, P/B, turnover rate
- **Background auto-refresh** — configurable scheduler (10s–5min) powered by APScheduler
- **China market conventions** — red for price up, green for price down
- **Sortable data table** — click any column header to sort ascending/descending
- **Quick-add stocks** — 6-digit A-share symbol input with validation and popular stock chips
- **Market status awareness** — real-time trading-hours indicator (9:30–11:30, 13:00–15:00 CST)
- **Responsive design** — works on desktop and mobile with glassmorphism header and micro-animations
- **API documentation** — auto-generated OpenAPI docs at `/docs`
- **Single-process production deploy** — frontend built into static assets served by FastAPI

---

## 🛠 Tech Stack

| Layer      | Technology                                                    |
|------------|---------------------------------------------------------------|
| **Backend**   | Python 3.11+ · FastAPI · SQLAlchemy 2.0 (async) · SQLite · AkShare · APScheduler |
| **Frontend**  | React 18 · TypeScript · Vite 5 · Tailwind CSS 3.4 · Lucide Icons              |
| **Data**      | [AkShare](https://github.com/akfamily/akshare) — free, open-source A-share data |

---

## 📁 Project Structure

```
StockTracker/
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── main.py               # FastAPI entry point, lifespan, CORS, static mount
│   │   ├── config.py             # YAML config loader → typed Settings object
│   │   ├── database/
│   │   │   ├── models.py         # SQLAlchemy Stock model (15+ columns)
│   │   │   ├── session.py        # Async engine, session factory, DB init
│   │   │   └── crud.py           # CRUD: add, remove, get, batch-update stocks
│   │   ├── routers/
│   │   │   └── stocks.py         # REST endpoints: stocks CRUD + scheduler control
│   │   ├── services/
│   │   │   ├── stock_fetcher.py  # AkShare integration, field mapping, filtering
│   │   │   └── scheduler.py      # APScheduler setup, refresh job, interval control
│   │   └── schemas/
│   │       └── stock.py          # Pydantic request/response schemas
│   ├── config.yaml               # Application configuration
│   └── requirements.txt          # Python dependencies
├── frontend/                     # React + TypeScript frontend
│   ├── src/
│   │   ├── App.tsx               # Root component, state management
│   │   ├── components/
│   │   │   ├── Header.tsx        # Glassmorphism header with controls
│   │   │   ├── MarketSummary.tsx  # Stat cards strip
│   │   │   ├── StockTable.tsx    # Sortable data table, color-coded
│   │   │   ├── AddStockModal.tsx  # Symbol input modal with validation
│   │   │   └── StockCard.tsx     # Mobile card view
│   │   ├── services/api.ts       # Axios HTTP client
│   │   ├── hooks/useStocks.ts    # Polling hook with configurable interval
│   │   └── types/stock.ts        # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts            # Vite config with API proxy + prod build output
├── run.sh                        # Dev mode: start backend + frontend
├── run_prod.sh                   # Production: build & serve on single port
├── .gitignore
└── README.md
```

---

## 📋 Prerequisites

| Tool       | Minimum Version | Check Command           |
|------------|-----------------|-------------------------|
| **Python** | 3.11+           | `python3 --version`     |
| **Node.js**| 18+             | `node --version`        |
| **npm**    | 9+              | `npm --version`         |

---

## 🚀 Quick Start (Development)

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd StockTracker
```

### 2. One-command startup

```bash
chmod +x run.sh
./run.sh
```

This will:
1. Create a Python virtual environment (`backend/.venv`)
2. Install all Python dependencies
3. Install all npm packages
4. Start the backend on port **8000** (with hot-reload)
5. Start the frontend dev server on port **5173** (with HMR)

### 3. Open in your browser

| Service       | URL                                |
|---------------|------------------------------------|
| **Frontend**  | http://localhost:5173              |
| **Backend**   | http://localhost:8000              |
| **API Docs**  | http://localhost:8000/docs         |
| **ReDoc**     | http://localhost:8000/redoc        |

### Manual startup (alternative)

If you prefer to run each service in its own terminal:

```bash
# Terminal 1 — Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

---

## 🏭 Production Deployment

### Option A: Using `run_prod.sh`

```bash
chmod +x run_prod.sh
./run_prod.sh
```

This will:
1. Install/update all dependencies
2. Build the React frontend into `backend/static/`
3. Start uvicorn serving both API and static files on **port 8000**

**Custom port and workers:**

```bash
./run_prod.sh --port 80 --workers 4
```

### Option B: Manual build & run

```bash
# Build frontend
cd frontend
npm install
npm run build       # outputs to ../backend/static/

# Start production server
cd ../backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Option C: Docker (coming soon)

A `Dockerfile` will be provided in a future release for containerized deployment.

---

## ⚙️ Configuration

All settings are in `backend/config.yaml`:

```yaml
# Database settings
database:
  url: "sqlite+aiosqlite:///./stocktracker.db"

# Background scheduler settings
scheduler:
  refresh_interval_seconds: 30    # 10 ~ 300 recommended
  market_hours_only: false        # skip fetches outside 9:30-15:00 CST

# CORS settings (for frontend dev server)
cors:
  origins:
    - "http://localhost:5173"
    - "http://127.0.0.1:5173"

# Server settings
server:
  host: "0.0.0.0"
  port: 8000
```

### Configuration Reference

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `database.url` | string | `sqlite+aiosqlite:///./stocktracker.db` | SQLAlchemy async database URL |
| `scheduler.refresh_interval_seconds` | int | `30` | Seconds between data refresh cycles (min: 10) |
| `scheduler.market_hours_only` | bool | `false` | Only fetch during A-share trading hours |
| `cors.origins` | list | `["http://localhost:5173"]` | Allowed CORS origins for dev |
| `server.host` | string | `0.0.0.0` | Server bind address |
| `server.port` | int | `8000` | Server listen port |

### Runtime Configuration (no restart needed)

You can change the refresh interval and market-hours setting at runtime via API:

```bash
# Change refresh interval to 60 seconds
curl -X PATCH http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"refresh_interval_seconds": 60}'

# Enable market-hours-only mode
curl -X PATCH http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"market_hours_only": true}'
```

You can also change the interval directly from the frontend header settings dropdown.

---

## 📡 API Reference

Base URL: `http://localhost:8000`

### Stock Endpoints

| Method   | Endpoint               | Description                        | Request Body                          |
|----------|------------------------|------------------------------------|---------------------------------------|
| `GET`    | `/api/stocks`          | List all tracked stocks            | —                                     |
| `POST`   | `/api/stocks`          | Add a new stock ticker             | `{"symbol": "600519"}`                |
| `GET`    | `/api/stocks/{symbol}` | Get a single stock's data          | —                                     |
| `DELETE` | `/api/stocks/{symbol}` | Remove a stock from tracking       | —                                     |

### Scheduler Endpoints

| Method   | Endpoint                 | Description                         | Request Body                                   |
|----------|--------------------------|-------------------------------------|-------------------------------------------------|
| `GET`    | `/api/scheduler/status`  | Get scheduler status and next run   | —                                               |
| `POST`   | `/api/scheduler/refresh` | Trigger an immediate data refresh   | —                                               |
| `PATCH`  | `/api/config`            | Update scheduler config at runtime  | `{"refresh_interval_seconds": 60}` |

### System Endpoints

| Method   | Endpoint        | Description         |
|----------|-----------------|---------------------|
| `GET`    | `/api/health`   | Health check        |

### Example Responses

**GET `/api/stocks`**

```json
{
  "count": 2,
  "stocks": [
    {
      "id": 1,
      "symbol": "600519",
      "name": "贵州茅台",
      "current_price": 1589.00,
      "open_price": 1575.50,
      "high_price": 1595.20,
      "low_price": 1570.00,
      "close_price": 1580.00,
      "volume": 28456123,
      "turnover": 45123456789.00,
      "change_percent": 0.57,
      "market_cap": 1996234567890.00,
      "pe_ratio": 29.83,
      "pb_ratio": 8.65,
      "turnover_rate": 0.23,
      "updated_at": "2026-04-01T14:30:00",
      "created_at": "2026-04-01T10:00:00"
    }
  ]
}
```

**GET `/api/scheduler/status`**

```json
{
  "running": true,
  "interval_seconds": 30,
  "market_hours_only": false,
  "next_run": "2026-04-01T14:30:30"
}
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (React SPA)                     │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌────────────┐  │
│  │  Header   │ │  Summary  │ │ StockTable │ │ AddModal   │  │
│  └────┬─────┘ └─────┬─────┘ └──────┬─────┘ └─────┬──────┘  │
│       └──────────────┼──────────────┼─────────────┘         │
│                      │  useStocks (polling hook)             │
│                      │  Axios → /api/*                       │
└──────────────────────┼──────────────────────────────────────┘
                       │ HTTP (REST JSON)
┌──────────────────────┼──────────────────────────────────────┐
│                FastAPI Backend (port 8000)                   │
│  ┌───────────────────┼───────────────────────────────────┐  │
│  │           API Routers (stocks.py)                     │  │
│  │  GET/POST/DELETE /api/stocks  PATCH /api/config       │  │
│  └───────────────────┼───────────────────────────────────┘  │
│                      │                                      │
│  ┌─────────────┐  ┌──┴──────────┐  ┌─────────────────────┐ │
│  │ APScheduler │──│ stock_fetch │  │  Database CRUD      │ │
│  │ (interval)  │  │ (AkShare)   │  │  (SQLAlchemy async) │ │
│  └─────────────┘  └─────────────┘  └──────────┬──────────┘ │
│                                                │            │
│                                      ┌─────────┴─────────┐ │
│                                      │   SQLite (.db)     │ │
│                                      └───────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User adds a stock** → Frontend `POST /api/stocks` → Backend inserts into DB → Immediately fetches data from AkShare → Returns complete stock record
2. **Scheduler fires** (every N seconds) → Queries each tracked symbol individually via `stock_bid_ask_em` (CN) or `stock_us_hist` (US) → Batch-updates all stocks in a single transaction
3. **Frontend polls** (configurable interval) → `GET /api/stocks` → Renders sorted table with latest prices and color-coded changes

---

## 🔧 Troubleshooting

### Backend won't start

```
ModuleNotFoundError: No module named 'app'
```

**Solution**: Make sure you're running uvicorn from the `backend/` directory:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

### AkShare fetch errors

```
WARNING: Could not fetch data for XXX
```

**Possible causes**:
- Network connectivity issues
- AkShare API temporarily unavailable
- Invalid stock symbol (not a valid 6-digit A-share code)

The scheduler will automatically retry on the next cycle. Existing data in the database is preserved.

### Frontend can't connect to backend

```
Network Error / CORS error
```

**Solutions**:
1. Ensure the backend is running on port 8000
2. Check that `cors.origins` in `config.yaml` includes `http://localhost:5173`
3. Vite's proxy config (`vite.config.ts`) forwards `/api/*` to the backend

### Port already in use

```bash
# Find and kill processes on port 8000
lsof -ti:8000 | xargs kill -9

# Find and kill processes on port 5173
lsof -ti:5173 | xargs kill -9
```

### Database reset

To start fresh with an empty database:

```bash
rm backend/stocktracker.db
# Restart the backend — tables will be recreated automatically
```

---

## 📊 Data Source

Stock data is provided by **[AkShare](https://github.com/akfamily/akshare)**, an open-source Python library with comprehensive coverage of China A-share markets. The `stock_zh_a_spot_em()` function fetches real-time quotes for all A-share stocks in a single API call — no API key required.

---

## 📄 License

MIT
