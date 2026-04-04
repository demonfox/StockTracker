---
name: structure-md-init
description: Use when setting up a new project's STRUCTURE.md navigation system, or when user asks to create STRUCTURE.md files for a codebase. Bootstraps the full STRUCTURE.md hierarchy and updates AGENTS.md/CLAUDE.md with conventions and maintenance rules.
---

# STRUCTURE.md Init

为项目创建 STRUCTURE.md 渐进披露式导航体系，并将规范写入 AGENTS.md（或 CLAUDE.md）。

## When to Use

- 新项目初始化时，需要建立 STRUCTURE.md 体系
- 用户说"创建 STRUCTURE.md"、"建立目录结构文档"
- 已有项目缺少 STRUCTURE.md，需要补建

## How It Works

### Phase 1: 探查项目现状

1. 读取项目根目录结构（排除 `.git/`、`node_modules/`、`dist/`、`build/`、`vendor/`）
2. 识别已有的 AGENTS.md / CLAUDE.md
3. 列出所有需要创建 STRUCTURE.md 的目录

### Phase 2: 创建规范文档

在项目的 `docs/conventions/` 下创建 `structure-md.md`（规范文档本身），内容如下：

```markdown
# STRUCTURE.md 规范

> 本文档定义项目中 STRUCTURE.md 文件的编写标准和维护规则。

## 目的

每个文件夹（含子文件夹）维护一个 STRUCTURE.md，所有 STRUCTURE.md 构成渐进披露式的树状结构，为 Coding Assistants 和开发者提供分层导航。

AI 助手探索项目时，从根目录 STRUCTURE.md 开始，按需逐层深入，无需遍历整个文件树。

## 标准模板

所有 STRUCTURE.md 使用以下模板，各 section 按需裁剪（没有内容的直接省略）：

# <文件夹名称>

<一句话概述本文件夹的职责和定位>

## 文件说明

| 文件 | 说明 |
|------|------|
| `xxx.ts` | 一句话描述 |

## 子目录

| 目录 | 说明 |
|------|------|
| `sub/` | 一句话描述，详见 [sub/STRUCTURE.md](./sub/STRUCTURE.md) |

## 模块设计

概要设计思路和核心逻辑。重点写理解代码所需的关键信息。

## 设计决策

记录关键技术选型和方案取舍：

- **<决策主题>**：选择了 A 而非 B，因为 ...

只记录非显而易见的决策，重点是"为什么这样做"。

## 输入 / 输出

对外暴露的接口、接收的数据、产出的数据。

## 依赖关系

- **内部依赖**：依赖项目内的哪些模块
- **外部依赖**：依赖的第三方库
- **被依赖**：哪些模块依赖本模块

## 相关文档

- [设计文档](../docs/xxx.md)

## 编写规则

### 渐进披露
父级 STRUCTURE.md 只提供子目录的一句话概述 + 链接，不重复子目录细节。

### 按需裁剪
各 section 非必填。叶子目录通常只需概述 + 文件说明。

### 真实性
只描述已存在的文件和目录。如需提及未来规划，标注"（计划中）"。

### 语言
跟随项目主语言。

### 豁免目录
以下目录不需要 STRUCTURE.md：
- `.git/`、`node_modules/`、`dist/`、`build/`、`vendor/` 等
- `archive/` 及其子目录（已归档材料）
- 其他第三方生成的目录

## 维护规则

每次代码变更涉及以下情况时，必须同步更新对应的 STRUCTURE.md：

1. 新增文件 → 添加到"文件说明"
2. 新增子目录 → 添加到父目录"子目录" + 为新目录创建 STRUCTURE.md
3. 删除文件/目录 → 移除条目
4. 重命名/移动 → 更新路径和链接
5. 模块职责变更 → 更新"模块设计""输入/输出""依赖关系"
6. 设计文档变更 → 更新"相关文档"链接

代码变更如影响设计文档所描述的内容，也应同步更新设计文档。
```

如果项目已有 `docs/conventions/structure-md.md`，跳过此步。

### Phase 3: 为所有现有目录创建 STRUCTURE.md

自底向上遍历目录树，为每个非豁免目录创建 STRUCTURE.md：

1. **叶子目录优先**：先创建最深层目录的 STRUCTURE.md
2. **逐层向上**：父目录的 STRUCTURE.md 引用子目录链接
3. **内容来源**：读取目录中的实际文件，结合代码内容生成描述

**根目录 STRUCTURE.md 示例**：

```markdown
# project-name

一句话项目概述。

## 文件说明

| 文件 | 说明 |
|------|------|
| `AGENTS.md` | Coding Assistants 指引文件 |
| `package.json` | 项目依赖和脚本配置 |

## 子目录

| 目录 | 说明 |
|------|------|
| `src/` | 源代码，详见 [src/STRUCTURE.md](./src/STRUCTURE.md) |
| `docs/` | 设计文档，详见 [docs/STRUCTURE.md](./docs/STRUCTURE.md) |
| `tests/` | 测试用例，详见 [tests/STRUCTURE.md](./tests/STRUCTURE.md) |

## 相关文档

- [AGENTS.md](./AGENTS.md) — 项目全局指引
```

### Phase 4: 更新 AGENTS.md

在 AGENTS.md（或 CLAUDE.md）中追加以下两个段落（如已存在类似内容则合并更新）：

```markdown
## STRUCTURE.md 导航体系

每个目录（含子目录）都有 `STRUCTURE.md` 文件，构成渐进披露式的树状信息结构。探索项目时，**从根目录 `STRUCTURE.md` 开始，按需逐层深入**，无需遍历文件树。

规范详见 [docs/conventions/structure-md.md](./docs/conventions/structure-md.md)。

## 代码变更纪律

每次变更代码后必须同步更新：

1. **STRUCTURE.md** — 新增/删除/重命名文件或目录时，更新所在目录及父目录的 `STRUCTURE.md`
2. **设计文档** — 变更影响 `docs/` 中设计文档所描述的内容时，同步更新对应文档
```

如果项目没有 AGENTS.md 也没有 CLAUDE.md，则创建 AGENTS.md 并包含上述内容。

## Checklist

- [ ] Phase 1: 探查目录结构，列出所有非豁免目录
- [ ] Phase 2: 创建 `docs/conventions/structure-md.md` 规范文档
- [ ] Phase 3: 为每个非豁免目录创建 STRUCTURE.md（自底向上）
- [ ] Phase 4: 更新 AGENTS.md 添加导航体系和变更纪律段落
- [ ] 验证：所有非豁免目录都有 STRUCTURE.md
- [ ] 验证：STRUCTURE.md 之间的链接正确

## Common Mistakes

- **信息重复**：父目录复制了子目录的详细内容 → 父级只写一句话概述 + 链接
- **描述不存在的文件**：写了计划中的文件 → 只描述 `ls` 能看到的
- **所有 section 都写**：叶子目录也硬写"子目录"段 → 没有内容的 section 直接省略
- **忘记更新 AGENTS.md**：只创建了 STRUCTURE.md 但没在 AGENTS.md 中说明 → Phase 4 不可跳过
