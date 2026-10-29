# AGENTS.md — 仓库级 AI 开发总控规则与架构基线

> **文档职责（长期规则 vs 当轮任务解耦）**：  
> 1. **`AGENTS.md`（本文件）** 以 **仓库级长期规则** 为主（总体架构、技术栈、分层职责、全局环境变量、权威真源层级与长期编码红线）。在已有仓库（Mode 2）中新增子模块时，**必须保留原有 `AGENTS.md` 约束，仅按必要范围增量修改，严禁覆盖全局规则**。  
> 2. **当轮任务计划（`TASK_PLAN_PATH`）**：每轮具体开发的 MVP 范围、文件白名单（File Whitelist）、阶段状态与针对性验收命令，建议单独保存在 `docs/tasks/<task-slug>.md`（见 `templates/task-plan.template.md`）；仅当从零立项（Mode 1）的单模块极简项目时，可合并填写在本文件 §1。  
> 3. **Phase 1 硬门禁**：在项目负责人确认当轮任务单与 `CONTRACT_PATH` 契约之前，**严禁编写任何业务实现代码**。  
> 4. **Phase 3 硬红线**：禁止直接向 `main` commit 或 force-push。功能分支为 `feature/<task-slug>`，从 `develop`（或已声明的集成分支）切出；仅当仓库没有 `develop` 且没有其他集成分支时，才允许**从** `main` 切出该功能分支。提交说明使用 Conventional Commits。  
> 5. **不变量类别**：有状态任务遵循四类领域无关不变量（唯一性 / 同事务原子性 / 精准释放与终态幂等 / 归属人鉴权 vs 模拟身份）。下文教材/订单句子是工作示例，不是非交易模块的必用词汇。

## 元信息与权威真源路由（Metadata & Source of Truth Routing）

- **项目/仓库名称**：`<填写项目名称，例如：校园二手书交易后端>`
- **开发模式与规模**：`<Mode 1: Greenfield MVP | Mode 2: Brownfield Scoped Dev>` / `<Scale L | Scale M | Scale S>`
- **`TASK_PLAN_PATH`（当轮任务与白名单单据）**：`docs/tasks/<task-slug>.md`（默认：`docs/tasks/mvp-init.md`）
- **`CONTRACT_PATH`（当前权威数据与接口契约路径）**：`docs/contract.md`（多模块仓库统一使用：`docs/contracts/<module>-contract.md`）
- **权威真源层级（Source of Truth Hierarchy — Mode 2 已有仓库必读）**：
  1. 若仓库已存在 **数据库迁移文件（Migrations / `sql/schema.sql`）** 或 **OpenAPI / Protobuf 规范**，直接复用既有定义作为底层结构真源，严禁另建冲突文档；
  2. 本轮新增/变更的字段、状态机、业务不变量与接口约定，以 `CONTRACT_PATH` 为唯一权威真源；
  3. 本轮允许新建或修改的文件边界，以 `TASK_PLAN_PATH`（或本文件 §4.1）中的 **File Whitelist** 为准。

---

## 1. MVP 最小闭环（Scope & Non-Goals）

<!-- 填写说明：
- 多模块或 Mode 2 已有仓库：请将具体任务的 In-Scope / Non-Goals 写入 `docs/tasks/<task-slug>.md`，此处仅保留仓库核心业务边界简述与链接。
- 从零立项（Mode 1）单模块项目：可直接在此处列出 3~5 个最核心、可验收的闭环动作及 Non-Goals。
-->

### 1.1 本轮必做核心动作（In-Scope MVP Actions — 详见 `TASK_PLAN_PATH`）
1. **动作 1（例如：发布与上下架教材）**：卖家提交书名、ISBN、售价（分）、成色，入库生成 `ON_SALE` 教材记录；支持卖家本人对 `ON_SALE` 教材执行下架（`OFF_SHELF`）与重新上架（`ON_SALE`）。
2. **动作 2（例如：教材列表与关键词检索）**：支持按状态（`ON_SALE`）和书名/ISBN 关键词分页查询教材。
3. **动作 3（例如：同事务原子锁书与创建订单）**：买家对 `ON_SALE` 教材下单，在同一数据库事务内原子更新教材为 `RESERVED` 并创建 `PENDING` 订单（保证同一本书最多存在一个 `PENDING` 订单，失败整体回滚）。
4. **动作 4（例如：带权限校验的订单完成/取消）**：仅允许订单关联买家或卖家将 `PENDING` 订单流转为 `COMPLETED`（联动教材为 `SOLD`）或 `CANCELLED`（仅释放该单对应的 `RESERVED` 教材回 `ON_SALE`）。

