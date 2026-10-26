# 完整实战示范：从一句话「我要做后端的二手书交易模块」到可验收 MVP

本示例展示当团队里没有经验的同学只对 AI 说出一句话需求时，`dev-skill` 如何拦截「直接瞎写代码」的冲动，通过 **Phase 1（`AGENTS.md` + `docs/contract.md` 双契约门禁）** 与 **Phase 2（三步真实校验开发）** 交付可联调、可验收的代码。

---

## 0. 对比：没有 `dev-skill` vs 启用 `dev-skill`

| 维度 | ❌ 没有 `dev-skill`（常见翻车现场） | ✅ 启用 `dev-skill`（本案例流程） |
|---|---|---|
| **收到一句话后的第一反应** | 立刻开始写 `main.py`、`user.py`、`jwt_auth.py`、`wx_pay.py` 等十几个文件 | **触发 Phase 1 硬门禁**：禁止写业务代码，先生成 `AGENTS.md` + `docs/contract.md` 请人确认 |
| **功能边界** | AI 擅自加上 JWT 登录、RBAC 角色表、Redis 缓存、微信支付回调桩代码 | 压成 4 个核心 MVP 闭环动作，明确把复杂鉴权/真实支付列为 `Non-Goals` |
| **数据库与接口对齐** | 表字段靠猜（有的地方叫 `price`，有的地方叫 `bookPrice`），前端完全无法对接 | 在 `docs/contract.md` 钉死字段类型、状态机（`ON_SALE -> RESERVED -> SOLD`）和 JSON 示例 |
| **最终交付物状态** | 看似代码很多，实则缺依赖、连不上库、部分接口写死假数据 | 每步跑通真实校验命令，附带 `pytest` 与 `curl` 真实请求/响应及 `40901` 错误码验证 |

---

## 1. Round 1：新手输入一句话 → AI 触发 Phase 1 契约门禁

### 👤 用户（组员）输入
> 「我要做后端的二手书交易模块」

---

### 🤖 AI 响应（Phase 1：拦截直接写代码，产出双契约供确认）

收到！按照 `dev-skill` 规范，收到一句话模块需求时，**我们在确认契约前绝不直接写业务代码**，先帮你把 MVP 范围、架构目录、数据库表字段和前后端接口契约钉死。

我已为你生成以下两份契约文件初稿（仓库根目录 `AGENTS.md` 与 `docs/contract.md`）：

#### 📄 文件 1：`AGENTS.md`（总控方向盘摘要）
1. **MVP 最小闭环（4 个核心动作）**：
   - `发布教材`：卖家提交书名、ISBN、售价（分）、成色，入库状态为 `ON_SALE`。
   - `检索教材`：支持按状态（`ON_SALE`）和关键词查询在售教材列表。
   - `下单锁书`：买家对 `ON_SALE` 教材下单，生成 `PENDING` 订单并将教材原子更新为 `RESERVED`（防止一书多卖，且禁止卖家买自己的书）。
   - `订单流转`：确认交割（订单 `COMPLETED` + 教材 `SOLD`）或取消订单（订单 `CANCELLED` + 教材回滚为 `ON_SALE`）。
   - **本轮明确不做（Non-Goals）**：不做独立登录注册/JWT 权限中心（直接传 `seller_id`/`buyer_id`）、不接真实微信/支付宝网关、不引 Redis/消息队列。
2. **Architecture 与目录树**：
   - 技术栈：**Python 3.11 + FastAPI + SQLite3（SQLAlchemy 2.0）+ pytest**（零外部服务依赖，队友拉下来 10 秒即可跑通）。
   - 目录结构：`app/main.py`、`app/models.py`、`app/schemas.py`、`app/services.py`、`app/routers.py`、`sql/schema.sql`、`tests/test_smoke.py`。
3. **环境与分步校验命令**：
   - 环境变量：`APP_ENV=development`、`DATABASE_URL=sqlite:///./secondhand_books.db`（对应 `.env.example`）。
   - 强制校验：Step 1 建表与 Model 导入检查 → Step 2 `pytest -v tests/test_smoke.py` → Step 3 真实启动 `uvicorn` + `curl` 冒烟验证。
4. **Agent 编码红线**：
   - 仅允许修改本模块白名单文件；所有表名、字段名、状态枚举、接口 JSON 键名必须与 `docs/contract.md` 100% 一致。

#### 📄 文件 2：`docs/contract.md`（数据库字段与接口契约摘要）
1. **核心数据表（2 张表）**：
   - `books` 表：`id` (PK), `title` (VARCHAR(128)), `isbn` (VARCHAR(32)), `seller_id` (VARCHAR(64)), `price_cents` (INTEGER, 正整数分), `condition_level` (`NEW`/`LIKE_NEW`/`GOOD`/`ACCEPTABLE`), `status` (`ON_SALE`/`RESERVED`/`SOLD`), `created_at`, `updated_at`。
   - `orders` 表：`id` (PK), `order_no` (UNIQUE), `book_id` (FK -> `books.id`), `buyer_id` (VARCHAR(64)), `amount_cents` (INTEGER), `status` (`PENDING`/`COMPLETED`/`CANCELLED`), `created_at`, `updated_at`。
