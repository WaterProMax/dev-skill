# 数据表字段、业务不变量与接口对接契约（`CONTRACT_PATH`）

> **文档性质**：本文件由 `dev-skill` 在 **Phase 1（契约门禁阶段）** 生成，是前后端联调、跨模块对接及 AI 编码的 **唯一真相源（Single Source of Truth）**。  
> **路径约定（`CONTRACT_PATH`）**：单模块项目默认存放于 `docs/contract.md`；多模块或已有仓库（Mode 2）统一存放于 `docs/contracts/<module>-contract.md`，并在 `AGENTS.md` 与 `docs/tasks/<task-slug>.md` 中通过 `CONTRACT_PATH` 显式引用。  
> **对齐与变更铁律**：实现代码中的物理表名、字段名、长度约束、索引名、状态枚举、业务不变量、路由路径与错误码必须与本文件 **100% 一致**。任何涉及删除/修改字段、改变状态流转或权限边界的变更（**L3 变更**）必须先提交具体差异并重新获得人工确认后才准改代码。

- **所属项目/模块**：`<填写项目或模块名，例如：校园二手书交易模块>`
- **关联长期总控文件**：`AGENTS.md`
- **关联当轮任务单（`TASK_PLAN_PATH`）**：`docs/tasks/<task-slug>.md`
- **当前契约路径（`CONTRACT_PATH`）**：`docs/contract.md`（或 `docs/contracts/<module>-contract.md`）
- **接口基础路径（Base URL / Prefix）**：`/api/v1`
- **数据交换格式**：`application/json; charset=utf-8`
- **时间与金额约定**：
  - 时间字段统一使用 **ISO-8601 字符串（带时区，如 `2026-10-26T19:00:00+08:00`）**
  - 金额字段统一使用 **整数「分（cents）」** 存储与传输（例如 `3500` 表示 `35.00 元`），严禁使用浮点数存储金额。
- **保证层（Enforcement Layer）三级定义**：
  - `DB Constraint`：由数据库引擎强制保证（`PRIMARY KEY`、`FOREIGN KEY` + `PRAGMA foreign_keys = ON`、`NOT NULL`、`UNIQUE`、`CHECK`、部分唯一索引）。
  - `Request Validation`：由 API 路由/Schema 层在进入业务逻辑前拦截（字段必填、字符串长度、正整数范围、枚举值集合）。
  - `Service Invariant`：由业务服务层在数据库事务内强制保证（条件原子更新 `rowcount == 1`、跨表同事务回滚、归属人权限校验 `40301`、状态机前置状态校验）。

---

## 1. 数据库与字段设计（Database Schema — Scale S 无数据库任务可裁剪本节）

### 1.1 表清单概览（Tables Overview）

| 物理表名 | 中文名称 | 核心用途 | 主键 | 外键与关联关系 |
|---|---|---|---|---|
| `books` | 二手教材表 | 存储卖家发布的教材信息、成色、价格与当前库存状态 | `id` | 被 `orders.book_id` 外键关联 |
| `orders` | 交易订单表 | 存储买家下单记录、快照金额与订单履约状态 | `id` | 外键 `book_id -> books.id`（连接必开 `PRAGMA foreign_keys = ON`） |

### 1.2 表字段字典（Field Dictionary — 索引名与长度必须与 §1.4 SQL 及 §2.2 接口 100% 一致）

#### 表 1：`books`（二手教材表）