### 1.2 本轮明确不做（Non-Goals — 严禁 AI 擅自引入）
- ❌ **不做重型统一认证中心**：本轮不引入 OAuth2 / RBAC 多角色权限系统（采用显式声明的模拟身份传递 + 严格归属人权限校验规则 `40301`）。
- ❌ **不接真实第三方支付网关**：不对接微信/支付宝真实商户号，通过状态流转接口验证业务闭环。
- ❌ **不引入未授权重型中间件**：不引入 Redis 集群、RabbitMQ/Kafka 消息队列、Elasticsearch 或微服务拆分。
- ❌ **不跨界生成无关端代码**：若任务为纯后端/CLI/算法模块，不擅自生成未要求的后台管理大屏或无关模块。

---

## 2. Architecture 总体框架与目录树（Architecture & Directory Tree）

### 2.1 技术栈选型与理由（Tech Stack）

| 层级 | 选型（含版本） | 选型理由（优先简单、本地可一键启动） |
|---|---|---|
| 语言与运行时 | `<例如：Python 3.11+ / Node.js 20 / Go 1.22 / Java 17>` | `<团队环境已具备，零额外编译门槛>` |
| Web 框架（按需） | `<例如：FastAPI 0.115 / Express / Gin / 纯标准库 CLI>` | `<轻量、路由清晰；Scale S 非 HTTP 任务可省略 Web 框架>` |
| 数据库与连接规范 | `<例如：SQLite 3（必开 PRAGMA foreign_keys = ON）+ SQLAlchemy 2.0 / MySQL 8.0>` | `<本地零配置跑通事务与外键约束；Scale S 无状态任务可省略数据库>` |
| 测试与校验工具 | `<例如：unittest / pytest + httpx / curl>` | `<支持命令行自动化回归与业务不变量验证>` |

### 2.2 分层职责与保证层映射（Layered Responsibilities & Enforcement Layers）

```text
HTTP Client / CLI Caller
   │
   ▼
[Router / Controller 层]  ── 对应保证层：Request Validation（参数类型、长度 10~20、必填、枚举格式校验）
   │
   ▼
[Service 业务逻辑层]      ── 对应保证层：Service Invariant（归属人权限 40301、同事务原子更新 rowcount==1、状态机流转 40901/40902/40903）
   │
   ▼
[Repository / Model 层]   ── 负责 ORM/SQL 参数化映射（表名、列名与 CONTRACT_PATH 100% 一致）
   │
   ▼
[Database 存储层]         ── 对应保证层：DB Constraint（PRIMARY KEY、FOREIGN KEY、UNIQUE、CHECK、部分唯一索引）
```

### 2.3 目录结构预览（Directory Tree Preview）

```text
<project-root>/
├── AGENTS.md                        # 仓库级长期总控规则（本文件）
├── .env.example                     # 环境变量示例模板（不含真实密钥）
├── requirements.txt                 # 依赖清单（或 package.json / go.mod / pom.xml）
├── docs/
│   ├── contract.md                  # 单模块默认 CONTRACT_PATH（多模块用 docs/contracts/<module>-contract.md）
│   └── tasks/
│       └── mvp-init.md              # 当轮任务范围、文件白名单与验收单（TASK_PLAN_PATH）
├── app/
│   ├── __init__.py
│   ├── main.py                      # 应用入口、路由挂载、统一异常封装与健康检查
│   ├── config.py                    # 环境变量读取与默认配置
│   ├── database.py                  # 数据库连接管理（SQLite 必须在此显式执行 PRAGMA foreign_keys = ON）
│   ├── models.py                    # 数据库表模型定义（严格对齐 CONTRACT_PATH）
│   ├── schemas.py                   # 请求/响应 DTO 校验模型（严格对齐 CONTRACT_PATH）
│   ├── services.py                  # 核心业务不变量、事务原子锁与权限校验
│   └── routers.py                   # API 路由处理函数
├── sql/
│   └── schema.sql                   # 可直接执行的建表 DDL 与全部索引定义
└── tests/
    ├── test_smoke.py                # 覆盖正常闭环 + 并发/事务回滚/越权/终态重复操作的自动化测试
    └── verification.json            # 映射 initialization 与各 INV-N / AC-N 到单测及生产目标函数
```

