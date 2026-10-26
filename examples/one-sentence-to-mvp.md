# 完整实战示范：从一句话「我要做后端的二手书交易模块」到可验收 MVP

> **证据边界声明（Walkthrough Format vs. Reproducible Code）**：  
> 1. **流程对话演示（本文档 §1～§2）**：展示 AI 在 `dev-skill` 约束下如何拦截一句话需求、产出 Phase 1 契约并汇报 Phase 2 验收结果的 **标准交互与报告格式示范**（其中 HTTP 服务日志为报告格式展示）。  
> 2. **真实可复现代码与测试证据（[`examples/minimal-repro/`](./minimal-repro/)）**：为确保契约 SQL、外键约束与四条业务不变量（`INV-1`～`INV-4`）可被任何人本地复现，仓库内置了零外部依赖的最小可运行实现与测试套件。你只需在仓库根目录运行以下命令即可亲眼验证全部 5 项不变量测试通过：
>    ```bash
>    python3 -m unittest discover -s examples/minimal-repro -v
>    ```

---

## 0. 对比：没有 `dev-skill` vs 启用 `dev-skill` (`v1.1.0`)

| 维度 | ❌ 没有 `dev-skill`（常见翻车现场） | ✅ 启用 `dev-skill`（本案例流程） |
|---|---|---|
| **收到一句话后的第一反应** | 立刻写 `main.py`、`jwt_auth.py`、`wx_pay.py` 等十几个文件 | **触发 Phase 1 硬门禁 + 规模路由（Mode 1 / Scale L）**：先生成 `AGENTS.md`、`docs/tasks/mvp-init.md` 与 `docs/contract.md` 请人确认 |
| **规则与契约自洽性** | 字段长度、索引名、状态枚举前后矛盾，SQLite 外键未开启 | 标注每条规则的 **保证层（DB / Request / Service）**，开启 `PRAGMA foreign_keys = ON`，状态机完整覆盖 `OFF_SHELF` |
| **并发、事务与权限边界** | 只测顺序成功请求，无事务回滚测试，谁都能取消别人的订单 | 明确定义并测试 **4 条业务不变量（`INV-1`～`INV-4`）**：同事务原子锁与回滚、部分唯一索引、归属人权限 `40301`、终态防重 `40903` |
| **中途契约变更治理** | AI 自己偷偷删改契约再宣称“代码与契约 100% 一致” | 执行 **三级契约变更协议（L1/L2/L3）**：新增字段或改行为属于 **L3 变更**，必须由人工确认后同步 |

---

## 1. Round 1：新手输入一句话 → AI 触发 Phase 1 契约门禁

### 👤 用户（组员）输入
> 「我要做后端的二手书交易模块」

---

### 🤖 AI 响应（Phase 1：判定 Mode 1 / Scale L，产出契约供确认）

收到！按 `dev-skill` 规范，这是一项 **Mode 1（从零立项）× Scale L（完整模块 MVP）** 任务。在确认契约前我们 **绝不编写任何业务实现代码**。

我已为你生成以下 Phase 1 契约文件初稿（根目录 `AGENTS.md`、当轮任务单 `docs/tasks/mvp-init.md` 与唯一数据/接口契约 `CONTRACT_PATH = docs/contract.md`）：

#### 📄 文件 1：`AGENTS.md` + `docs/tasks/mvp-init.md`（总控与当轮任务白名单摘要）
1. **MVP 最小闭环（4 个核心动作）**：
   - `发布与上下架教材`：卖家提交书名、ISBN（10~20 字符）、售价（分）、成色，入库为 `ON_SALE`；仅卖家本人可执行 `ON_SALE <-> OFF_SHELF` 上下架。
   - `检索教材`：支持按状态（`ON_SALE`）和关键词查询教材列表。
   - `同事务原子锁书与下单`：买家对 `ON_SALE` 教材下单，在 **同一数据库事务** 内条件更新教材为 `RESERVED`（`rowcount == 1`）并创建 `PENDING` 订单（失败整体回滚，禁止自买 `40002`）。
   - `带归属人权限的订单完成/取消`：仅该单 `buyer_id` 或 `seller_id` 可将 `PENDING` 订单流转为 `COMPLETED`（联动教材 `SOLD`）或 `CANCELLED`（仅释放该单关联的 `RESERVED` 教材回 `ON_SALE`）。
   - **本轮明确不做（Non-Goals）**：不做 OAuth2/JWT 认证中心（采用显式模拟身份参数 + 真实归属人权限校验 `40301`）、不接真实支付网关、不引 Redis/消息队列。
