# services

前端 HTTP 客户端层，封装与后端 REST API 的所有通信。

## 文件说明

| 文件 | 说明 |
|------|------|
| `api.ts` | Axios 实例配置 + 全部 API 函数：股票 CRUD、调度器状态、配置更新、健康检查 |

## 模块设计

- 使用 `/api` 作为 baseURL，开发环境由 Vite proxy 转发到后端 `localhost:8000`，生产环境直接命中 FastAPI
- 超时设置 15 秒
- 每个 API 函数返回类型化的 Promise

## 依赖关系

- **外部依赖**：`axios`
- **内部依赖**：`types/stock.ts`（TypeScript 类型）
- **被依赖**：`hooks/useStocks.ts`
