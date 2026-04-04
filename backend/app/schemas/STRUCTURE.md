# schemas

Pydantic 请求/响应数据模型，定义 API 的数据契约。

## 文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 统一导出所有 schema 类 |
| `stock.py` | 所有 Pydantic 模型：`StockCreate`、`StockResponse`、`StockListResponse`、`ConfigUpdate`、`SchedulerStatusResponse`、`MessageResponse` |

## 模块设计

- `StockResponse` 使用 `model_config = ConfigDict(from_attributes=True)` 直接从 ORM 模型转换
- 请求 schema 内置校验规则（如 symbol 长度、market 枚举、interval 范围）

## 依赖关系

- **外部依赖**：`pydantic`
- **被依赖**：`app.routers.stocks`（路由层使用 schema 做类型注解和校验）
