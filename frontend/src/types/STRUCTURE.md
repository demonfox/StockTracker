# types

TypeScript 类型定义，与后端 Pydantic schema 镜像对齐，提供前端全局类型安全。

## 文件说明

| 文件 | 说明 |
|------|------|
| `stock.ts` | 全部类型接口：`Stock`（股票数据）、`StockListResponse`、`StockCreateRequest`、`SchedulerStatus`、`ConfigUpdateRequest`、`MessageResponse`、`SortConfig` 等 |

## 依赖关系

- **被依赖**：`services/api.ts`、`hooks/useStocks.ts`、`components/` 下的各组件