| 字段名 (Column) | 类型与长度 (Type) | 必填 (NOT NULL) | 默认值 (Default) | 约束与索引名称 (Key / Index) | 保证层 (Enforcement Layer) | 业务含义与规则说明 (Description) |
|---|---|---|---|---|---|---|
| `id` | `INTEGER` | 是 | 自增 (`AUTOINCREMENT`) | `PRIMARY KEY` | `DB Constraint` | 教材唯一主键 ID |
| `title` | `VARCHAR(128)` | 是 | 无 | `INDEX idx_books_title`, `CHECK (length(trim(title)) BETWEEN 1 AND 128)` | `DB Constraint` + `Request Validation` | 教材名称（非空，去除首尾空白后长度 1~128 字符） |
| `isbn` | `VARCHAR(20)` | 是 | 无 | `INDEX idx_books_isbn`, `CHECK (length(isbn) BETWEEN 10 AND 20)` | `DB Constraint` + `Request Validation` | 标准书号 ISBN（长度 10~20 字符，支持标准 10 位或 13 位 ISBN 及可选连字符 `-`） |
| `seller_id` | `VARCHAR(64)` | 是 | 无 | `INDEX idx_books_seller`, `CHECK (length(trim(seller_id)) > 0)` | `DB Constraint` + `Request Validation` | 卖家用户标识（学号或用户 ID，仅本人可执行下架/重新上架） |
| `price_cents` | `INTEGER` | 是 | 无 | `CHECK (price_cents > 0)` | `DB Constraint` + `Request Validation` | 售价（单位：分，必须为正整数 `> 0`） |
| `condition_level` | `VARCHAR(16)` | 是 | `'GOOD'` | `CHECK (condition_level IN ('NEW', 'LIKE_NEW', 'GOOD', 'ACCEPTABLE'))` | `DB Constraint` + `Request Validation` | 成色枚举：`NEW` / `LIKE_NEW` / `GOOD` / `ACCEPTABLE` |
| `status` | `VARCHAR(16)` | 是 | `'ON_SALE'` | `INDEX idx_books_status`, `CHECK (status IN ('ON_SALE', 'RESERVED', 'SOLD', 'OFF_SHELF'))` | `DB Constraint` + `Service Invariant` | 教材状态枚举：`ON_SALE` / `RESERVED` / `SOLD` / `OFF_SHELF` |
| `created_at` | `TEXT` | 是 | `datetime('now')` | 普通字段 | `DB Constraint` | 创建时间（ISO-8601 / UTC） |
| `updated_at` | `TEXT` | 是 | `datetime('now')` | 普通字段 | `DB Constraint` + `Service Invariant` | 最后更新时间 |

#### 表 2：`orders`（交易订单表）

| 字段名 (Column) | 类型与长度 (Type) | 必填 (NOT NULL) | 默认值 (Default) | 约束与索引名称 (Key / Index) | 保证层 (Enforcement Layer) | 业务含义与规则说明 (Description) |
|---|---|---|---|---|---|---|
| `id` | `INTEGER` | 是 | 自增 (`AUTOINCREMENT`) | `PRIMARY KEY` | `DB Constraint` | 订单唯一主键 ID |
| `order_no` | `VARCHAR(40)` | 是 | 无 | `UNIQUE INDEX uk_orders_order_no` | `DB Constraint` + `Service Invariant` | 业务订单号（格式：`ORD` + 时间戳 + 随机序列，全局唯一） |
| `book_id` | `INTEGER` | 是 | 无 | `FOREIGN KEY -> books.id`, `INDEX idx_orders_book_id`, `UNIQUE INDEX uk_orders_active_book (WHERE status = 'PENDING')` | `DB Constraint` + `Service Invariant` | 关联教材 ID；部分唯一索引强制同一本书最多存在一个 `PENDING` 订单 |
| `buyer_id` | `VARCHAR(64)` | 是 | 无 | `INDEX idx_orders_buyer_id`, `CHECK (length(trim(buyer_id)) > 0)` | `DB Constraint` + `Request Validation` + `Service Invariant` | 买家用户标识（Service 层强制校验 `buyer_id != books.seller_id`） |
| `amount_cents` | `INTEGER` | 是 | 无 | `CHECK (amount_cents > 0)` | `DB Constraint` + `Service Invariant` | 下单快照金额（单位：分，事务内取下单时刻 `books.price_cents`） |
| `status` | `VARCHAR(16)` | 是 | `'PENDING'` | `INDEX idx_orders_status`, `CHECK (status IN ('PENDING', 'COMPLETED', 'CANCELLED'))` | `DB Constraint` + `Service Invariant` | 订单状态枚举：`PENDING` / `COMPLETED` / `CANCELLED` |
| `created_at` | `TEXT` | 是 | `datetime('now')` | 普通字段 | `DB Constraint` | 下单时间 |
| `updated_at` | `TEXT` | 是 | `datetime('now')` | 普通字段 | `DB Constraint` + `Service Invariant` | 状态变更时间 |

