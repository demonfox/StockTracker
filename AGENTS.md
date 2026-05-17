# AGENTS.md — StockTracker AI 助手指引

> 本文件为 AI Coding Assistants 提供项目导航和协作规范。

## 项目概述

StockTracker 是一个全栈 A 股 + 美股实时行情追踪应用：
- **后端**：Python 3.11+ / FastAPI / SQLAlchemy 2.0 (async) / SQLite / APScheduler
- **前端**：React 18 / TypeScript / Vite 5 / Tailwind CSS
- **数据源**：腾讯财经 K 线 / 行情 API（唯一数据源）

## STRUCTURE.md 导航体系

每个目录（含子目录）都有 `STRUCTURE.md` 文件，构成渐进披露式的树状信息结构。探索项目时，**从根目录 `STRUCTURE.md` 开始，按需逐层深入**，无需遍历文件树。

规范详见 [docs/conventions/structure-md.md](./docs/conventions/structure-md.md)。

## AI 协作规则

1. **禁止擅自修改代码**：在用户明确要求或确认之前，AI **绝不允许** 自行修改任何代码文件。当诊断出问题或有修复建议时，必须先向用户说明根因分析和修复方案，等用户明确同意后才能动手改代码。
2. **分析归分析，修改归修改**：诊断问题时只做调查和分析，把结论和方案呈现给用户。不要把"分析"和"修复"混为一谈。
3. **低置信度时必须说明**：如果对根因分析的置信度不高，必须明确告知用户，而不是编造一个听起来合理的解释然后直接开始改代码。

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
| 数据抓取核心 | `backend/app/services/tencent_api.py` |
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
