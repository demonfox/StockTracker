# database

SQLAlchemy 异步 ORM 层，负责数据模型定义、数据库会话管理和 CRUD 操作。

## 文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 公共 API 汇总导出，统一暴露 Stock 模型、会话工具和 CRUD 函数 |
| `models.py` | SQLAlchemy ORM 模型定义（`Stock` 表，含 15+ 字段覆盖价格/成交/基本面/52 周数据） |
| `session.py` | 异步引擎 & session 工厂创建、数据库生命周期管理（`init_db`/`close_db`）、FastAPI 依赖注入 |
| `crud.py` | 全部 CRUD 操作：`get_all_stocks`、`add_stock`、`remove_stock`、`batch_update_stock_data` 等 |

## 模块设计

- 使用 SQLAlchemy 2.0 声明式映射 (`DeclarativeBase` + `Mapped`) 定义 ORM 模型
- 全部使用 `AsyncSession`，与 FastAPI 的异步生态一致
- `session.py` 通过 `get_db` 生成器提供 FastAPI `Depends` 注入
- `crud.py` 中的 `batch_update_stock_data` 支持一次事务内更新多只股票，由调度器批量调用

## 依赖关系

- **外部依赖**：`sqlalchemy`、`aiosqlite`
- **内部依赖**：`app.config`（获取数据库 URL）
- **被依赖**：`app.routers.stocks`（路由层）、`app.services.scheduler`（调度器）
