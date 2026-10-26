# 当轮开发任务单（`docs/tasks/<task-slug>.md`）

> **文档职责**：本文件用于保存 **单次迭代 / 单个子模块 / 单个修复任务** 的具体范围、文件白名单与验收条件，避免多人多模块协作时反复覆盖仓库根目录的长期 `AGENTS.md`。  
> **门禁规则**：Phase 1 产出的本任务单与关联 `CONTRACT_PATH` 经负责人确认后，方可进入 Phase 2 编写代码。

## 1. 任务元信息与路由（Task Metadata & Scale Triage）

- **任务 ID（`TASK_ID`）**：`<例如：TASK-2026-001-book-order-mvp>`
- **任务名称**：`<例如：新增校园二手书交易与原子锁单子模块>`
- **仓库模式（`MODE`）**：`<Mode 1: Greenfield MVP | Mode 2: Brownfield Scoped Dev>`
- **任务规模（`SCALE`）**：`<Scale L: 模糊新项目 | Scale M: 已有项目新功能 | Scale S: 边界明确的小修复/CLI/前端/算法>`
- **关联长期总控**：`AGENTS.md`
- **关联契约路径（`CONTRACT_PATH`）**：`<docs/contract.md | docs/contracts/<module>-contract.md | NONE (Scale S 内联契约)>`
- **复用已有规范声明（Mode 2 必填）**：`<例如：复用现有的 OpenAPI docs/openapi.yaml 与统一响应封装 app/common/response.py，不新建冲突结构>`
- **当前状态（`PHASE_STATUS`）**：`[ ] Phase 1 待确认` / `[ ] Phase 2 开发中` / `[ ] Phase 2 已验收`

---

## 2. 当轮范围界定（In-Scope & Non-Goals）

### 2.1 本轮必做（In-Scope）
1. `<动作/改动 1：精确描述可验证的输入、处理与输出>`
2. `<动作/改动 2：精确描述状态变更或业务不变量>`
3. `<动作/改动 3：精确描述异常与权限拦截边界>`

### 2.2 本轮明确不做（Non-Goals）
- ❌ `<排除项 1：例如不修改现有用户登录模块与全局中间件>`
- ❌ `<排除项 2：例如不引入额外数据库表或第三方队列>`

---

## 3. 文件白名单与只读边界（File Whitelist & Read-Only Boundaries）

> **评测器强校验项**：`tests/evaluate_workspace.py` 会直接比对 `git diff` 改动文件与下方白名单，任何越界改动将直接判 `FAIL`。

### 3.1 允许新建或修改的文件（Allowed Create / Modify Whitelist）
- `docs/tasks/<task-slug>.md`（本任务单）
- `<CONTRACT_PATH，例如 docs/contract.md 或 docs/contracts/book-order-contract.md>`
- `<requirements.txt 或 package.json —— 若本轮新增或锁版本依赖则必须列入>`
- `<.env.example —— 若本轮新增环境变量则必须列入>`
- `<sql/schema.sql 或具体 migration 文件路径>`
- `<app/modules/book_order/** 或具体源码文件路径>`
- `<tests/test_book_order.py>`

### 3.2 严禁修改的只读邻接模块（Read-Only Adjacent Zones）
- 🚫 `app/modules/auth/**`、`app/modules/user/**`、`app/core/middleware.py` 等非本任务白名单路径。

---

## 4. Scale S 轻量内联契约（仅当 `SCALE = Scale S` 且无独立 `CONTRACT_PATH` 时填写）

<!-- 若任务为 Scale L / Scale M，请详细填写独立的 CONTRACT_PATH（使用 templates/contract.template.md），本节可留空或写“见 CONTRACT_PATH”。 -->

- **函数 / CLI / 组件签名**：`<例如：def parse_isbn(raw: str) -> str>`
- **输入约束（Request / Input Validation）**：`<例如：允许 10 位或 13 位数字及连字符，总长度 10~20，空值或非法校验位抛出 ValueError>`
- **输出与不变量（Output & Invariants）**：`<例如：返回去除连字符后的标准纯数字/X 字符串，幂等且不修改入参>`
- **向后兼容性影响**：`<例如：仅修复带连字符 ISBN-13 误判问题，不影响已有调用方签名>`

---

## 5. 本轮分步验收命令与通过标准（Verification Plan）

1. **Step 1（结构/Schema/依赖检查）**：
   ```bash
   <填写具体可执行命令，例如：sqlite3 /tmp/test.db "PRAGMA foreign_keys = ON; .read sql/schema.sql">
   ```
2. **Step 2（单测与业务不变量测试：含并发/原子锁、事务回滚、越权 `40301`、终态重复 `40903`）**：
   ```bash
   <填写具体可执行命令，例如：python3 -m unittest discover -s tests -v>
   ```
3. **Step 3（端到端冒烟或回归测试）**：
   ```bash
   <填写具体可执行命令，例如：python3 tests/evaluate_workspace.py --workspace . --scene phase2_delivery>
   ```

### 5.1 结果验收与证据（按任务填写）

对每个必要 `acceptanceItem` 写明：稳定 ID、输入/适用条件、可观察的通过与失败判据、保证层、验证命令/人工检查方法、证据产物路径。Scale S 可用简短条目；不适用的项无需展开。

- **声明边界**：`<哪些功能已实现/已实测；哪些依赖为 MOCK；未测或未知项>`
- **复现信息**：`<提交、配置/运行环境、样例 ID、时间、命令、退出状态及日志路径>`
- **搜索/推荐/AI 任务（仅适用时）**：参考 Skill 的 `references/evidence-driven-workflows.md`，分别定义候选发现与逐项核验的通过标准，列出 `fixed-material` / `end-to-end-search` 的运行条件、Baseline 公平性、样本数、成功/错误/拒绝计数与分母、成本和重试预算。不能用全部拒绝的“零误推”替代推荐成功率。
