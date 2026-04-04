# frontend

React + TypeScript + Vite 前端应用，提供 StockTracker 的 Web 仪表盘界面。

## 文件说明

| 文件 | 说明 |
|------|------|
| `package.json` | npm 依赖和脚本配置 |
| `package-lock.json` | npm 依赖锁定文件 |
| `vite.config.ts` | Vite 配置：开发代理（`/api` → `localhost:8000`）、生产构建输出到 `../backend/static` |
| `tailwind.config.js` | Tailwind CSS 配置：自定义颜色主题（涨跌色、背景色、文字色） |
| `postcss.config.js` | PostCSS 配置（Tailwind + autoprefixer） |
| `tsconfig.json` | TypeScript 根配置 |
| `tsconfig.app.json` | 应用 TypeScript 配置 |
| `tsconfig.node.json` | Node/Vite 工具链 TypeScript 配置 |
| `eslint.config.js` | ESLint 配置 |
| `index.html` | SPA 入口 HTML 模板 |
| `README.md` | Vite + React 模板自带的说明文档 |
| `.gitignore` | 前端专用 git 忽略规则 |

## 子目录

| 目录 | 说明 |
|------|------|
| `src/` | 源代码（组件、hooks、服务、类型），详见 [src/STRUCTURE.md](./src/STRUCTURE.md) |
| `public/` | 公共静态资源，详见 [public/STRUCTURE.md](./public/STRUCTURE.md) |

## 设计决策

- **Vite + React 18**：快速 HMR 开发体验，生产构建输出直接到 `backend/static/` 实现单端口部署
- **Tailwind CSS**：utility-first 样式，自定义主题遵循中国市场惯例（红涨绿跌）
- **Axios**：相比 fetch API 提供更好的拦截器和类型支持
