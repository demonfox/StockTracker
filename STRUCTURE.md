# StockTracker

全栈 A 股实时行情追踪应用。Python FastAPI 后端从东方财富/AkShare 抓取实时数据，React + TypeScript 前端提供现代化仪表盘界面。

## 文件说明

| 文件 | 说明 |
|------|------|
| `README.md` | 项目介绍、技术栈、快速开始、API 文档、架构图、故障排查 |
| `run.sh` | 开发模式启动脚本：自动创建 venv、安装依赖、启动前后端 |
| `run_prod.sh` | 生产模式启动脚本：构建前端到 `backend/static/`，单端口部署 |
| `.gitignore` | Git 忽略规则 |

## 子目录

| 目录 | 说明 |
|------|------|
| `backend/` | Python FastAPI 后端（API、数据库、调度器、数据抓取），详见 [backend/STRUCTURE.md](./backend/STRUCTURE.md) |
| `frontend/` | React + TypeScript 前端（仪表盘 UI），详见 [frontend/STRUCTURE.md](./frontend/STRUCTURE.md) |
| `docs/` | 项目文档和规范，详见 [docs/STRUCTURE.md](./docs/STRUCTURE.md) |

## 模块设计

```
┌─────────────────────────────────────────┐
│         Browser (React SPA)             │
│  Header / MarketSummary / StockTable    │
│         useStocks (polling hook)        │
│         Axios → /api/*                  │
└────────────────┬────────────────────────┘
                 │ HTTP (REST JSON)
┌────────────────┴────────────────────────┐
│         FastAPI Backend (:8000)          │
│  Routers → Services → Database          │
│  APScheduler (interval refresh)         │
│  EastMoney API / AkShare (data source)  │
│  SQLite (persistence)                   │
└─────────────────────────────────────────┘
```

### 数据流

1. 用户添加股票 → `POST /api/stocks` → 入库 + 立即抓取 → 返回完整记录
2. 调度器定时触发 → 逐只抓取 EastMoney 实时数据 → 批量更新数据库
3. 前端轮询 → `GET /api/stocks` → 渲染排序表格 + 涨跌色

## 相关文档

- [AGENTS.md](./AGENTS.md) — AI 助手项目指引
- [docs/conventions/structure-md.md](./docs/conventions/structure-md.md) — STRUCTURE.md 编写规范
