# backend

Python FastAPI 后端服务，提供股票数据的 REST API、后台定时刷新和数据库持久化。

## 文件说明

| 文件 | 说明 |
|------|------|
| `config.yaml` | 应用配置文件：数据库 URL、调度器间隔、CORS 源、服务器端口 |
| `requirements.txt` | Python 依赖清单 |
| `stocktracker.db` | SQLite 数据库文件（运行时自动创建） |

## 子目录

| 目录 | 说明 |
|------|------|
| `app/` | FastAPI 应用主包（路由、数据库、服务、配置），详见 [app/STRUCTURE.md](./app/STRUCTURE.md) |
| `static/` | 前端生产构建产物，由 `vite build` 输出，详见 [static/STRUCTURE.md](./static/STRUCTURE.md) |

## 设计决策

- **SQLite + aiosqlite**：单机部署场景下足够，异步接口与 FastAPI 一致，无需额外数据库服务
- **AkShare + 自建 EastMoney HTTP 客户端**：免费数据源，自建客户端解决 AkShare 连接池导致的 `RemoteDisconnected` 问题