### 1.3 状态枚举与状态机流转约定（State Enums & Complete Transition Matrix）

> **完整性铁律**：§1.2 字段字典中出现的每一个状态枚举值（含 `OFF_SHELF`、`CANCELLED` 等非主链路状态），都必须在下表中明确定义 **如何进入（Allowed From）**、**能否退出（Allowed To / 是否终态）**、**操作权限要求** 以及 **保证层**。（若项目采用整型枚举如 `0=ON_SALE, 1=LOCKED, 2=SOLD, 3=OFF_SHELF`，同样必须在字典与下表中 100% 对应。）

| 所属表.字段 | 枚举值 | 状态性质 | 允许从哪个状态进入 (Allowed From) | 允许流转到哪个状态 (Allowed To) | 操作权限与跨表联动规则 | 保证层 (Enforcement Layer) |
|---|---|---|---|---|---|---|
| `books.status` | `ON_SALE` | 非终态（在售） | 初始创建 / `RESERVED`（订单取消释放） / `OFF_SHELF`（卖家重新上架） | `RESERVED`（买家下单） / `OFF_SHELF`（卖家下架） | 发布教材默认状态；或 `PENDING` 订单取消后回滚恢复；或卖家本人重新上架 | `DB Constraint` + `Service Invariant` |
| `books.status` | `RESERVED` | 非终态（已锁定） | 仅 `ON_SALE` | `SOLD`（订单完成） / `ON_SALE`（订单取消） | 买家创建订单时同事务条件更新（`WHERE id=? AND status='ON_SALE'` 且 `rowcount==1`）；**锁定期间禁止卖家直接下架（返回 `40902`）** | `Service Invariant` + `DB Constraint` |
| `books.status` | `SOLD` | **终态（已售出）** | 仅 `RESERVED` | **无（终态，不可退出）** | 关联订单流转为 `COMPLETED` 时同事务更新为 `SOLD`；终态不可再下单或上下架 | `Service Invariant` |
| `books.status` | `OFF_SHELF` | 非终态（已下架） | 仅 `ON_SALE` | 仅 `ON_SALE`（卖家重新上架） | **进入条件**：仅该书 `seller_id` 本人在 `ON_SALE` 状态下可下架（若为 `RESERVED`/`SOLD` 返回 `40902`）；**退出条件**：仅 `seller_id` 本人可重新上架回 `ON_SALE` | `Service Invariant` |
| `orders.status` | `PENDING` | 非终态（待交割） | 初始下单 | `COMPLETED` / `CANCELLED` | 仅当 `books.status == 'ON_SALE'` 且 `buyer_id != seller_id` 时同事务创建，同时锁定教材为 `RESERVED` | `Service Invariant` + `DB Constraint` |
| `orders.status` | `COMPLETED` | **终态（已完成）** | 仅 `PENDING` | **无（终态，不可退出）** | 仅该订单 `buyer_id` 或 `seller_id` 可触发；同事务将 `books.status` 从 `RESERVED` 更新为 `SOLD`；重复操作返回 `40903` | `Service Invariant` |
| `orders.status` | `CANCELLED` | **终态（已取消）** | 仅 `PENDING` | **无（终态，不可退出）** | 仅该订单 `buyer_id` 或 `seller_id` 可触发；同事务仅释放该单关联且处于 `RESERVED` 的教材回 `ON_SALE`；重复操作返回 `40903` | `Service Invariant` |

### 1.4 可直接执行的建表 SQL 与外键连接激活规范（Executable DDL & Connection Pragma）

