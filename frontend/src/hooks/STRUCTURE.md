# hooks

React 自定义 hooks，封装业务逻辑和状态管理。

## 文件说明

| 文件 | 说明 |
|------|------|
| `useStocks.ts` | 股票数据管理 hook：自动轮询（可配置间隔）、CRUD 操作、手动刷新、加载/错误状态追踪、调度器状态同步 |

## 模块设计

`useStocks` 是前端的核心数据层，封装了所有与后端 API 的交互逻辑：
- 通过 `setInterval` 实现前端轮询
- 使用 `useRef` 防止并发请求和 unmount 后的状态更新
- 删除股票时采用乐观更新（先从本地移除，不等后端响应）

## 依赖关系

- **内部依赖**：`services/api.ts`（HTTP 客户端）、`types/stock.ts`（类型定义）
- **被依赖**：`App.tsx`（根组件消费此 hook）