2. **核心接口（统一返回 `{"code": 0, "message": "ok", "data": ...}`）**：
   - `POST /api/v1/books`：发布教材
   - `GET /api/v1/books`：分页/关键词查询教材列表
   - `POST /api/v1/orders`：创建订单并锁定教材（若教材非 `ON_SALE` 返回 HTTP `409` / `code: 40901`；若自买返回 HTTP `400` / `code: 40002`）
   - `POST /api/v1/orders/{order_id}/transition`：传入 `{"action": "COMPLETE" | "CANCEL", "operator_id": "..."}` 完成或取消订单

---

> 🛑 **Phase 1 契约门禁确认点（当前尚未编写任何业务代码）**  
> 请确认以下 3 件事，确认或提出修改意见后我立即进入 Phase 2 分步编码：
> 1. 这 4 个核心动作的 MVP 边界够用吗？
> 2. `books` 和 `orders` 表的字段有没有需要增删的（比如是否需要加「适用课程名」或「校区」）？
> 3. 这 4 个接口路径和字段名，前端队友可以直接对接吗？

---

## 2. Round 2：用户确认并微调字段 → AI 先改契约再分步落地

### 👤 用户（组员）回复
> 「确认没问题！不过 `books` 表里帮我加一个可选字段 `course_name`（适用课程名，比如“高等数学”），其他按这个直接开始写代码吧。」

---

### 🤖 AI 响应（Phase 2：契约同步 → Step 1 → Step 2 → Step 3 真实校验交付）

收到确认！按 **契约变更同步协议**，我已先在 `docs/contract.md` 中同步补充 `course_name` 字段，随后严格按三步完成开发与真实验证：

#### Step 0：先同步更新 `docs/contract.md`（契约即唯一真相）
- 在 `docs/contract.md` §1.2 `books` 表字段字典与 §1.4 `schema.sql` 中新增：
  - `course_name`：`VARCHAR(64)`，可空（`NULL`），默认 `NULL`，含义为「适用课程名称（如“高等数学”、“数据结构”）」。
- 在 `POST /api/v1/books` 请求体与响应示例中同步加入 `"course_name": "计算机系统基础"`。

#### Step 1：环境骨架与数据层落地 + 校验
已创建 `.env.example`、`requirements.txt`、`sql/schema.sql`、`app/database.py`、`app/models.py`、`app/schemas.py`。
运行 Step 1 校验命令：
```bash
$ sqlite3 /tmp/test_books.db < sql/schema.sql && python3 -c "import app.models, app.schemas; print('Step 1 Schema & Models OK')"
Step 1 Schema & Models OK
```

#### Step 2：核心业务（状态机 + 防重锁书）与接口实现 + 自动化测试
已实现 `app/services.py`、`app/routers.py`、`app/main.py` 与 `tests/test_smoke.py`。
运行 Step 2 校验命令：
```bash
$ pytest -v tests/test_smoke.py
============================= test session starts ==============================
collected 5 items

tests/test_smoke.py::test_publish_and_list_books PASSED                  [ 20%]
tests/test_smoke.py::test_self_purchase_rejected_40002 PASSED            [ 40%]
tests/test_smoke.py::test_create_order_locks_book PASSED                 [ 60%]
tests/test_smoke.py::test_duplicate_order_rejected_40901 PASSED          [ 80%]
tests/test_smoke.py::test_complete_and_cancel_transitions PASSED         [100%]

============================== 5 passed in 0.34s ===============================
```

#### Step 3：真实启动服务与 `curl` 冒烟验收
启动本地服务后，执行完整闭环冒烟请求：

1. **发布含 `course_name` 的教材（`POST /api/v1/books`）**：
   ```json
   {"code":0,"message":"ok","data":{"id":1,"title":"深入理解计算机系统","isbn":"9787111544937","course_name":"计算机系统基础","seller_id":"stu_001","price_cents":3500,"condition_level":"LIKE_NEW","status":"ON_SALE"}}
   ```
2. **买家 `stu_002` 下单锁书（`POST /api/v1/orders`）**：
   ```json
   {"code":0,"message":"ok","data":{"id":1,"order_no":"ORD2026102619150001","book_id":1,"buyer_id":"stu_002","amount_cents":3500,"status":"PENDING","book_status":"RESERVED"}}
   ```
3. **第三人尝试抢购同一本书（验证防重锁书 `40901`）**：
   ```json
   {"code":40901,"message":"Book is not available for purchase (current status: RESERVED)","data":null}
   ```
4. **确认线下交割完成（`POST /api/v1/orders/1/transition`）**：
   ```json
   {"code":0,"message":"ok","data":{"id":1,"order_no":"ORD2026102619150001","status":"COMPLETED","book_id":1,"book_status":"SOLD"}}
   ```

所有表字段、状态枚举、路由路径、错误码与 `docs/contract.md` 100% 对齐，前端队友可直接照着 `docs/contract.md` 联调。