#### 1.4.1 数据库连接初始化必配项（SQLite 外键约束强制开启）

> ⚠️ **关键工程陷阱提示**：SQLite 默认在每个新建数据库连接上关闭外键约束（`PRAGMA foreign_keys = OFF`）。即便 `CREATE TABLE` 写了 `FOREIGN KEY (book_id) REFERENCES books(id)`，若不在每次建立连接时开启该指令，依然可以插入指向不存在 `book_id` 的脏订单！  
> **强制规范**：应用代码必须在每个数据库连接初始化时显式执行 `PRAGMA foreign_keys = ON;`：
> - **Python `sqlite3` 标准库写法**：
>   ```python
>   conn = sqlite3.connect(db_path)
>   conn.execute("PRAGMA foreign_keys = ON;")
>   ```
> - **SQLAlchemy Engine 连接钩子写法**：
>   ```python
>   from sqlalchemy import event
>   from sqlalchemy.engine import Engine
>
>   @event.listens_for(Engine, "connect")
>   def set_sqlite_pragma(dbapi_connection, connection_record):
>       cursor = dbapi_connection.cursor()
>       cursor.execute("PRAGMA foreign_keys = ON;")
>       cursor.close()
>   ```

#### 1.4.2 建表与索引 DDL（与 §1.2 字段字典 100% 严丝合缝）

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(128) NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 128),
    isbn VARCHAR(20) NOT NULL CHECK (length(isbn) BETWEEN 10 AND 20),
    seller_id VARCHAR(64) NOT NULL CHECK (length(trim(seller_id)) > 0),
    price_cents INTEGER NOT NULL CHECK (price_cents > 0),
    condition_level VARCHAR(16) NOT NULL DEFAULT 'GOOD' CHECK (condition_level IN ('NEW', 'LIKE_NEW', 'GOOD', 'ACCEPTABLE')),
    status VARCHAR(16) NOT NULL DEFAULT 'ON_SALE' CHECK (status IN ('ON_SALE', 'RESERVED', 'SOLD', 'OFF_SHELF')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
CREATE INDEX IF NOT EXISTS idx_books_seller ON books(seller_id);
CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(40) NOT NULL,
    book_id INTEGER NOT NULL,
    buyer_id VARCHAR(64) NOT NULL CHECK (length(trim(buyer_id)) > 0),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    status VARCHAR(16) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'CANCELLED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_orders_order_no ON orders(order_no);
CREATE INDEX IF NOT EXISTS idx_orders_book_id ON orders(book_id);
CREATE UNIQUE INDEX IF NOT EXISTS uk_orders_active_book ON orders(book_id) WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
```

### 1.5 核心业务不变量、并发事务与操作权限规则（Verifiable Business Invariants & Auth Rules）

> **测试覆盖铁律**：Phase 2 的自动化测试必须针对以下 4 条不变量编写专门的验证用例（涵盖并发/条件更新锁抢占、事务中途失败回滚、非归属人越权操作 `40301`、终态重复操作 `40903`），绝不能只测顺序成功请求。

| 不变量编号 | 不变量名称 | 严格业务定义与实现要求 | 保证层 (Enforcement Layer) | 必测验证场景与预期错误码 |
|---|---|---|---|---|
| **INV-1** | **唯一有效待交易订单不变量** | 同一本教材（`book_id`）在同一时刻最多只能存在 **1 个** `status = 'PENDING'` 的有效待交易订单，严禁一书多卖。 | `DB Constraint`（部分唯一索引 `uk_orders_active_book`）+ `Service Invariant`（条件原子更新 `WHERE id = ? AND status = 'ON_SALE'` 且检查 `rowcount == 1`） | 两个买家针对同一本 `ON_SALE` 教材发起抢购或重复下单，仅第一个成功，后续请求必须返回 `40901 BOOK_NOT_AVAILABLE` |
| **INV-2** | **锁书与建单同事务原子性不变量** | 更新 `books.status = 'RESERVED'` 与插入 `orders` 记录必须在 **同一个数据库事务（Transaction）** 中执行；若订单写入或校验失败，必须整体回滚，教材状态必须保持 `ON_SALE`。 | `Service Invariant`（显式事务上下文 `with conn:`）+ `DB Constraint` | 模拟锁书成功后订单插入抛出异常（如违反约束），断言事务回滚后 `books.status` 仍为 `'ON_SALE'` 且无残留脏订单 |
| **INV-3** | **取消订单精准释放锁定不变量** | 取消订单（`PENDING -> CANCELLED`）只能释放 **该订单自身关联（`orders.book_id`）且当前处于 `'RESERVED'` 状态** 的教材回 `'ON_SALE'`；严禁误释放其他订单或已售出教材。 | `Service Invariant`（同事务内校验订单状态与 `books.status == 'RESERVED'`） | 订单取消后验证对应教材恢复 `'ON_SALE'`；对已 `CANCELLED` 或 `COMPLETED` 的终态订单再次调用取消/完成，必须返回 `40903 INVALID_ORDER_TRANSITION` |
| **INV-4** | **模拟身份与操作权限分离不变量** | **模拟身份传递方式**：MVP 阶段通过请求字段（`seller_id` / `buyer_id` / `operator_id`）或请求头 `X-User-Id` 传递当前操作人身份。<br>**操作权限判定规则**：<br>① 下架/重新上架教材：仅允许该教材的 `books.seller_id` 本人操作；<br>② 创建订单：`buyer_id` 严禁等于 `books.seller_id`（自买返回 `40002`）；<br>③ 完成/取消订单：仅允许该订单的 `orders.buyer_id` 或关联教材的 `books.seller_id` 操作。 | `Request Validation`（操作人标识非空）+ `Service Invariant`（归属权比对） | 路人账号（既非买家也非卖家）尝试取消/完成他人订单，或尝试下架他人教材，必须被拦截并返回 HTTP `403` / `40301 FORBIDDEN_NOT_OWNER` |

---

## 2. 接口对接契约（API Contract — Scale S 非 HTTP 任务可替换为函数/CLI 契约）

### 2.1 统一响应信封与错误码字典（Unified Envelope & Error Codes）

所有接口统一返回以下 JSON 结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

| HTTP 状态码 | 业务错误码 (`code`) | 英文标识 / 含义 | 触发场景说明 | 保证层 (Enforcement Layer) |
|---|---|---|---|---|
| `200` / `201` | `0` | `OK` | 请求成功 | - |
| `400` | `40001` | `INVALID_ARGUMENT` | 必填字段缺失、`isbn` 长度不在 `10~20` 字符内、价格 `<= 0`、非法枚举值 | `Request Validation` + `DB Constraint` |
| `400` | `40002` | `SELF_PURCHASE_FORBIDDEN` | 买家 `buyer_id` 与该书卖家 `seller_id` 相同 | `Service Invariant` |
| `403` | `40301` | `FORBIDDEN_NOT_OWNER` | 当前 `operator_id` 无权操作该教材（非卖家本人上下架）或无权操作该订单（非该单买/卖家） | `Service Invariant` |
| `404` | `40401` | `RESOURCE_NOT_FOUND` | 指定的 `book_id` 或 `order_id` 不存在（或外键引用的教材不存在） | `Service Invariant` + `DB Constraint` |
| `409` | `40901` | `BOOK_NOT_AVAILABLE` | 教材当前状态不是 `ON_SALE`（已处于 `RESERVED`、`SOLD` 或 `OFF_SHELF`） | `Service Invariant` + `DB Constraint` |
| `409` | `40902` | `BOOK_STATUS_CONFLICT` | 教材当前处于 `RESERVED` 或 `SOLD`，禁止卖家直接执行下架或重复上架 | `Service Invariant` |
| `409` | `40903` | `INVALID_ORDER_TRANSITION` | 订单已处于 `COMPLETED` 或 `CANCELLED` 终态，禁止重复完成或重复取消 | `Service Invariant` |
| `500` | `50000` | `INTERNAL_ERROR` | 服务端未预期异常（事务已自动回滚） | `Service Invariant` |

---

### 2.2 接口明细列表（Endpoint Specifications）

#### 接口 1：`POST /api/v1/books` — 发布二手教材

- **模拟身份与权限**：请求体传入 `seller_id`（非空字符串）作为教材归属卖家。
- **请求参数（JSON Body — 与 §1.2 字段字典 100% 对齐）**：

| 字段名 | 类型 | 必填 | 校验规则与说明 | 保证层 (Enforcement Layer) |
|---|---|---|---|---|
| `title` | `string` | 是 | 去除首尾空白后 1~128 字符 | `Request Validation` + `DB Constraint` |
| `isbn` | `string` | 是 | 长度 10~20 字符（支持标准 10 位或 13 位 ISBN，允许数字、`X` 及可选连字符 `-`） | `Request Validation` + `DB Constraint` |
| `seller_id` | `string` | 是 | 非空字符串，1~64 字符 | `Request Validation` + `DB Constraint` |
| `price_cents` | `integer` | 是 | 正整数（`> 0`），单位：分 | `Request Validation` + `DB Constraint` |
| `condition_level` | `string` | 否 | 默认 `"GOOD"`，可选 `NEW` / `LIKE_NEW` / `GOOD` / `ACCEPTABLE` | `Request Validation` + `DB Constraint` |

- **请求示例**：
  ```json
  {
    "title": "深入理解计算机系统（原书第3版）",
    "isbn": "978-7-111-54493-7",
    "seller_id": "stu_2026001",
    "price_cents": 3500,
    "condition_level": "LIKE_NEW"
  }
  ```
- **成功响应示例（HTTP `201`）**：
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": 1,
      "title": "深入理解计算机系统（原书第3版）",
      "isbn": "978-7-111-54493-7",
      "seller_id": "stu_2026001",
      "price_cents": 3500,
      "condition_level": "LIKE_NEW",
      "status": "ON_SALE",
      "created_at": "2026-10-26T19:00:00+08:00"
    }
  }
  ```

---

#### 接口 2：`POST /api/v1/books/{book_id}/shelf` — 卖家下架/重新上架教材（覆盖 `OFF_SHELF` 流转）

- **模拟身份与权限**：请求体传入 `operator_id`；Service 层强制校验 `operator_id == books.seller_id`，否则返回 HTTP `403` / `code: 40301`。
- **请求参数（JSON Body）**：
  - `action`（必填，`string`，枚举值：`"OFF_SHELF"` 下架 | `"ON_SALE"` 重新上架）
  - `operator_id`（必填，`string`，操作人用户 ID）
- **状态流转约束**：
  - `"OFF_SHELF"`：仅允许从 `ON_SALE -> OFF_SHELF`；若当前为 `RESERVED` 或 `SOLD`，返回 HTTP `409` / `code: 40902`。
  - `"ON_SALE"`：仅允许从 `OFF_SHELF -> ON_SALE`；若当前非 `OFF_SHELF`，返回 HTTP `409` / `code: 40902`。
- **请求示例**：
  ```json
  {
    "action": "OFF_SHELF",
    "operator_id": "stu_2026001"
  }
  ```
- **成功响应示例（HTTP `200`）**：
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": 1,
      "status": "OFF_SHELF",
      "updated_at": "2026-10-26T19:02:00+08:00"
    }
  }
  ```

---

#### 接口 3：`GET /api/v1/books` — 查询教材列表

- **Query 参数**：
  - `status`（可选，`string`，可选 `ON_SALE` / `RESERVED` / `SOLD` / `OFF_SHELF`）
  - `keyword`（可选，`string`，按 `title` 或 `isbn` 模糊匹配）
  - `page`（可选，`integer`，默认 `1`）
  - `page_size`（可选，`integer`，默认 `20`，最大 `100`）
- **成功响应示例（HTTP `200`）**：
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "total": 1,
      "page": 1,
      "page_size": 20,
      "items": [
        {
          "id": 1,
          "title": "深入理解计算机系统（原书第3版）",
          "isbn": "978-7-111-54493-7",
          "seller_id": "stu_2026001",
          "price_cents": 3500,
          "condition_level": "LIKE_NEW",
          "status": "ON_SALE",
          "created_at": "2026-10-26T19:00:00+08:00"
        }
      ]
    }
  }
  ```

