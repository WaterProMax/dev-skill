# Dev Skill (`dev-skill` `v1.1.0`)

> **开发 Skill — 从「一句话需求」或「已有仓库扩模块」到任务规模分流（Scale L/M/S）、`AGENTS.md` 长期规则、当轮任务白名单、自洽数据/接口契约与业务不变量验收的工程治理流程**  
> **Contract-First MVP & Scoped Development Skill for AI-Assisted Engineering**

---

## 为什么需要这个 Skill？（团队 AI 协作三件套）

在课程项目、比赛开发与团队协作中，我们已经有了另外两块拼图：
1. 🎨 **画图 Skill（[`WaterProMax/drawing-skill`](https://github.com/WaterProMax/drawing-skill)）**：管架构图与机制图怎么画对、画好看；
2. 📝 **写作 Skill（[`WaterProMax/writing-skill`](https://github.com/WaterProMax/writing-skill)）**：管知识库生成与技术文档怎么基于源码证据不撒谎；
3. 🛠️ **开发 Skill（本仓库 `WaterProMax/dev-skill`）**：**管不会写代码或没有工程经验的队友，怎么让 AI 把功能做对、不越界、合得拢、真实验收**。

---

## `v1.1.0` 核心机制一览

### 1. 双模式 × 三级规模路由（拒绝所有小改动都硬套重型后端模板）

| 规模档位 | 适用场景 | 匹配的流程与按需展开规则 |
|---|---|---|
| **Scale L — 模糊的新项目 / 完整 MVP** | 从零立项，组员只丢出一句话（如「我要做后端的二手书交易模块」） | 完整 MVP 收拢 + 架构设计 + `AGENTS.md` + `docs/tasks/mvp-init.md` + `docs/contract.md`，确认后再分三步编码 |
| **Scale M — 已有项目的新功能** | 在现有仓库新增子模块（如「在商城里新增优惠券模块」） | **仓库盘点（Recon）** + 保护根 `AGENTS.md` 原有长期规则 + 独立任务单 `docs/tasks/<module>.md`（锁死 **File Whitelist**） + 增量契约 `docs/contracts/<module>-contract.md`（优先复用已有 OpenAPI/迁移文件） |
| **Scale S — 边界明确的小修复 / CLI / 纯前端 / 算法模块** | 修单个 Bug、写纯命令行工具、纯前端组件或算法函数 | **按需裁剪**：无需硬造数据库表或 HTTP 接口！在 `docs/tasks/<task>.md` 中写清简短影响说明、输入/输出签名、不变量与针对性验证命令即可 |

### 2. `AGENTS.md` 长期规则与当轮任务单（`docs/tasks/<task>.md`）解耦
- **`AGENTS.md`（`templates/AGENTS.template.md`）**：只管仓库级长期规范（技术栈、分层职责、权威真源优先级、全局环境与编码红线）。已有仓库扩模块时 **严禁重写覆盖全局 `AGENTS.md`**。
- **`docs/tasks/<task-slug>.md`（`templates/task-plan.template.md`）**：单独保存当轮任务的 `In-Scope`、`Non-Goals`、`File Whitelist`（含 `requirements.txt` 等依赖文件）、`CONTRACT_PATH` 指针与三步校验命令，多人协作互不覆盖。

### 3. 100% 自洽契约模板 + 三级保证层（Enforcement Layer）+ 四大业务不变量
在 `templates/contract.template.md` 中：
- **模板自洽强校验**：字段字典中的全部 9 个索引（`idx_*` / `uk_*`）、ISBN 长度约束（`VARCHAR(20)`，`10~20` 字符）、全部 7 个状态枚举（含 `OFF_SHELF` 如何进入与重新上架退出）与可执行 SQL、API 校验规则 **100% 严丝合缝**，并注明每条规则由 **`DB Constraint` / `Request Validation` / `Service Invariant`** 哪一层保证。
- **SQLite 外键显式开启**：在建表 SQL 与连接初始化代码中强制执行 `PRAGMA foreign_keys = ON;`，防止插入引用不存在教材的脏订单。
- **四条可验证业务不变量（`INV-1`～`INV-4`）**：
  - `INV-1`：**唯一有效待交易订单**（部分唯一索引 `uk_orders_active_book` + 条件更新 `rowcount == 1`，重复抢购返回 `40901`）；
  - `INV-2`：**锁书与建单同事务原子性**（任一步失败整体回滚，绝不残留孤儿锁）；
  - `INV-3`：**取消订单精准释放本单锁定 & 终态防重**（对已 `COMPLETED`/`CANCELLED` 订单重复操作返回 `40903`）；
  - `INV-4`：**模拟身份与归属人操作权限分离**（非本人上下架或非本单买/卖家操作订单统一返回 `40301 FORBIDDEN_NOT_OWNER`）。

### 4. 三级契约变更确认协议（L1 / L2 / L3 — 堵死 Agent 私改契约漏洞）

| 变更级别 | 变更内容 | 默认处理规则 |
|---|---|---|
| **L1 补充说明** | 修正文案、补充示例，**不改变任何字段、类型、状态流转或行为** | 直接同步更新 `CONTRACT_PATH` |
| **L2 内部细节** | 内部私有实现调整，**不改变对外契约、表结构或文件白名单** | 在已授权白名单范围内直接执行 |
| **L3 行为/范围变更** | **删除/修改字段、改变状态流转或权限、扩大范围或修改白名单外文件** | **强制暂停（Re-Gate）**：提交具体差异（Diff），重新获得人工确认后才准改代码 |

---

## 一键复制话术模板（直接喂给 Cursor / Claude Code / Cloud Agent）

### 场景 A：从零立项（Scale L — 组员只会说一句话需求时）

```text
请严格加载并遵循 `dev-skill`（SKILL.md）的 Mode 1（从零立项 Greenfield MVP / Scale L）流程。
我的需求是：【在这里填你的一句话需求，例如：我要做后端的校园二手书交易模块】

注意硬门禁要求：
1. 现在处于 Phase 1（契约对齐阶段），在我确认之前，严禁编写任何业务实现代码！
2. 请先参考 `templates/AGENTS.template.md`、`templates/task-plan.template.md` 和 `templates/contract.template.md`，生成：
   - 根目录 `AGENTS.md` 与当轮任务单 `docs/tasks/mvp-init.md`（明确 `CONTRACT_PATH`、MVP 动作与 Non-Goals、完整文件白名单、分步校验命令）
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
3. 请先新建独立任务单 `docs/tasks/<module>.md`（锁死本次允许新建/修改的【File Whitelist】）和模块契约 `docs/contracts/<module>-contract.md`。
4. 输出后立即停下等我确认；确认后再按 Step 1 → Step 2（含并发/事务回滚/越权 40301/终态 40903 测试）→ Step 3 推进。
```

### 场景 C：Phase 1 契约确认后，放行进入 Phase 2

```text
Phase 1 的任务单与契约文件我已确认通过。
现在请进入 `dev-skill` 的 Phase 2：
1. 严格遵守文件白名单与契约定义（100% 对齐；若遇 L3 级字段/状态机/范围变更必须先停下请我重确认，严禁私自改契约）；
2. 依次执行 Step 1（环境/Schema/外键开启校验）→ Step 2（核心业务与 INV-1~INV-4 不变量测试）→ Step 3（端到端冒烟验证），如实贴出真实终端输出（若测试失败严禁宣称完成）。
```

---

## 目录结构（Repository Layout）

```text
dev-skill/
├── SKILL.md                             # Skill 核心入口：Mode×Scale 路由、长期/当轮解耦、Phase 1/2、L1/L2/L3 变更协议、INV-1~4
├── README.md                            # 面向队友/新手的仓库说明与一键复制调用话术
├── CHANGELOG.md                         # 版本演进记录（v1.0.0 -> v1.1.0）
├── templates/                           # 标准契约与任务单模板
│   ├── AGENTS.template.md               # 仓库级长期总控规则模板（含真源层级、L1/L2/L3 协议、完整白名单）
│   ├── task-plan.template.md            # 当轮任务单模板 docs/tasks/<task>.md（含 Scale L/M/S、File Whitelist、验收计划）
│   └── contract.template.md             # 100% 自洽契约模板（含保证层、SQLite 外键开启、OFF_SHELF 流转、INV-1~4 不变量）
├── examples/                            # 端到端实战示范与最小可运行复现代码
│   ├── one-sentence-to-mvp.md           # 完整两轮交互示范（显式标注演示格式与复现证据边界）
│   └── minimal-repro/                   # 零依赖可一键运行的 SQLite + unittest 最小复现套件
│       ├── README.md
│       ├── schema.sql
│       ├── book_order_service.py
│       └── test_minimal_repro.py
└── tests/                               # 两层验证体系（静态一致性审计 + 沙盒行为评测器）
    ├── README.md
    ├── regression-cases.yaml            # 6 大回归场景（深度 Schema 校验）
    ├── validate_structure.py            # 第 1 层：结构、YAML 完整性、模板索引/状态机/SQLite 外键自洽审计
    └── evaluate_workspace.py            # 第 2 层：针对目标工作区的 Phase 1 门禁、白名单 git diff、反假桩与测试诚实度评测
```

---

## 一键运行全套校验与最小复现（Verification Commands）

```bash
# 1. 第 1 层：结构、YAML 深度 Schema 与模板自洽性审计（含 SQLite 内存建表与外键拦截实测）
python3 tests/validate_structure.py

# 2. 第 2 层：行为评测器正反例沙盒自测（覆盖一句话立项拦截、已有仓库白名单 git diff、测试失败谎报拦截）
python3 tests/evaluate_workspace.py --self-test

# 3. 最小可运行复现示例（验证外键约束 + INV-1~INV-4 全部 5 项业务不变量测试）
python3 -m unittest discover -s examples/minimal-repro -v
```
