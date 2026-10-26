---
name: dev-skill
description: Use when a user or teammate with limited coding experience asks to build a project, backend service, feature, or submodule from a vague or one-sentence request (e.g., "我要做后端的XX", "帮我做个XX系统"), when starting a new MVP from scratch (Greenfield), or when adding or fixing a module in an existing repository (Brownfield) before writing any implementation code.
---

# Contract-First MVP & Scoped Development Skill (`dev-skill`)

## Overview

Turn vague, one-sentence feature requests from novices or teammates (such as *"我要做后端的订单模块"* or *"帮我写个校园二手交易系统"*)—as well as scoped features or fixes in existing repositories—into bounded, contract-governed, verifiable deliveries.

Alongside `drawing-skill` (architecture/mechanism diagrams) and `writing-skill` (evidence-governed technical documents), `dev-skill` governs the **AI-assisted development lifecycle**:

> **1. Contract Gate before business code (`契约先行，点头再动代码`).** Never write business code directly from a vague request. First converge scope, architecture, file whitelist, and contracts (`AGENTS.md` + `docs/tasks/<task>.md` + `CONTRACT_PATH`), then stop for human confirmation.
> **2. Contract is the single source of truth (`契约即唯一真相，分级变更重确认`).** Table names, column names, state enums, invariants, route paths, and I/O schemas in code must match `CONTRACT_PATH` 100%. Behavioral or scope changes (L3) require human re-confirmation before editing code.
> **3. Stepwise execution with real verification (`小步快跑，真实命令与不变量验收`).** Build in verifiable steps and execute real verification commands covering happy paths, concurrency/transaction invariants, and authorization/error boundaries.

**Violating the letter of the Phase 1 Contract Gate is violating the spirit of this skill.**

---

## 1. Mode & Scale Routing (`双模式 × 三级规模路由`)

Not every task is a full database-backed backend. First classify the request along **Repository Mode** (`Mode 1` vs `Mode 2`) and **Task Scale** (`Scale L` / `Scale M` / `Scale S`), then expand only the contract sections the task genuinely needs.

```dot
digraph dev_skill_flow {
    rankdir=TB;
    "Receive development request" [shape=box];
    "Classify Mode (Mode 1 vs Mode 2)\n& Task Scale (Scale L / M / S)" [shape=diamond];
    "Scale L: Vague New Project / Full MVP\n(Full AGENTS.md + Task Plan + Contract)" [shape=box];
    "Scale M: Existing Repo New Feature\n(Repo Recon + Task Plan Whitelist + Incremental Contract)" [shape=box];
    "Scale S: Clear Micro-Fix / CLI / Pure Frontend / Algorithm\n(Concise Impact & I/O Contract in Task Plan)" [shape=box];
    "Human owner confirmed\nPhase 1 artifacts?" [shape=diamond];
    "STOP & Wait for Confirmation\n(Zero unauthorized business code)" [shape=box];
    "Phase 2: Stepwise Implementation\n& Invariant / Regression Verification" [shape=box];
    "L3 Contract Change Needed\nduring Phase 2?" [shape=diamond];
    "Delivery Report with\nReproducible Verification Output" [shape=box];

    "Receive development request" -> "Classify Mode (Mode 1 vs Mode 2)\n& Task Scale (Scale L / M / S)";
    "Classify Mode (Mode 1 vs Mode 2)\n& Task Scale (Scale L / M / S)" -> "Scale L: Vague New Project / Full MVP\n(Full AGENTS.md + Task Plan + Contract)" [label="Mode 1 / Scale L"];
    "Classify Mode (Mode 1 vs Mode 2)\n& Task Scale (Scale L / M / S)" -> "Scale M: Existing Repo New Feature\n(Repo Recon + Task Plan Whitelist + Incremental Contract)" [label="Mode 2 / Scale M"];
    "Classify Mode (Mode 1 vs Mode 2)\n& Task Scale (Scale L / M / S)" -> "Scale S: Clear Micro-Fix / CLI / Pure Frontend / Algorithm\n(Concise Impact & I/O Contract in Task Plan)" [label="Scale S"];
    "Scale L: Vague New Project / Full MVP\n(Full AGENTS.md + Task Plan + Contract)" -> "Human owner confirmed\nPhase 1 artifacts?";
    "Scale M: Existing Repo New Feature\n(Repo Recon + Task Plan Whitelist + Incremental Contract)" -> "Human owner confirmed\nPhase 1 artifacts?";
    "Scale S: Clear Micro-Fix / CLI / Pure Frontend / Algorithm\n(Concise Impact & I/O Contract in Task Plan)" -> "Human owner confirmed\nPhase 1 artifacts?";
    "Human owner confirmed\nPhase 1 artifacts?" -> "STOP & Wait for Confirmation\n(Zero unauthorized business code)" [label="No / Pending"];
    "Human owner confirmed\nPhase 1 artifacts?" -> "Phase 2: Stepwise Implementation\n& Invariant / Regression Verification" [label="Yes (Approved)"];
    "Phase 2: Stepwise Implementation\n& Invariant / Regression Verification" -> "L3 Contract Change Needed\nduring Phase 2?";
    "L3 Contract Change Needed\nduring Phase 2?" -> "Human owner confirmed\nPhase 1 artifacts?" [label="Yes (Re-Gate)"];
    "L3 Contract Change Needed\nduring Phase 2?" -> "Delivery Report with\nReproducible Verification Output" [label="No (100% Aligned)"];
}
```

