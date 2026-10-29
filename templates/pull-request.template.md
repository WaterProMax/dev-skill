# Pull Request（`templates/pull-request.template.md`）

> 在 Phase 2 验证通过后，用本模板填写 PR 描述。把每个 `<...>` 换成当轮真实值。  
> **硬红线**：本 PR 的提交在 `feature/<task-slug>`（或任务单声明的 `fix/<task-slug>`）上，**没有**直接 commit 或 force-push 到 `main`。  
> 合入目标是 `develop` 或任务单中的 `INTEGRATION_BRANCH`。只有仓库不存在 `develop` 且没有其他集成分支时，PR 才可以指向 `main`，且提交仍然不在 `main` 上。

## 元信息（自动对照任务单）

- **`TASK_ID`**：`<例如：TASK-2026-001-book-order-mvp>`
- **任务单路径（`TASK_PLAN_PATH`）**：`<docs/tasks/<task-slug>.md>`
- **`CONTRACT_PATH`**：`<docs/contract.md | docs/contracts/<module>-contract.md | NONE (Scale S 内联契约)>`
- **功能分支**：`feature/<task-slug>`
- **集成分支（`INTEGRATION_BRANCH`）**：`<develop | 其他已声明分支>`
- **`COVERAGE_GATE`**：`<95 | 仓库既有门槛 | unset>`
- **硬红线确认**：本分支不是 `main`，也没有对 `main` force-push。

## 功能（Feature）

`<用一两句话说明用户可观察到的能力。非交易模块用自己的资源名，不要套教材/订单措辞。>`

## 变更（Changes）

- `<文件或行为 1>`
- `<文件或行为 2>`
- `<契约是否有 L1/L2/L3 变更；L3 须已获得人工重确认>`

## 方案（Approach）

`<关键不变量落在哪一层：DB Constraint / Request Validation / Service Invariant。涉及四类不变量时各写一句：唯一性、同事务原子性、精准释放与终态幂等、归属人鉴权 vs 模拟身份。不适用的类别写 N/A。>`

## 验证命令与结果（粘贴真实输出摘要）

| 检查 | 命令 | 退出码 | 结果摘要 |
|---|---|---|---|
| Step 1 | `<命令>` | `<0>` | `<摘要>` |
| Step 2 单元 + 集成 | `<命令>` | `<0>` | `<摘要>` |
| Step 3 | `<命令>` | `<0>` | `<摘要>` |
| Linter / 风格 | `<例如 ruff check .>` | `<0>` | `<摘要>` |
| 覆盖率（`COVERAGE_GATE`） | `<命令或“未统计”>` | `<0 或 n/a>` | `<实测百分比或 unset 说明>` |

## Conventional Commits 摘要

按 `<type>(<optional-scope>): <description>` 列出本分支提交。`type` ∈ `feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`。

- `feat(book-order): enforce single-active resource lock`
- `<继续列出其余提交说明>`

## 评审人（Reviewers）

- **仓库所有者**：`<GitHub 登录名>`
- **其他评审人**：`<至少 2 人；单人仓库写 solo，不要编造账号>`
- **单人仓库自检**：`<solo 时写明所有者已对照任务单与 CI 自检 1 次；团队仓库写 n/a>`
- **通过标准**：讨论串全部解决；CI 全绿；团队至少 2 个 LGTM / Approve，或 solo = 1 次所有者自检 + CI 全绿。

## 合入与发版

- [ ] Squash and merge 到 `INTEGRATION_BRANCH`
- [ ] 不把功能提交直接合进或强推到 `main`
- [ ] 等待下一次发版切分，不在本 PR 里自行给 `main` 打发布提交