---

## 3. 环境与启动/校验约定（Environment & Verification）

### 3.1 环境变量表（对应 `.env.example`）

| 变量名 | 示例默认值（`.env.example`） | 必填 | 用途说明 |
|---|---|---|---|
| `APP_ENV` | `development` | 否 | 运行环境标识（`development` / `test` / `production`） |
| `APP_HOST` | `127.0.0.1` | 否 | 服务监听地址 |
| `APP_PORT` | `8000` | 否 | 服务监听端口 |
| `DATABASE_URL` | `sqlite:///./data.db` | 是 | 数据库连接串（严禁在代码或文档中硬编码真实生产密码） |

### 3.2 数据库连接强制约束（SQLite Foreign Keys & Transaction Rule）

- 若使用 **SQLite**，由于 SQLite 默认在每个新建连接上关闭外键检查（`PRAGMA foreign_keys = OFF`），**必须在 `app/database.py` 的每个数据库连接初始化钩子及建表脚本中显式执行 `PRAGMA foreign_keys = ON;`**，否则 `orders.book_id -> books.id` 外键约束不会生效。

### 3.3 一键安装与启动命令（Quickstart Commands）

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库表结构并验证外键开启
sqlite3 data.db "PRAGMA foreign_keys = ON;" ".read sql/schema.sql"

# 4. 启动本地服务
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3.4 分步开发强制校验命令（Mandatory Step Verification）

> **Agent 铁律**：Phase 2 每完成一个 Step，必须真实运行对应命令并贴出终端输出；若任何测试失败，**严禁宣称已完成**，必须先定位修复并重跑通过。

- **Step 1 校验（环境骨架 + 建表 SQL + 外键约束生效检查）**：
  ```bash
  sqlite3 /tmp/test_init.db "PRAGMA foreign_keys = ON; .read sql/schema.sql" && python3 -c "import app.models, app.schemas; print('Step 1 Schema & Models OK')"
  ```
- **Step 2 校验（核心业务不变量：并发锁抢占、事务回滚、越权 `40301`、终态重复 `40903` 自动化测试）**：
  ```bash
  pytest -v tests/test_smoke.py
  ```
- **Step 3 校验（真实进程启动 + `curl` 端到端冒烟验证）**：
  ```bash
  # 健康检查
  curl -s http://127.0.0.1:8000/api/v1/health
  # 正常闭环与异常错误码（40901 / 40301 / 40903）请求验证
  curl -s -X POST http://127.0.0.1:8000/api/v1/books -H "Content-Type: application/json" -d '{"title":"深入理解计算机系统","isbn":"9787111544937","seller_id":"stu_2026001","price_cents":3500,"condition_level":"LIKE_NEW"}'
  ```

---

## 4. Agent 编码红线（Guardrails）

### 4.1 允许修改范围（File Whitelist — 完整包含依赖与契约文件）
- ✅ **默认允许新建/修改（Mode 1 单模块）**：
  - `AGENTS.md`
  - `docs/contract.md`（或 `CONTRACT_PATH` 指定的 `docs/contracts/<module>-contract.md`）
  - `docs/tasks/**`（`TASK_PLAN_PATH` 当轮任务单）
  - `.env.example`
  - `requirements.txt`（或 `package.json` / `go.mod` / `pom.xml` 等依赖清单文件）
  - `sql/schema.sql`
  - `app/**`
  - `tests/**`（含自动化测试与 `tests/verification.json` 运行时验收映射）
- *(注：在 Mode 2 已有仓库中，具体白名单以 `TASK_PLAN_PATH` 中声明的子模块文件列表为准。)*

### 4.2 禁止触碰边界（Forbidden Zones）
- 🚫 **Mode 2 已有仓库特别红线**：严禁重写全局 `AGENTS.md` 原有规则；严禁修改白名单之外的邻接模块代码、公共鉴权中间件、既有数据库迁移历史或已有接口的返回结构。
- 🚫 **禁止私自扩栈**：未经负责人确认，严禁往 `requirements.txt` 等依赖清单里添加未在 §2.1 声明的重型框架、外部云 SDK 或付费 API。