### 1.1 Repository Mode (`仓库起点模式`)

| Mode | Triggering Scenario | Mandatory First Action |
|---|---|---|
| **Mode 1 — 从零立项 (`Greenfield MVP`)** | Starting a new project or standalone service from an empty workspace or a single sentence (e.g., *"我要做后端的二手书交易模块"*). | Do **not** write business code. Generate root `AGENTS.md`, task plan `docs/tasks/<task-slug>.md`, and contract at `CONTRACT_PATH` (default `docs/contract.md`). |
| **Mode 2 — 已有仓库开发 (`Brownfield / Scoped Dev`)** | Adding a feature, submodule, or fix inside an existing repository. | **Pre-Contract Recon**: Inspect directory tree, dependency manifests, existing `AGENTS.md`, migrations/entities, and OpenAPI/interface docs. Preserve existing `AGENTS.md` long-term rules; put current task scope & file whitelist in `docs/tasks/<task-slug>.md` and incremental contract in `docs/contracts/<module>-contract.md`. |

### 1.2 Task Scale Triage (`任务规模三级路由 — 按需展开，拒绝过度模板化`)

Database tables, HTTP endpoints, and external service sections must be expanded **only as actually needed** by the task. Never invent fake database tables or REST endpoints just to fill a template.

| Scale | Task Type (`任务类型`) | Appropriate Workflow & Artifacts (`合适的流程与产物`) | Contract Sections to Expand (`按需展开范围`) |
|---|---|---|---|
| **Scale L** | **模糊的新项目 (`Vague New Project / Full MVP`)** | Full MVP convergence, architecture design, `AGENTS.md` + `docs/tasks/<task-slug>.md` + `docs/contract.md`, Phase 1 confirmation, then 3-step implementation (`templates/AGENTS.template.md` + `templates/contract.template.md`). | Full sections needed by the system: DB schema + state machine + invariants (if stateful), HTTP API / CLI / Agent JSON schema, and Mock boundaries. |
| **Scale M** | **已有项目的新功能 (`New Feature in Existing Repo`)** | Repository reconnaissance (`Recon`), preserve root `AGENTS.md` (incremental edit only if global rules change), create `docs/tasks/<module>.md` (scope + File Whitelist) and `docs/contracts/<module>-contract.md` (or reuse existing OpenAPI/migrations), confirm, then implement & run regression suite. | Only the new/modified tables, endpoints, or component props, plus upstream/downstream compatibility with existing modules. |
| **Scale S** | **边界明确的小修复 / 纯前端 / CLI / 算法模块 (`Clear Bugfix / Non-DB / Algorithm / CLI`)** | Concise impact note, file whitelist, input/output signature or behavioral invariant update, and targeted verification command inside `docs/tasks/<task-slug>.md` (`templates/task-plan.template.md`). | **Omit DB DDL and REST sections if not applicable.** Specify function/CLI/component inputs, outputs, error cases, and targeted test commands. |