---

#### 接口 4：`POST /api/v1/orders` — 买家创建订单（同事务原子锁书）

- **模拟身份与权限**：请求体传入 `buyer_id`；Service 层强制校验 `buyer_id != books.seller_id`（否则返回 `40002`）。
- **请求示例**：
  ```json
  {
    "book_id": 1,
    "buyer_id": "stu_2026002"
  }
  ```
- **成功响应示例（HTTP `201`）**：
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": 101,
      "order_no": "ORD2026102619050001",
      "book_id": 1,
      "buyer_id": "stu_2026002",
      "amount_cents": 3500,
      "status": "PENDING",
      "book_status": "RESERVED",
      "created_at": "2026-10-26T19:05:00+08:00"
    }
  }
  ```
- **失败响应示例（教材已被锁定或下架，HTTP `409`）**：
  ```json
  {
    "code": 40901,
    "message": "Book is not available for purchase (current status: RESERVED)",
    "data": null
  }
  ```

---

#### 接口 5：`POST /api/v1/orders/{order_id}/transition` — 订单状态流转（完成/取消）

- **模拟身份与权限**：请求体传入 `operator_id`；仅允许该订单 `buyer_id` 或关联教材 `seller_id` 调用，任何第三方调用返回 HTTP `403` / `code: 40301`。
- **请求示例**：
  ```json
  {
    "action": "COMPLETE",
    "operator_id": "stu_2026002"
  }
  ```
  *（注：`action` 枚举为 `"COMPLETE"` 或 `"CANCEL"`；对已处于 `COMPLETED` 或 `CANCELLED` 的终态订单重复调用返回 HTTP `409` / `code: 40903`。）*
- **成功响应示例（HTTP `200`）**：
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": 101,
      "order_no": "ORD2026102619050001",
      "status": "COMPLETED",
      "book_id": 1,
      "book_status": "SOLD",
      "updated_at": "2026-10-26T19:10:00+08:00"
    }
  }
  ```
