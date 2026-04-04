# app

FastAPI 应用主包，组织了 Web 服务的全部后端逻辑：路由、数据库、业务服务和配置。

## 文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包标识文件 |
| `main.py` | FastAPI 应用入口：CORS 配置、路由注册、静态文件挂载、应用生命周期管理（DB 初始化 + 调度器启停） |
| `config.py` | YAML 配置加载器，将 `config.yaml` 解析为类型化的 `Settings` dataclass 单例 |

## 子目录

| 目录 | 说明 |
|------|------|
| `database/` | SQLAlchemy 异步 ORM 层（模型、会话、CRUD），详见 [database/STRUCTURE.md](./database/STRUCTURE.md) |
| `routers/` | FastAPI API 路由定义，详见 [routers/STRUCTURE.md](./routers/STRUCTURE.md) |
| `schemas/` | Pydantic 请求/响应 schema，详见 [schemas/STRUCTURE.md](./schemas/STRUCTURE.md) |
| `services/` | 核心业务逻辑（数据抓取 + 调度器），详见 [services/STRUCTURE.md](./services/STRUCTURE.md) |

## 模块设计

应用启动流程（`main.py` lifespan）：
1. `init_db()` → 创建数据库表
2. `start_scheduler()` → 启动 APScheduler 定时抓取
3. yield（运行期间）
4. `stop_scheduler()` + `close_db()` → 优雅关闭