2. **文件白名单（File Whitelist）**：
   - 允许新建/修改：`AGENTS.md`、`docs/tasks/mvp-init.md`、`docs/contract.md`、`.env.example`、`requirements.txt`、`sql/schema.sql`、`app/**`、`tests/**`。
3. **环境与分步校验命令**：
   - 数据库连接强制开启 SQLite 外键：`PRAGMA foreign_keys = ON;`。
   - Step 1 建表与外键检查 → Step 2 业务不变量测试（含并发抢锁、事务回滚、越权 `40301`、终态重复 `40903`） → Step 3 端到端冒烟验证。

#### 📄 文件 2：`docs/contract.md`（数据库字段、状态机、不变量与接口契约摘要）
1. **核心数据表与索引（与 `schema.sql` 100% 对齐）**：
   - `books` 表：`id` (PK), `title` (`VARCHAR(128)`, `idx_books_title`), `isbn` (`VARCHAR(20)`, 长度 10~20, `idx_books_isbn`), `seller_id` (`VARCHAR(64)`, `idx_books_seller`), `price_cents` (`INTEGER > 0`), `condition_level` (`NEW`/`LIKE_NEW`/`GOOD`/`ACCEPTABLE`), `status` (`ON_SALE`/`RESERVED`/`SOLD`/`OFF_SHELF`, `idx_books_status`), `created_at`, `updated_at`。
   - `orders` 表：`id` (PK), `order_no` (`uk_orders_order_no`), `book_id` (`FK -> books.id`, `idx_orders_book_id`, 以及部分唯一索引 `uk_orders_active_book WHERE status = 'PENDING'`), `buyer_id` (`idx_orders_buyer_id`), `amount_cents` (`INTEGER > 0`), `status` (`PENDING`/`COMPLETED`/`CANCELLED`, `idx_orders_status`), `created_at`, `updated_at`。
2. **状态流转全覆盖（含 `OFF_SHELF`）**：
   - `ON_SALE -> OFF_SHELF`（仅卖家本人下架；`RESERVED`/`SOLD` 状态禁止下架，返回 `40902`）；`OFF_SHELF -> ON_SALE`（仅卖家本人重新上架）。
   - `SOLD`、`COMPLETED`、`CANCELLED` 为终态，重复流转统一返回 `40903 INVALID_ORDER_TRANSITION`。
3. **四条可验证业务不变量（`INV-1`～`INV-4`）**：
   - `INV-1`：同一本书最多存在一个 `PENDING` 订单（`DB Constraint: uk_orders_active_book` + `Service Invariant: rowcount == 1`，冲突返回 `40901`）。
   - `INV-2`：锁书与建单在同一事务内执行，任一步异常整体回滚。
   - `INV-3`：取消订单仅释放本单关联且处于 `RESERVED` 的教材；终态禁止重复操作（`40903`）。
   - `INV-4`：模拟身份通过 `seller_id`/`buyer_id`/`operator_id` 传递，非归属人操作统一返回 `40301 FORBIDDEN_NOT_OWNER`。

---

> 🛑 **Phase 1 契约门禁确认点（当前尚未编写任何业务代码）**  
> 请确认以下 3 件事，确认或提出修改意见后我再进入 Phase 2 分步编码：
> 1. 这 4 个核心动作与 `OFF_SHELF` 上下架边界符合预期吗？
> 2. `books` 和 `orders` 表的字段、索引与 4 条不变量有没有需要调整的（例如是否需要增加「适用课程名」）？
> 3. 接口路径与错误码（`40002` 自买、`40301` 越权、`40901` 已锁、`40902` 状态冲突、`40903` 终态重复）前端队友可以直接对接吗？

---

## 2. Round 2：用户确认并提出 L3 字段新增 → AI 同步契约后分步验收

### 👤 用户（组员）回复
> 「确认没问题！不过 `books` 表里帮我加一个可选字段 `course_name`（适用课程名，比如“计算机系统基础”），其他按这个直接开始写代码吧。」

---

### 🤖 AI 响应（Phase 2：L3 契约同步 → Step 1 → Step 2 → Step 3 真实校验交付）

