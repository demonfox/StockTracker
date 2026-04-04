# AGENTS.md — StockTracker AI 助手指引

> 本文件为 AI Coding Assistants 提供项目导航和协作规范。

## 项目概述

StockTracker 是一个全栈 A 股实时行情追踪应用：
- **后端**：Python 3.11+ / FastAPI / SQLAlchemy 2.0 (async) / SQLite / AkShare / APScheduler
- **前端**：React 18 / TypeScript / Vite 5 / Tailwind CSS
- **数据源**：东方财富 push2 API（实时）+ AkShare（回退）

## STRUCTURE.md 导航体系

每个目录（含子目录）都有 `STRUCTURE.md` 文件，构成渐进披露式的树状信息结构。探索项目时，**从根目录 `STRUCTURE.md` 开始，按需逐层深入**，无需遍历文件树。

规范详见 [docs/conventions/structure-md.md](./docs/conventions/structure-md.md)。

## 代码变更纪律

每次变更代码后必须同步更新：

1. **STRUCTURE.md** — 新增/删除/重命名文件或目录时，更新所在目录及父目录的 `STRUCTURE.md`
2. **设计文档** — 变更影响 `docs/` 中设计文档所描述的内容时，同步更新对应文档

## 关键入口点

| 用途 | 文件 |
|------|------|
| 后端启动入口 | `backend/app/main.py` |
| 前端启动入口 | `frontend/src/main.tsx` |
| 应用配置 | `backend/config.yaml` |
| 数据库模型 | `backend/app/database/models.py` |
| API 路由 | `backend/app/routers/stocks.py` |
| 数据抓取核心 | `backend/app/services/eastmoney_api.py` |
| 前端数据层 | `frontend/src/hooks/useStocks.ts` |

## 开发命令

```bash
# 开发模式（前后端分别启动）
./run.sh

# 生产模式（构建前端 + 单端口部署）
./run_prod.sh

# 仅启动后端
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# 仅启动前端
cd frontend && npm run dev
```
