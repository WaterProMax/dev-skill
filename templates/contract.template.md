# 数据表字段与接口对接契约（`docs/contract.md`）

> **文档性质**：本文件由 `dev-skill` 在 **Phase 1（契约门禁阶段）** 生成，是前后端联调、跨模块对接及 AI 编码的 **唯一真相源（Single Source of Truth）**。  
> **对齐铁律**：实现代码中的物理表名、字段名、状态枚举、路由路径、请求/响应 JSON 键名必须与本文件 **100% 一致**。任何中途变更必须先更新本文件。

- **所属项目/模块**：`<填写项目或模块名>`
- **关联总控文件**：`AGENTS.md`
- **接口基础路径（Base URL / Prefix）**：`/api/v1`
- **数据交换格式**：`application/json; charset=utf-8`
- **时间与金额约定**：
  - 时间字段统一使用 **ISO-8601 字符串（带时区，如 `2026-10-26T19:00:00+08:00`）**
  - 金额字段统一使用 **整数「分（cents）」** 存储与传输（例如 `1500` 表示 `15.00 元`），避免浮点数精度丢失。

---

## 1. 数据库与字段设计（Database Schema）

### 1.1 表清单概览（Tables Overview）

| 物理表名 | 中文名称 | 核心用途 | 主键 | 关联关系 |
|---|---|---|---|---|
| `<table_1，如 books>` | `<二手教材表>` | `<存储卖家发布的教材信息与当前库存状态>` | `id` | 被 `<orders.book_id>` 关联 |
| `<table_2，如 orders>` | `<交易订单表>` | `<存储买家下单记录、交易金额与履约状态>` | `id` | 外键 `book_id -> books.id` |

### 1.2 表字段字典（Field Dictionary）

#### 表 1：`<books>`（`<二手教材表>`）

| 字段名 (Column) | 类型与长度 (Type) | 必填 (NOT NULL) | 默认值 (Default) | 约束/索引 (Key/Index) | 业务含义与规则说明 (Description) |
|---|---|---|---|---|---|
| `id` | `INTEGER / BIGINT` | 是 | 自增 (`AUTOINCREMENT`) | `PRIMARY KEY` | 教材唯一主键 ID |
| `title` | `VARCHAR(128)` | 是 | 无 | `INDEX idx_books_title` | 教材名称（非空，长度 1~128） |
| `isbn` | `VARCHAR(32)` | 是 | 无 | `INDEX idx_books_isbn` | 标准书号 ISBN（支持 10 位或 13 位） |
| `seller_id` | `VARCHAR(64)` | 是 | 无 | `INDEX idx_books_seller` | 卖家用户标识（学号或用户 ID） |
| `price_cents` | `INTEGER` | 是 | 无 | `CHECK (price_cents > 0)` | 售价（单位：分，必须为正整数） |
| `condition_level` | `VARCHAR(16)` | 是 | `'GOOD'` | 普通字段 | 成色枚举：`NEW` / `LIKE_NEW` / `GOOD` / `ACCEPTABLE` |
| `status` | `VARCHAR(16)` | 是 | `'ON_SALE'` | `INDEX idx_books_status` | 教材状态枚举：`ON_SALE` / `RESERVED` / `SOLD` / `OFF_SHELF` |
| `created_at` | `DATETIME / TEXT` | 是 | `CURRENT_TIMESTAMP` | 普通字段 | 创建时间 |
| `updated_at` | `DATETIME / TEXT` | 是 | `CURRENT_TIMESTAMP` | 普通字段 | 最后更新时间 |

#### 表 2：`<orders>`（`<交易订单表>`）

