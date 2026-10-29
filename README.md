# Dev Skill (`dev-skill` `v1.3.0`)

> **开发 Skill — 从「一句话需求」或「已有仓库扩模块」到任务规模分流（Scale L/M/S）、`AGENTS.md` 长期规则、当轮任务白名单、自洽数据/接口契约与业务不变量验收的工程治理流程**  
> **Contract-First MVP & Scoped Development Skill for AI-Assisted Engineering**

---

## 为什么需要这个 Skill？（团队 AI 协作三件套）

在课程项目、比赛开发与团队协作中，我们已经有了另外两块拼图：
1. 🎨 **画图 Skill（[`WaterProMax/drawing-skill`](https://github.com/WaterProMax/drawing-skill)）**：管架构图与机制图怎么画对、画好看；
2. 📝 **写作 Skill（[`WaterProMax/writing-skill`](https://github.com/WaterProMax/writing-skill)）**：管知识库生成与技术文档怎么基于源码证据不撒谎；
3. 🛠️ **开发 Skill（本仓库 `WaterProMax/dev-skill`）**：**管不会写代码或没有工程经验的队友，怎么让 AI 把功能做对、不越界、合得拢、真实验收**。

---

## `v1.3.0` 核心机制一览

### 1. 双模式 × 三级规模路由（拒绝所有小改动都硬套重型后端模板）

| 规模档位 | 适用场景 | 匹配的流程与按需展开规则 |
|---|---|---|
| **Scale L — 模糊的新项目 / 完整 MVP** | 从零立项，组员只丢出一句话（如「我要做后端的二手书交易模块」） | 完整 MVP 收拢 + 架构设计 + `AGENTS.md` + `docs/tasks/mvp-init.md` + `docs/contract.md`，确认后再分三步编码 |
| **Scale M — 已有项目的新功能** | 在现有仓库新增子模块（如「在商城里新增优惠券模块」） | **仓库盘点（Recon）** + 保护根 `AGENTS.md` 原有长期规则 + 独立任务单 `docs/tasks/<module>.md`（锁死 **File Whitelist**） + 增量契约 `docs/contracts/<module>-contract.md`（优先复用已有 OpenAPI/迁移文件） |
| **Scale S — 边界明确的小修复 / CLI / 纯前端 / 算法模块** | 修单个 Bug、写纯命令行工具、纯前端组件或算法函数 | **按需裁剪**：无需硬造数据库表或 HTTP 接口！在 `docs/tasks/<task>.md` 中写清简短影响说明、输入/输出签名、不变量与针对性验证命令即可 |

### 2. `AGENTS.md` 长期规则与当轮任务单（`docs/tasks/<task>.md`）解耦
- **`AGENTS.md`（`templates/AGENTS.template.md`）**：只管仓库级长期规范（技术栈、分层职责、权威真源优先级、全局环境与编码红线）。已有仓库扩模块时 **严禁重写覆盖全局 `AGENTS.md`**。
- **`docs/tasks/<task-slug>.md`（`templates/task-plan.template.md`）**：单独保存当轮任务的 `In-Scope`、`Non-Goals`、`File Whitelist`（含 `requirements.txt` 与 `tests/verification.json`）、`CONTRACT_PATH` 指针与三步校验命令，多人协作互不覆盖。

### 3. 100% 自洽契约模板 + 三级保证层（Enforcement Layer）+ 四大业务不变量
在 `templates/contract.template.md` 中：
- **模板自洽强校验**：字段字典中的全部 9 个索引（`idx_*` / `uk_*`）、ISBN 长度约束（`VARCHAR(20)`，`10~20` 字符）、全部 7 个状态枚举（含 `OFF_SHELF` 如何进入与重新上架退出）与可执行 SQL、API 校验规则 **100% 严丝合缝**，并注明每条规则由 **`DB Constraint` / `Request Validation` / `Service Invariant`** 哪一层保证。
- **SQLite 外键显式开启**：在建表 SQL 与连接初始化代码中强制执行 `PRAGMA foreign_keys = ON;`，防止插入引用不存在教材的脏订单。
- **四类领域无关的业务不变量（`INV-1`～`INV-4`）**。标题不绑定教材/订单；校园二手书只是工作示例（括号内）：
  - `INV-1`：**唯一性 / 单一有效待处理资源（防重）**（示例：一本书最多一个 `PENDING` 订单，`uk_orders_active_book` + `rowcount == 1`，冲突 `40901`）；
  - `INV-2`：**同事务原子性**（示例：锁书与建单同一事务，任一步失败整体回滚，不留孤儿锁）；
  - `INV-3`：**精准释放与终态幂等**（示例：取消只释放本单锁定；对 `COMPLETED`/`CANCELLED` 重复操作返回 `40903`）；
  - `INV-4`：**归属人鉴权 vs 模拟身份**（示例：`X-User-Id` 只传递身份，非归属人返回 `40301 FORBIDDEN_NOT_OWNER`）。
  - 优惠券、工单、库存等模块沿用这四类并改用自己的资源名与错误码。没有共享可变状态的 Scale S 任务把不适用项标成 `N/A`。

### 4. 三级契约变更确认协议（L1 / L2 / L3 — 堵死 Agent 私改契约漏洞）

| 变更级别 | 变更内容 | 默认处理规则 |
|---|---|---|
| **L1 补充说明** | 修正文案、补充示例，**不改变任何字段、类型、状态流转或行为** | 直接同步更新 `CONTRACT_PATH` |
| **L2 内部细节** | 内部私有实现调整，**不改变对外契约、表结构或文件白名单** | 在已授权白名单范围内直接执行 |
| **L3 行为/范围变更** | **删除/修改字段、改变状态流转或权限、扩大范围或修改白名单外文件** | **强制暂停（Re-Gate）**：提交具体差异（Diff），重新获得人工确认后才准改代码 |

### 5. Phase 3：Git / PR 交付门禁（验证通过之后，不是另一份 Skill）

Phase 2 命令全绿后，按 6 个阶段、12 步集成（详见 `SKILL.md` §6）：fork（若需要）→ 从 `develop` 或已声明集成分支切 `feature/<task-slug>` → 单测/集成/Linter/可配置覆盖率 → Conventional Commits 并推送功能分支 → 用 `templates/pull-request.template.md` 开 PR → 解决讨论并等 CI → squash merge 到集成分支后等待发版。

**硬红线：禁止直接 commit 或 force-push 到 `main`（自动否决）。** 仓库没有 `develop` 时，才允许从 `main` 切出功能分支。覆盖率默认 ≥95% 仅在项目已经统计覆盖率时生效；已有门槛写进任务单的 `COVERAGE_GATE`，未统计则记 `unset`。团队有评审人时请求仓库所有者 + 至少 2 名其他人并取得至少 2 个 LGTM；单人仓库为所有者自检 1 次 + CI 全绿。

---

## 搜索 / 推荐 / RAG 任务的结果验收（自 `v1.2.0`）

这类任务除原有工程契约外，按需读取 [证据驱动工作流指南](references/evidence-driven-workflows.md)，把“接口跑通”进一步落实为“结果满足用户需求”：

- 按用途定义逐项验收，绑定正文快照和可定位引文；代码/数据通过目标环境执行与结果断言验证。
- 通用教程搜索移除任务专有表列名，同时保留技术机制词；特定数据集/API 查询保留用户需要的标识，避免一刀切删词。
- 允许外部教程与有来源、已验证的本地任务数据互补，硬约束通过后再降低阅读负担。
- 固定候选池与开放搜索分别验收，披露模拟 Baseline、样本数、推荐成功率、错误采纳、拒绝率及成本；0 推荐的错误采纳占比为 N/A。

这些是 Skill 的设计与验收指导，不表示本仓库已经实现学习推荐系统或完成真实 ChatGPT 搜索对照。新规则不要求普通 CRUD、CLI 或前端任务引入推荐流水线。

## 一键复制话术模板（直接喂给 Cursor / Claude Code / Cloud Agent）

### 场景 A：从零立项（Scale L — 组员只会说一句话需求时）

```text
请严格加载并遵循 `dev-skill`（SKILL.md）的 Mode 1（从零立项 Greenfield MVP / Scale L）流程。
我的需求是：【在这里填你的一句话需求，例如：我要做后端的校园二手书交易模块】

注意硬门禁要求：
1. 现在处于 Phase 1（契约对齐阶段），在我确认之前，严禁编写任何业务实现代码！
2. 请先参考 `templates/AGENTS.template.md`、`templates/task-plan.template.md` 和 `templates/contract.template.md`，生成：
   - 根目录 `AGENTS.md` 与当轮任务单 `docs/tasks/mvp-init.md`（明确 `CONTRACT_PATH`、MVP 动作与 Non-Goals、含 `tests/verification.json` 的完整文件白名单、分步校验命令）
   - `docs/contract.md`（包含：标注保证层 Enforcement Layer 的表字段字典、含 OFF_SHELF 的完整状态流转表、开启 PRAGMA foreign_keys = ON 的可执行建表 SQL、INV-1~INV-4 业务不变量与权限规则、REST 接口与错误码字典）
3. 输出契约后请立即停下，向我列出需要确认的关键问题，等我回复“确认”后再进入 Phase 2 分步写代码。
```

### 场景 B：已有仓库新增模块（Scale M — 保护全局规则与邻接模块）

```text
请严格加载并遵循 `dev-skill`（SKILL.md）的 Mode 2（已有仓库扩展 Brownfield / Scale M）流程。
我要在当前仓库中开发：【在这里填需求，例如：在后端新增一个优惠券领取子模块】

注意硬门禁要求：
1. 请先盘点当前仓库的真实目录、依赖版本、已有 OpenAPI/迁移文件与统一响应封装，优先复用现有规范；保留根 `AGENTS.md` 原有长期规则，切勿重写覆盖！
2. 现在处于 Phase 1（契约对齐阶段），在我确认之前，严禁修改任何业务代码！
3. 请先新建独立任务单 `docs/tasks/<module>.md`（锁死本次允许新建/修改的【File Whitelist】，包含 `tests/verification.json`）和模块契约 `docs/contracts/<module>-contract.md`。
4. 输出后立即停下等我确认；确认后再按 Step 1 → Step 2（含并发/事务回滚/越权 40301/终态 40903 测试及 `tests/verification.json` 映射）→ Step 3 推进。
```

### 场景 C：Phase 1 契约确认后，放行进入 Phase 2

```text
Phase 1 的任务单与契约文件我已确认通过。
现在请进入 `dev-skill` 的 Phase 2：
1. 严格遵守文件白名单与契约定义（100% 对齐；若遇 L3 级字段/状态机/范围变更必须先停下请我重确认，严禁私自改契约）；
2. 依次执行 Step 1（环境/Schema/外键开启校验）→ Step 2（核心业务与 INV-1~INV-4 四类不变量测试，并维护 `tests/verification.json`；错误码按本模块契约，二手书示例才是 40901/40301/40903）→ Step 3（端到端冒烟验证），如实贴出真实终端输出（若测试失败严禁宣称完成）。
3. 同时跑 Linter 与任务单中的 `COVERAGE_GATE`（已统计覆盖率时默认 ≥95%，否则沿用仓库门槛或记 `unset`）。
```

### 场景 D：Phase 2 通过后，进入 Phase 3 / Git 交付

```text
Phase 2 的验证命令我已确认全部通过。
现在请进入 `dev-skill` 的 Phase 3（Git / PR 交付门禁），不要新开一份 Skill：
1. 若我不能直接推上游，请先 fork。从 `develop`（或任务单里的集成分支）切出 `feature/<task-slug>`，并绑定 TASK_ID 与 docs/tasks/<task-slug>.md。仓库没有 develop、也没有其他集成分支时，才允许从 main 切出该功能分支。
2. 跑通单元测试、集成测试、Linter，以及可配置覆盖率门禁 COVERAGE_GATE（项目已统计覆盖率时默认 ≥95%；已有门槛以仓库为准；未统计就在任务单写 unset，不要谎称 95%）。
3. 用 Conventional Commits 提交（例如 feat(book-order): enforce single-active resource lock），把功能分支推到我的远程（fork 或 origin），不要推 main。
4. 按 templates/pull-request.template.md 开 PR，写清功能、变更、方案、CONTRACT_PATH、任务单路径、验证命令结果、提交摘要和评审人。团队有人时请仓库所有者 + 至少 2 名其他评审；单人仓库写 solo。
5. 解决全部 review 讨论，等 CI 全绿。团队至少 2 个 LGTM；单人仓库 = 所有者自检 1 次 + CI 全绿。然后 squash merge 到 develop（或已声明的集成分支），等待下一次发版。
硬红线：禁止直接 commit 或 force-push 到 main，否则自动否决。
```

---

## 目录结构（Repository Layout）

```text
dev-skill/
├── SKILL.md                             # Skill 核心入口：Mode×Scale 路由、Phase 1/2/3、L1/L2/L3、四类不变量
├── README.md                            # 面向队友/新手的仓库说明与一键复制调用话术
├── CHANGELOG.md                         # 版本演进记录（v1.0.0 -> v1.3.0）
├── references/
│   └── evidence-driven-workflows.md     # 搜索/推荐/AI 任务按需读取：证据、查询提纯、分层评测
├── templates/                           # 标准契约、任务单与 PR 模板
│   ├── AGENTS.template.md               # 仓库级长期总控（含真源层级、L1/L2/L3、禁止直推 main）
│   ├── task-plan.template.md            # 当轮任务单（含 Scale L/M/S、Linter、COVERAGE_GATE、Phase 3 清单）
│   ├── contract.template.md             # 自洽契约模板（四类不变量 + 二手书工作示例）
│   └── pull-request.template.md         # PR 描述：CONTRACT_PATH、验证结果、Conventional Commits、评审人
├── examples/                            # 端到端实战示范与最小可运行复现代码
│   ├── one-sentence-to-mvp.md           # 两轮交互示范 + Phase 3 清单摘录
│   ├── phase3-checklist.md              # Phase 3 分支 / PR / 评审人填写示例
│   └── minimal-repro/                   # 零依赖可一键运行的 SQLite + unittest 最小复现套件
│       ├── README.md
│       ├── schema.sql
│       ├── book_order_service.py
│       ├── test_minimal_repro.py
│       └── verification.json            # INV-1~INV-4 与 initialization 的真实单测及生产目标映射
└── tests/                               # 两层验证体系（静态一致性审计 + 沙盒行为评测器）
    ├── README.md
    ├── regression-cases.yaml            # 12 个回归场景规范（Schema 校验，不自动执行 Agent）
    ├── validate_structure.py            # 第 1 层：结构、YAML 完整性、模板索引/状态机/SQLite 外键自洽审计
    ├── evaluate_workspace.py            # 第 2 层：针对目标工作区的 Phase 1 门禁、白名单 git diff、反假桩与运行时探针评测
    └── test_evaluate_workspace.py       # 针对第 2 层评测器的 29 项单元与对抗性回归测试
```

---

## 一键运行全套校验与最小复现（Verification Commands）

```bash
# 1. 第 1 层：结构、YAML 深度 Schema 与模板自洽性审计（含 SQLite 内存建表与外键拦截实测）
python3 tests/validate_structure.py

# 2. 第 2 层：行为评测器正反例沙盒自测 + 29 项定向与对抗回归测试
python3 tests/evaluate_workspace.py --self-test
python3 -m unittest discover -s tests -p 'test_evaluate_workspace.py' -v

# 3. 最小可运行复现示例（验证外键约束 + INV-1~INV-4 全部 5 项业务不变量测试）
python3 -m unittest discover -s examples/minimal-repro -v
```