---

## 2. Separation of Long-Term Rules vs. Task Plan (`长期规则与当轮任务解耦`)

To prevent multi-module collaboration in existing repositories from overwriting project-wide steering rules:

1. **`AGENTS.md` holds Long-Term Repository Rules (`仓库级长期规则`)**:
   - Tech stack, architectural layering, unified response/error envelope, global environment variables, and permanent coding red lines.
   - **Brownfield Preservation Rule**: If `AGENTS.md` already exists, **keep its existing constraints intact** and make only minimal incremental additions when global conventions change. Never rewrite the entire project's `AGENTS.md` for a single submodule task.
2. **`docs/tasks/<task-slug>.md` holds the Current Task Plan (`当轮任务范围、白名单与验收条件`)**:
   - Use `templates/task-plan.template.md` to store the current iteration's MVP `In-Scope` / `Non-Goals`, **File Whitelist** (including dependency files like `requirements.txt` or `package.json` if dependencies change), explicit `CONTRACT_PATH` pointer, phase status, and step verification commands.
   - *(Note: For a standalone single-module Mode 1 exercise, the task plan block may either live in `docs/tasks/mvp-init.md` or be embedded in `AGENTS.md` §5, provided `CONTRACT_PATH` and the File Whitelist are explicitly declared.)*
3. **Reuse Existing Authoritative Specs (`复用已有权威契约与真源层级`)**:
   - If the repository already maintains OpenAPI/Swagger specs, SQL/Alembic/Prisma migrations, or shared protobuf/schema files, **reuse them first** and declare the **Source of Truth Hierarchy (`权威真源层级`)** in `AGENTS.md` and `docs/tasks/<task-slug>.md` instead of creating conflicting duplicate schemas.
   - Always reference the active contract via a single explicit `CONTRACT_PATH` (e.g., `docs/contract.md` for single-module projects or `docs/contracts/<module>-contract.md` for multi-module repositories).

---

## 3. Phase 1 — Hard Contract Gate (`契约门禁：点头前绝不写业务代码`)

When receiving a development request, **STOP in Phase 1**. Produce the required Phase 1 artifacts for the task's Scale and wait for human confirmation.

### 3.1 Artifact Checklist (`AGENTS.md` + `docs/tasks/<task-slug>.md` + `CONTRACT_PATH`)

1. **`AGENTS.md` (Long-Term Steering Contract — `templates/AGENTS.template.md`)**
   - **Architecture & Directory Structure**: Battle-tested, locally runnable stack, layered responsibilities, and file-level directory structure.
   - **Source of Truth Hierarchy & `CONTRACT_PATH`**: Explicit pointer to `CONTRACT_PATH` and `TASK_PLAN_PATH`, plus precedence rules when OpenAPI or DB migrations exist.
   - **Global Environment & Verification Conventions**: Runtime/DB versions, `.env.example` variable table, quickstart commands, and SQLite/DB connection rules (e.g., `PRAGMA foreign_keys = ON`).
   - **Long-Term Guardrails & Contract Change Protocol**: Coding conventions, L1/L2/L3 contract change rules, and anti-hallucination red lines.

2. **`docs/tasks/<task-slug>.md` (Task Scope, Whitelist & Verification Plan — `templates/task-plan.template.md`)**
   - **Task Metadata**: `TASK_ID`, `MODE`, `SCALE` (`L/M/S`), `CONTRACT_PATH`, and `PHASE_STATUS`.
   - **In-Scope Actions & Non-Goals**: Concrete verifiable actions and explicit exclusions.
   - **File Whitelist & Read-Only Boundaries**: Every file allowed to be created or modified (must include `requirements.txt` / `package.json` if dependencies are added/updated).
   - **Stepwise Verification Commands**: Exact commands for Step 1, Step 2, and Step 3.