| 字段名 (Column) | 类型与长度 (Type) | 必填 (NOT NULL) | 默认值 (Default) | 约束/索引 (Key/Index) | 业务含义与规则说明 (Description) |
|---|---|---|---|---|---|
| `id` | `INTEGER / BIGINT` | 是 | 自增 (`AUTOINCREMENT`) | `PRIMARY KEY` | 订单唯一主键 ID |
| `order_no` | `VARCHAR(40)` | 是 | 无 | `UNIQUE INDEX uk_order_no` | 业务订单号（格式：`ORD` + 年月日时分秒 + 随机数） |
| `book_id` | `INTEGER / BIGINT` | 是 | 无 | `FOREIGN KEY -> books.id`, `INDEX` | 关联教材 ID |
| `buyer_id` | `VARCHAR(64)` | 是 | 无 | `INDEX idx_orders_buyer` | 买家用户标识（不能与该书 `seller_id` 相同） |
| `amount_cents` | `INTEGER` | 是 | 无 | `CHECK (amount_cents > 0)` | 下单快照金额（单位：分，取下单时 `books.price_cents`） |
| `status` | `VARCHAR(16)` | 是 | `'PENDING'` | `INDEX idx_orders_status` | 订单状态枚举：`PENDING` / `COMPLETED` / `CANCELLED` |
| `created_at` | `DATETIME / TEXT` | 是 | `CURRENT_TIMESTAMP` | 普通字段 | 下单时间 |
| `updated_at` | `DATETIME / TEXT` | 是 | `CURRENT_TIMESTAMP` | 普通字段 | 状态变更时间 |

### 1.3 状态枚举与状态机流转约定（State Enums & Transitions）

<!-- 填写说明：严禁只写 0/1/2 而不写含义；必须写清允许的前置状态和联动变更。 -->

| 所属表.字段 | 枚举值 | 含义 | 允许从哪个状态进入 (From) | 触发动作与跨表联动规则 |
|---|---|---|---|---|
| `books.status` | `ON_SALE` | 在售可下单 | 初始创建 / `RESERVED`（订单取消回滚） | 教材发布成功默认状态；或关联 `PENDING` 订单取消后自动释放 |
| `books.status` | `RESERVED` | 已被下单锁定 | `ON_SALE` | 买家创建订单时**原子更新**为 `RESERVED`，防止一书多卖 |
| `books.status` | `SOLD` | 已成交 | `RESERVED` | 关联订单确认为 `COMPLETED` 时联动更新为 `SOLD` |
| `orders.status` | `PENDING` | 待线下交割/确认 | 初始下单 | 仅当 `books.status == 'ON_SALE'` 且 `buyer_id != seller_id` 时可创建 |
| `orders.status` | `COMPLETED` | 交易完成 | `PENDING` | 触发 `books.status -> 'SOLD'`（终态，不可再变更） |
| `orders.status` | `CANCELLED` | 订单已取消 | `PENDING` | 触发 `books.status -> 'ON_SALE'`（终态，不可再变更） |

### 1.4 可直接执行的建表 SQL（Executable DDL）

```sql
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(128) NOT NULL,
    isbn VARCHAR(32) NOT NULL,
    seller_id VARCHAR(64) NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents > 0),
    condition_level VARCHAR(16) NOT NULL DEFAULT 'GOOD',
    status VARCHAR(16) NOT NULL DEFAULT 'ON_SALE',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(40) NOT NULL UNIQUE,
    book_id INTEGER NOT NULL,
    buyer_id VARCHAR(64) NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

CREATE INDEX IF NOT EXISTS idx_orders_book_id ON orders(book_id);
CREATE INDEX IF NOT EXISTS idx_orders_buyer_id ON orders(buyer_id);
```

---

## 2. 接口对接契约（API Contract）

### 2.1 统一响应信封与错误码字典（Unified Envelope & Error Codes）

所有接口统一返回以下 JSON 结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

