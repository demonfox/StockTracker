# services

核心业务逻辑层，负责股票数据抓取和后台定时刷新调度。

## 文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 统一导出 fetcher 和 scheduler 的公共 API |
| `eastmoney_api.py` | 东方财富 push2 API 的 HTTP 客户端，使用 `urllib.request` 直连（避免连接池问题），带自动重试 |
| `tencent_api.py` | 腾讯财经 K 线 / 行情 API 的 HTTP 客户端，使用 `urllib.request` 直连，提供 CN 股票日 K 线 + qt 实时行情 |
| `stock_fetcher.py` | 统一数据抓取调度器：CN 市场走 EastMoney 实时 API（回退腾讯财经 K 线）、US 市场走 AkShare 日 K 线 |
| `scheduler.py` | APScheduler 后台定时任务管理：定时刷新、市场交易时间判断、运行时 interval 调整 |

## 模块设计

- **eastmoney_api.py**：直接调用东方财富 push2 接口，每次请求新建 TCP 连接（`Connection: close`），内置 3 次指数退避重试。字段映射表将 API 的 `f43`/`f58` 等代码转为中文键名
- **tencent_api.py**：调用腾讯财经 `web.ifzq.gtimg.cn` K 线端点，返回日 K 线 + qt 实时行情（88 字段）。内含单位换算（成交额万→元、市值亿→元），输出字段与 EastMoney 主路径完全兼容
- **stock_fetcher.py**：按市场分组调度，CN 优先用 EastMoney 实时接口，失败后回退到腾讯财经 K 线 API
- **scheduler.py**：基于 APScheduler AsyncIOScheduler，支持市场交易时间过滤（9:30–11:30, 13:00–15:00 CST）

## 设计决策

- **自建 HTTP 客户端代替 AkShare 直调**：AkShare 内部使用 `requests` 库的连接池，EastMoney 服务器会静默关闭 keep-alive 连接导致 `RemoteDisconnected` 错误。`eastmoney_api.py` 和 `tencent_api.py` 均用 stdlib 的 `urllib.request` 发送 `Connection: close` 请求彻底规避此问题
- **同步抓取 + `run_in_executor`**：AkShare 是同步库，通过 `asyncio.run_in_executor` 在线程池中运行，不阻塞事件循环
- **多数据源冗余**：CN 股票的 fallback 从 AkShare → 腾讯财经，字段更丰富（含市值、市盈率、振幅等），且连接稳定

## 依赖关系

- **内部依赖**：`app.config`（配置）、`app.database`（CRUD + session）
- **外部依赖**：`akshare`、`apscheduler`、`urllib.request`（stdlib）
- **被依赖**：`app.routers.stocks`（API 端点）、`app.main`（启动/停止调度器）