3. **`CONTRACT_PATH` (`docs/contract.md` or `docs/contracts/<module>-contract.md` — `templates/contract.template.md`)**
   - **Database Schema & Enforcement Layer** *(when DB is involved)*:
     - **Field Dictionary**: Column name, type/length, nullable, default, key/index name, **Enforcement Layer (`保证层`: `DB Constraint` / `Request Validation` / `Service Invariant`)**, and business description.
     - **100% Template & DDL Self-Consistency**: Every named index (`idx_*`, `uk_*`), field length/constraint, and status enum declared in the Field Dictionary must match the executable SQL DDL and API validation rules 100%.
     - **State Enums & Complete Transition Matrix**: Every status value declared in the Field Dictionary (including non-happy-path states like `OFF_SHELF` or `CANCELLED`) must have defined entry conditions (`From`), exit rules (`To`), terminal/non-terminal markers, and cross-table side effects.
     - **Database Connection Enforcement Notes**: For SQLite, explicitly mandate `PRAGMA foreign_keys = ON;` on every database connection initialization so foreign key constraints are actually enforced at runtime.
   - **Core Business Invariants, Concurrency & Authorization Rules (§1.5 Mandatory for Stateful Logic)**:
     - See Section 4 below.
   - **API / I/O Contract & Integration Boundaries**:
     - Unified response envelope, business error codes, request/response examples, and explicit `REAL` vs `MOCK` boundaries.

### 3.2 Phase 1 Gate Stop Condition

After generating or updating the Phase 1 artifacts:
- **Do NOT create or modify any `.py`, `.ts`, `.js`, `.java`, `.go`, or business implementation files.**
- Ask the human owner to confirm the scope, file whitelist, data/API contracts, and business invariants before entering Phase 2.

---

## 4. Verifiable Business Invariants (`可验证业务不变量、并发事务与权限边界`)

For any module involving state transitions, inventory/resource locking, or multi-user actions, `CONTRACT_PATH` (§1.5) and Phase 2 tests **must** explicitly define and verify these four invariant categories, specifying the **Enforcement Layer (`DB Constraint` + `Request Validation` + `Service Invariant`)** for each:

1. **Uniqueness & Contention Invariant (`唯一有效状态/防重锁定不变量`)**:
   - Example: *A single book may have at most ONE active (`PENDING`) order at any time.*
   - Enforced by: `DB Constraint` (e.g., partial unique index `uk_orders_active_book ON orders(book_id) WHERE status = 'PENDING'`) **AND** `Service Invariant` (conditional atomic update `UPDATE books SET status = 'RESERVED' WHERE id = ? AND status = 'ON_SALE'` verifying `rowcount == 1`).
2. **Transactional Atomicity & Rollback Invariant (`跨表同事务原子性与回滚不变量`)**:
   - Resource locking (`books.status: ON_SALE -> RESERVED`) and order/record creation (`INSERT INTO orders`) **must execute in the same database transaction**. If any step fails, the entire transaction rolls back so resources never remain orphaned in a locked state.
3. **Targeted Release & State Consistency Invariant (`精准释放与状态回滚不变量`)**:
   - Cancelling an order (`PENDING -> CANCELLED`) may only release the lock on the specific resource bound to that order, and only when the resource is currently in the expected locked state (`RESERVED -> ON_SALE`).
   - Repeat operations on terminal states (`COMPLETED`, `CANCELLED`, `SOLD`) must be rejected with an explicit conflict error code (`40903 INVALID_ORDER_TRANSITION`).
