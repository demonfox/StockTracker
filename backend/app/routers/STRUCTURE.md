# routers

FastAPI API 路由层，定义所有 REST 端点并调度到对应的业务逻辑。

## 文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 导出 `stocks_router`，供 `main.py` 注册 |
| `stocks.py` | 全部 API 端点：股票 CRUD（`/api/stocks`）、调度器控制（`/api/scheduler/*`）、运行时配置（`/api/config`） |

## 模块设计

- 所有端点统一挂载在 `/api` 前缀下
- 添加股票时立即触发一次数据抓取，让用户获得即时反馈
- 调度器配置支持运行时修改（`PATCH /api/config`），无需重启

## 依赖关系

- **内部依赖**：`app.database`（CRUD + session）、`app.schemas`（请求/响应校验）、`app.services`（调度器 + 数据抓取）
- **外部依赖**：`fastapi`
- **被依赖**：`app.main`（注册路由）