- **失败响应示例（非本单买/卖家越权操作，HTTP `403`）**：
  ```json
  {
    "code": 40301,
    "message": "Forbidden: operator stu_999999 is neither buyer nor seller of order 101",
    "data": null
  }
  ```

---

## 3. 外部/上下游对接与 Mock 边界说明（Integration & Mock Boundaries）

| 对接方 / 依赖项 | 对接方向 | 交互方式 / 协议 | 本轮实现状态 (`REAL` / `MOCK`) | 权限、事务与联调说明 |
|---|---|---|---|---|
| 前端客户端 / 小程序 | 上游调用方 | HTTP REST JSON (`/api/v1/*`) | `REAL` | 金额统一以整数「分」传输；错误统一解析 `code` 字段 |
| 本地关系型数据库 | 下游存储 | SQLite 3 (`PRAGMA foreign_keys = ON`) / MySQL | `REAL` | 真实落库、外键约束与同事务原子更新，严禁用内存列表替代 |
| 校园统一身份认证 (CAS) | 上游身份识别 | 请求字段 `seller_id` / `buyer_id` / `operator_id` | `MOCK`（仅身份载体模拟） | **注意区分**：身份获取采用显式传参模拟，但 **操作权限规则（`INV-4` 归属人校验 `40301`）为 `REAL` 真实强校验** |
| 第三方在线支付 | 下游外部服务 | 状态流转接口 `/orders/{id}/transition` | `MOCK`（显式声明） | MVP 阶段代表「线下交割确认」，不调用真实微信/支付宝商户网关 |