4. **Mock Identity vs. Authorization Boundary (`模拟身份传递与操作权限规则分离`)**:
   - Even when an MVP uses simplified/mock authentication (no OAuth2/JWT), the contract must separately specify:
     - **Mock Identity Carrier (`模拟身份传递方式`)**: e.g., HTTP Header `X-User-Id` or request body field `seller_id` / `buyer_id` / `operator_id`.
     - **Authorization Rules (`操作权限判定规则`)**: Who is allowed to perform each state change (e.g., only `books.seller_id` may off-shelf/re-list a book; only the order's `buyer_id` or `seller_id` may complete or cancel the order; `buyer_id != seller_id` on order creation). Unauthorized callers must receive a deterministic error (`HTTP 403` / `40301 FORBIDDEN_NOT_OWNER`).

---

## 5. Phase 2 — Stepwise Coding & Contract Change Protocol (`分步开发与契约变更协议`)

Enter Phase 2 **only after** human confirmation of Phase 1.

### 5.1 Three Verifiable Steps (Adapted by Scale)

- **Step 1: Environment, Skeleton & Schema (`环境骨架与数据层`)**
  - Create `.env.example`, dependency manifest (`requirements.txt` / `package.json`), and schema/models matching `CONTRACT_PATH` 100% (including `PRAGMA foreign_keys = ON` per connection for SQLite).
  - Run Step 1 verification command (schema DDL execution, FK check, model import).
- **Step 2: Core Service, Invariants & Endpoints (`核心业务、不变量与接口实现`)**
  - Implement service logic and endpoints within the approved **File Whitelist**.
  - Run Step 2 automated tests covering **not only happy paths**, but specifically:
    1. Concurrent / conditional lock contention (`40901`);
    2. Transaction failure atomic rollback (no orphan lock on insert failure);
    3. Unauthorized operator rejection (`40301`);
    4. Repeat transition on terminal state (`40903`) and foreign key enforcement.
- **Step 3: Runtime & End-to-End Smoke Verification (`真实运行与端到端验收`)**
  - Run the live service or reproducible test runner and record actual terminal output.
  - **Honesty Red Line**: If any test or verification command fails, **never claim completion**. Report the exact failure output, fix the root cause, and re-run until green.

### 5.2 Three-Tier Contract Synchronization Protocol (`契约变更三级确认边界`)

To prevent an agent from silently editing `CONTRACT_PATH` during Phase 2 and then claiming *"code matches the new contract 100%"*, all mid-flight adjustments are governed by three strict tiers:

| Tier | Change Type (`变更类型`) | Examples (`具体表现`) | Mandatory Handling (`默认处理规则`) |
|---|---|---|---|
| **L1** | **Clarification / Editorial (`修正文案、补充示例，不改变行为`)** | Fixing typos, adding request/response JSON examples, clarifying field descriptions without altering any field name, type, length, enum, route, or invariant. | **Direct Sync (`直接同步`)**: Update `CONTRACT_PATH` directly and note the editorial sync in the delivery summary. |
| **L2** | **Internal Implementation Detail (`实现细节调整，不改变对外约定`)** | Extracting private helper functions, internal query tuning, or code comments within the approved File Whitelist and schema. | **Execute in Scope (`在已授权范围内执行`)**: Proceed without changing external contracts or pausing workflow. |
| **L3** | **Breaking / Behavioral / Scope Change (`删除/修改字段、改变状态流转或权限、扩大范围或白名单`)** | Adding/removing/renaming columns or JSON fields, changing field types/lengths/semantics, altering state transitions or auth rules, changing error codes, or touching files outside the File Whitelist. | **Mandatory Re-Gate (`提交具体差异，重新确认受影响部分`)**: **STOP coding.** Present the exact contract diff and impact analysis to the human owner and wait for explicit re-approval before modifying implementation code. |

---

## 6. Common Anti-Patterns & Rationalization Counter-Table

| # | Anti-Pattern (`常见翻车点`) | `dev-skill` Interception Rule |
|---|---|---|
| **1** | **Zero-Contract Code Dump (`不写契约直接吐代码`)** | **Phase 1 Gate**: Zero business code before `AGENTS.md` / `docs/tasks/<task>.md` and `CONTRACT_PATH` are confirmed. |
| **2** | **Template Overkill on Small Tasks (`小改动硬套重型后端模板`)** | **Scale S / M Routing**: Use `Scale S` for bugfixes, CLI tools, or pure frontend/algorithm modules; never invent fake tables or HTTP endpoints. |
| **3** | **Self-Approved Contract Drift (`私改契约伪装 100% 对齐`)** | **L3 Re-Gate Protocol**: Any change to field semantics, state transitions, auth rules, or scope requires human re-confirmation first. |
| **4** | **Overwrite Global `AGENTS.md` in Brownfield (`新增子模块覆盖全局规则`)** | **Long-Term vs. Task Split**: Keep long-term repo rules in `AGENTS.md`; put current task scope and File Whitelist in `docs/tasks/<task-slug>.md`. |
| **5** | **Fake-Done Stubs or False-Green Claims (`假数据桩代码或测试失败仍报完成`)** | **Step 2/3 Invariant & Workspace Evaluation**: Verify atomic transactions, FK enforcement, and real test outputs via `tests/evaluate_workspace.py`. |

| Excuse (`AI 常见借口`) | Reality (`工程铁律`) |
|---|---|
| *"I updated `docs/contract.md` myself to drop that tricky field, so code and contract are 100% aligned."* | Deleting a field or changing state transitions is an **L3 change**. Self-modifying the contract without human re-confirmation is a contract violation. |
| *"SQLite created the tables without error, so foreign keys are working."* | SQLite disables `PRAGMA foreign_keys` by default on every new connection. You must enable `PRAGMA foreign_keys = ON` per connection and verify it in tests. |
| *"Testing sequential duplicate orders is enough to prove locking works."* | Sequential rejection does not prove transactional rollback or ownership rules. Test atomic conditional update (`rowcount == 1`), rollback on failure, `40301` unauthorized calls, and `40903` terminal state retries. |

---

## 7. Pre-Completion Verification Checklist (`交付前自检清单`)

### Phase 1 Gate Checklist (Before Asking Human to Confirm)
- [ ] Mode (`Mode 1` / `Mode 2`) and Scale (`Scale L` / `Scale M` / `Scale S`) explicitly identified.
- [ ] In Mode 2, existing `AGENTS.md`, OpenAPI specs, and migrations were inspected and preserved; task scope and File Whitelist are isolated in `docs/tasks/<task-slug>.md`.
- [ ] `CONTRACT_PATH` is explicitly declared and consistent across `AGENTS.md` and `docs/tasks/<task-slug>.md`.
- [ ] In `CONTRACT_PATH`, all Field Dictionary indexes (`idx_*`, `uk_*`), field lengths, and status enums (including `OFF_SHELF` / `CANCELLED`) match the SQL DDL and API validation 100%, with each rule's **Enforcement Layer** (`DB Constraint` / `Request Validation` / `Service Invariant`) labeled.
- [ ] **Zero** unauthorized business implementation files created or modified yet.

### Phase 2 Delivery Checklist (Before Claiming Development Complete)
- [ ] All modified/created files are strictly inside the approved **File Whitelist** (including `requirements.txt` / dependency files).
- [ ] Code matches `CONTRACT_PATH` 100%; any L3 contract change was explicitly re-approved by the human owner before implementation.
- [ ] Stateful logic enforces all 4 Business Invariants (single active order, same-transaction lock + insert with rollback, targeted lock release, and explicit owner authorization `40301`).
- [ ] Step 1, Step 2, and Step 3 verification commands were executed with all tests passing (zero unreported failures or `TODO` stubs).

---

## 8. Templates, Reproducible Examples & Verification Suite

- `templates/AGENTS.template.md` — Template for repository-level `AGENTS.md` steering rules and `CONTRACT_PATH` hierarchy.
- `templates/task-plan.template.md` — Template for per-task scope, Scale routing (`L/M/S`), File Whitelist, and verification plan (`docs/tasks/<task-slug>.md`).
- `templates/contract.template.md` — Self-consistent template for `CONTRACT_PATH` (`docs/contract.md` or `docs/contracts/<module>-contract.md`) with Enforcement Layers, SQLite FK pragma, full state transitions, and Business Invariants.
- `examples/one-sentence-to-mvp.md` — End-to-end walkthrough demonstration (with explicit evidence boundary notes) + link to the runnable minimal reproduction.
- `examples/minimal-repro/` — Zero-dependency runnable Python + SQLite implementation and invariant test suite (`python3 -m unittest discover -s examples/minimal-repro -v`).
- `tests/validate_structure.py` — Layer 1 deep structural, YAML schema, and template consistency validator (`python3 tests/validate_structure.py`).
- `tests/evaluate_workspace.py` — Layer 2 behavioral workspace evaluator checking Phase 1 gate compliance, Mode 2 file whitelist isolation, contract alignment, and test failure honesty (`python3 tests/evaluate_workspace.py --self-test`).
- `CHANGELOG.md` — Version history (`v1.0.0` -> `v1.1.0`).