收到用户确认与字段新增指令！按 **契约变更分级确认协议（L3 变更由负责人授权）**，我已先在 `docs/contract.md` 中同步补充 `course_name` 字段，随后严格在白名单范围内完成三步开发与不变量验证：

#### Step 0：先同步更新 `docs/contract.md`（契约即唯一真相）
- 在 `docs/contract.md` §1.2 `books` 表字段字典与 §1.4 `schema.sql` 中新增：
  - `course_name`：`VARCHAR(64)`，可空（`NULL`），默认 `NULL`，保证层为 `Request Validation`，含义为「适用课程名称」。

#### Step 1：环境骨架、SQLite 外键开启与 Schema 校验
运行仓库内可复现示例的数据库初始化与外键强校验：
```bash
$ sqlite3 :memory: "PRAGMA foreign_keys = ON; .read examples/minimal-repro/schema.sql"
```

#### Step 2：核心业务不变量（`INV-1`～`INV-4`）自动化测试（真实可复现输出）
在仓库根目录运行 `examples/minimal-repro` 测试套件：
```bash
$ python3 -m unittest discover -s examples/minimal-repro -v
test_01_sqlite_foreign_key_enforced (test_minimal_repro.MinimalReproInvariantTests.test_01_sqlite_foreign_key_enforced)
Verify PRAGMA foreign_keys = ON blocks inserting orders for non-existent books. ... ok
test_02_inv1_atomic_lock_and_duplicate_order_rejected_40901 (test_minimal_repro.MinimalReproInvariantTests.test_02_inv1_atomic_lock_and_duplicate_order_rejected_40901)
INV-1: At most one active PENDING order per book; duplicate lock returns 40901. ... ok
test_03_inv2_transaction_rollback_on_order_failure (test_minimal_repro.MinimalReproInvariantTests.test_03_inv2_transaction_rollback_on_order_failure)
INV-2: If order creation fails after locking book, transaction rolls back book to ON_SALE. ... ok
test_04_inv3_cancel_releases_only_target_book_and_blocks_terminal_retry_40903 (test_minimal_repro.MinimalReproInvariantTests.test_04_inv3_cancel_releases_only_target_book_and_blocks_terminal_retry_40903)
INV-3: Cancelling releases only the target book; repeating transition on terminal order returns 40903. ... ok
test_05_inv4_authorization_40301_and_self_purchase_40002_and_offshelf_40902 (test_minimal_repro.MinimalReproInvariantTests.test_05_inv4_authorization_40301_and_self_purchase_40002_and_offshelf_40902)
INV-4: Enforce owner permissions (40301), self-purchase block (40002), and OFF_SHELF transitions (40902). ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.006s

OK
```

#### Step 3：端到端核心闭环与异常错误码响应示范（报告格式展示）

1. **发布含 `course_name` 的教材（`POST /api/v1/books`）**：
   ```json
   {"code":0,"message":"ok","data":{"id":1,"title":"深入理解计算机系统（原书第3版）","isbn":"978-7-111-54493-7","course_name":"计算机系统基础","seller_id":"stu_seller_01","price_cents":3500,"condition_level":"LIKE_NEW","status":"ON_SALE"}}
   ```
2. **买家 `stu_buyer_01` 同事务下单锁书（`POST /api/v1/orders`）**：
   ```json
   {"code":0,"message":"ok","data":{"id":1,"order_no":"ORD8F3A1C9E2B4D6071","book_id":1,"buyer_id":"stu_buyer_01","amount_cents":3500,"status":"PENDING","book_status":"RESERVED"}}
   ```
3. **第二名买家抢购同一本已被锁定的书（验证 `INV-1` 返回 `40901`）**：
   ```json
   {"code":40901,"message":"Book is not available for purchase (current status: RESERVED)","data":null}
   ```
4. **无关路人 `stu_stranger` 尝试恶意取消他人订单（验证 `INV-4` 权限拦截返回 `40301`）**：
   ```json
   {"code":40301,"message":"Forbidden: operator stu_stranger is neither buyer nor seller of order 1","data":null}
   ```
5. **卖家确认交割完成（`POST /api/v1/orders/1/transition`）及终态重复调用拦截（`40903`）**：
   ```json
   {"code":0,"message":"ok","data":{"id":1,"order_no":"ORD8F3A1C9E2B4D6071","status":"COMPLETED","book_id":1,"book_status":"SOLD"}}
   ```
   ```json
   {"code":40903,"message":"Order 1 is already in terminal state COMPLETED","data":null}
   ```