### 4.3 契约变更分级确认协议（Contract Synchronization Protocol — L1 / L2 / L3）

严禁 Agent 在编码过程中自行修改契约以掩盖代码偏差。任何变更按以下三级边界处理：

| 级别 | 变更内容 | 默认处理规则 |
|---|---|---|
| **L1 补充说明** | 修正文案错字、补充示例，**不改变任何字段名、类型、长度、枚举、路由或业务行为** | 直接同步更新 `CONTRACT_PATH` 并在回复末尾说明 |
| **L2 内部细节** | 内部私有函数拆分、局部变量重命名，**不改变对外契约、表结构、状态机或文件白名单** | 在已授权白名单范围内直接执行 |
| **L3 行为/范围变更** | **删除/新增/重命名字段、修改字段含义或长度、改变状态流转或权限规则、扩大范围或修改白名单外文件** | **强制暂停（Re-Gate）**：提交具体差异（Diff）与影响范围，**重新获得人工确认后**才准修改代码 |

### 4.4 反幻觉与证据诚实约定（Anti-Hallucination & Evidence Honesty）
1. **拒绝假数据桩代码**：严禁在业务接口中硬编码返回假数组或留 `# TODO` 冒充已落库功能；若外部依赖采用 Mock，必须在 `CONTRACT_PATH` §3 显式标为 `MOCK`。
2. **严禁隐瞒测试失败**：Step 1~3 校验命令若出现报错或失败用例，必须如实贴出报错并修复，严禁在测试失败时宣称“开发完成”。
3. **结论与证据对应**：按 `TASK_PLAN_PATH` 的验收项记录提交/配置、命令、日志和未测边界。少量样例通过不能扩写为全面解决；AI/搜索功能分别报告候选发现、证据核验与任务成功，披露样本数、拒绝结果和模拟 Baseline，不将模拟对照写成真实产品评测。

### 4.5 Git 交付红线与分支 / 提交约定（Phase 3）

> **硬红线（自动否决）**：严禁直接在 `main` 上 commit，严禁对 `main` 执行 force-push（含 `--force-with-lease`）。本地测试全绿也不能例外。发现当前工作分支是 `main`，交付直接失败。

1. **集成分支**：从 `develop` 或本文档 / 任务单写明的集成分支切出功能分支，squash merge 回该分支，再等待下一次发版。仅当仓库不存在 `develop` 且没有其他集成分支时，才允许从 `main` **切出** `feature/<task-slug>`；此时 PR 可以指向 `main`，但提交本身不得落在 `main` 上。
2. **分支名**：`feature/<task-slug>`，与 `TASK_ID`、`TASK_PLAN_PATH` 对应。修复类任务可使用 `fix/<task-slug>`，但必须在任务单声明。
3. **提交说明（Conventional Commits）**：`<type>(<optional-scope>): <description>`。`type` 取 `feat` / `fix` / `docs` / `style` / `refactor` / `perf` / `test` / `build` / `ci` / `chore` / `revert`。示例：`feat(book-order): enforce single-active resource lock`。
4. **推送目标**：贡献者远程（fork 的 `origin`，或本人有推送权限的仓库 `origin`）上的功能分支。禁止 `git push` 到 `main`。
5. **覆盖率门禁（`COVERAGE_GATE`，可配置）**：项目已经统计覆盖率时，默认 ≥95%。若 CI 或本文件已写明其他门槛，沿用该门槛并记入任务单，不要静默改成 95%。项目尚未统计覆盖率时，任务单写 `COVERAGE_GATE: unset` 以及准备采用的起步门槛，不得谎称已达 95%。
6. **评审**：团队中除仓库所有者外还有至少 2 名评审人时，请求所有者 + 至少 2 名其他人，讨论串全部解决、CI 全绿，并至少 2 个 LGTM / Approve。单人仓库写明 `solo`：所有者自检 1 次 + CI 全绿，不要编造评审人。
7. **PR 正文**：按 `templates/pull-request.template.md` 填写功能、变更、方案、`CONTRACT_PATH`、任务单路径、验证命令结果、Conventional Commits 摘要与评审人列表。
