# src

React + TypeScript 前端源代码根目录。

## 文件说明

| 文件 | 说明 |
|------|------|
| `App.tsx` | 根组件：组合 Header、MarketSummary、StockTable、AddStockModal，管理弹窗状态 |
| `main.tsx` | 应用入口：挂载 React 根节点到 DOM |
| `index.css` | 全局样式：Tailwind CSS 指令 + 自定义 CSS 变量（颜色主题、涨跌色） |
| `vite-env.d.ts` | Vite 环境类型声明 |

## 子目录

| 目录 | 说明 |
|------|------|
| `components/` | React UI 组件（Header、StockTable、AddStockModal 等），详见 [components/STRUCTURE.md](./components/STRUCTURE.md) |
| `hooks/` | 自定义 hooks（`useStocks` 数据管理），详见 [hooks/STRUCTURE.md](./hooks/STRUCTURE.md) |
| `services/` | Axios HTTP 客户端，详见 [services/STRUCTURE.md](./services/STRUCTURE.md) |
| `types/` | TypeScript 类型定义，详见 [types/STRUCTURE.md](./types/STRUCTURE.md) |
| `assets/` | 静态资源（SVG 等），详见 [assets/STRUCTURE.md](./assets/STRUCTURE.md) |

## 模块设计

数据流：`App.tsx` → `useStocks` hook → `services/api.ts` → 后端 `/api/*`

组件树：
```
App
├── Header（顶栏 + 控制）
├── MarketSummary（统计条）
├── StockTable（数据表）
└── AddStockModal（添加弹窗）
```