| HTTP 状态码 | 业务错误码 (`code`) | 英文标识 / 含义 | 触发场景说明 |
|---|---|---|---|
| `200` / `201` | `0` | `OK` | 请求成功 |
| `400` | `40001` | `INVALID_ARGUMENT` | 必填字段缺失、价格 `<= 0`、非法枚举值 |
| `400` | `40002` | `SELF_PURCHASE_FORBIDDEN` | 买家 `buyer_id` 与卖家 `seller_id` 相同 |
| `404` | `40401` | `RESOURCE_NOT_FOUND` | 指定的 `book_id` 或 `order_id` 不存在 |
| `409` | `40901` | `BOOK_NOT_AVAILABLE` | 教材当前状态不是 `ON_SALE`（已被锁定或已售出） |
| `409` | `40902` | `INVALID_ORDER_TRANSITION` | 订单已处于 `COMPLETED` 或 `CANCELLED` 终态，禁止重复流转 |
| `500` | `50000` | `INTERNAL_ERROR` | 服务端未预期异常 |

---

### 2.2 接口明细列表（Endpoint Specifications）

#### 接口 1：`<POST /api/v1/books>` — 发布二手教材

- **鉴权方式**：MVP 阶段免 Token，请求体直接传 `seller_id`（后续可升级为 Header `X-User-Id`）
- **请求参数（JSON Body）**：

| 字段名 | 类型 | 必填 | 校验规则与说明 |
|---|---|---|---|
| `title` | `string` | 是 | 1~128 字符 |
| `isbn` | `string` | 是 | 10~32 字符 |
| `seller_id` | `string` | 是 | 非空字符串 |
| `price_cents` | `integer` | 是 | 正整数，单位：分 |
| `condition_level` | `string` | 否 | 默认 `"GOOD"`，可选 `NEW` / `LIKE_NEW` / `GOOD` / `ACCEPTABLE` |

- **请求示例**：
  ```json
  {
    "title": "深入理解计算机系统（原书第3版）",
    "isbn": "9787111544937",
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
      "isbn": "9787111544937",
      "seller_id": "stu_2026001",
      "price_cents": 3500,
      "condition_level": "LIKE_NEW",
      "status": "ON_SALE",
      "created_at": "2026-10-26T19:00:00+08:00"
    }
  }
  ```

---

#### 接口 2：`<GET /api/v1/books>` — 查询教材列表

- **Query 参数**：
  - `status`（可选，`string`，默认返回全部；可传 `ON_SALE`）
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
          "isbn": "9787111544937",
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

#### 接口 3：`<POST /api/v1/orders>` — 买家创建订单（锁定教材）

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
- **失败响应示例（教材已被他人锁定，HTTP `409`）**：
  ```json
  {
    "code": 40901,
    "message": "Book is not available for purchase (current status: RESERVED)",
    "data": null
  }
  ```

---

#### 接口 4：`<POST /api/v1/orders/{order_id}/transition>` — 订单状态流转（完成/取消）

- **请求示例**：
  ```json
  {
    "action": "COMPLETE",
    "operator_id": "stu_2026002"
  }
  ```
  *（注：`action` 枚举为 `"COMPLETE"` 或 `"CANCEL"`）*
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

---

## 3. 外部/上下游对接与 Mock 边界说明（Integration & Mock Boundaries）

| 对接方 / 依赖项 | 对接方向 | 交互方式 / 协议 | 本轮实现状态 (`REAL` / `MOCK`) | 超时、降级与联调说明 |
|---|---|---|---|---|
| 前端客户端 / 小程序 | 上游调用方 | HTTP REST JSON (`/api/v1/*`) | `REAL` | 联调时开启本地 CORS；所有金额以「分」传输，前端展示除以 100 |
| 本地数据库 | 下游存储 | SQLite / MySQL (`DATABASE_URL`) | `REAL` | 真实落库与事务更新，禁止用内存数组替代 |
| 校园统一身份认证 (CAS) | 上游鉴权 | 请求头/字段传递 `seller_id` / `buyer_id` | `MOCK`（显式声明） | MVP 阶段直接信任请求体中的用户 ID，不调学校 CAS 接口 |
| 第三方在线支付 | 下游外部服务 | 状态流转接口 `/orders/{id}/transition` | `MOCK`（显式声明） | MVP 阶段代表「线下当面交割确认」，不调用微信/支付宝网关 |
