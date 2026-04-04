# components

React UI 组件，构成 StockTracker 前端的可视化界面。

## 文件说明

| 文件 | 说明 |
|------|------|
| `Header.tsx` | 顶部导航栏：玻璃拟态风格，包含品牌标识、市场状态指示器、刷新按钮、轮询间隔设置 |
| `MarketSummary.tsx` | 数据概览统计条：显示持仓数量、调度器状态、上次刷新时间等摘要卡片 |
| `StockTable.tsx` | 主数据表格：可排序列、颜色编码涨跌、删除按钮（hover 显示）、空状态引导 |
| `AddStockModal.tsx` | 添加股票弹窗：6 位 A 股代码输入校验、热门股票快捷标签、市场选择 |
| `StockCard.tsx` | 移动端卡片视图：单只股票数据的紧凑卡片展示 |
| `.gitkeep` | 目录占位文件 |
