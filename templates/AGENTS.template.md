# AGENTS.md — 项目/模块 AI 开发总控契约

> **文档性质**：本文件由 `dev-skill` 在 **Phase 1（契约门禁阶段）** 生成。  
> **核心铁律**：在项目负责人确认本文件与 `docs/contract.md` 之前，**严禁编写任何业务实现代码**。进入 Phase 2 后，所有 AI Agent（Cursor / Claude Code / Cloud Agent）必须严格按本文件定义的范围、目录、环境变量与校验命令执行。

## 元信息（Metadata）

- **项目/模块名称**：`<填写项目或模块名，例如：校园二手书交易后端 / 订单子模块>`
- **开发模式**：`<Mode 1：从零立项 (Greenfield MVP) | Mode 2：已有仓库扩展 (Brownfield / Scoped Dev)>`
- **关联数据与接口契约**：`docs/contract.md`（唯一字段与接口真源）
- **当前阶段状态**：`[ ] Phase 1 待确认` / `[ ] Phase 2 开发中` / `[ ] Phase 2 已验收`

---

## 1. MVP 最小闭环（Scope & Non-Goals）

<!-- 填写说明：把模糊的一句话需求压缩为 3~5 个最核心、可验收的闭环动作，并明确列出本轮不做的事项，防止 AI 自行加戏。 -->

### 1.1 本轮必做核心动作（In-Scope MVP Actions）
1. **动作 1（例如：发布闲置教材）**：卖家提交书名、ISBN、原价、售价（分）、成色，落库生成状态为 `ON_SALE` 的二手书记录。
2. **动作 2（例如：教材列表与关键词检索）**：买家按书名/ISBN/状态分页查询在售教材列表及详情。
3. **动作 3（例如：创建交易订单与防重锁定）**：买家对 `ON_SALE` 教材下单，原子更新教材状态为 `RESERVED` 并生成 `PENDING` 订单（禁止同一本书被重复下单）。
4. **动作 4（例如：确认交割/取消订单）**：支持将订单标记为 `COMPLETED`（教材变为 `SOLD`）或 `CANCELLED`（教材回滚为 `ON_SALE`）。

### 1.2 本轮明确不做（Non-Goals — 严禁 AI 擅自引入）
- ❌ **不做复杂权限与认证中心**：本轮不引入 OAuth2 / RBAC 多角色权限系统（仅通过请求头或参数传递 `user_id` 完成 MVP 闭环）。
- ❌ **不接真实第三方支付网关**：不对接微信/支付宝真实商户号，支付流转通过模拟状态流转接口完成。
- ❌ **不引入重型中间件**：不引入 Redis 集群、RabbitMQ/Kafka 消息队列、Elasticsearch 或微服务拆分。
- ❌ **不做前端页面 / 后台管理大屏**：本仓库/模块仅交付后端 API 与数据库 Schema，以接口冒烟测试为验收标准。

---

## 2. Architecture 总体框架与目录树（Architecture & Directory Tree）

### 2.1 技术栈选型与理由（Tech Stack）

| 层级 | 选型（含版本） | 选型理由（优先简单、本地可一键启动） |
|---|---|---|
| 语言与运行时 | `<例如：Python 3.11 / Node.js 20 / Go 1.22 / Java 17>` | `<团队环境已具备，零额外编译门槛>` |
| Web 框架 | `<例如：FastAPI 0.115 / Express / Gin / Spring Boot 3.2>` | `<轻量、路由清晰、自带参数校验>` |
| 数据库与 ORM | `<例如：SQLite 3 + SQLAlchemy 2.0（本地零配置，可平滑切 MySQL 8.0）>` | `<新手无需安装独立数据库服务即可跑通全链路闭环>` |
| 测试与校验工具 | `<例如：pytest + httpx / curl>` | `<支持命令行自动化冒烟回归>` |

### 2.2 分层职责（Layered Responsibilities）

```text
HTTP Client / Frontend
   │
   ▼
[Router / Controller 层]  ── 仅负责路由绑定、请求参数格式校验、统一响应结构封装（禁止写 SQL 与核心业务分支）
   │
   ▼
[Service 业务逻辑层]      ── 负责状态机流转校验、跨表事务一致性、业务异常抛出（对应 docs/contract.md 错误码）
   │
   ▼
[Repository / Model 层]   ── 负责数据库表映射（ORM Entity）与原子 CRUD 操作（字段名与 docs/contract.md 100% 一致）
   │
   ▼
[Database 存储层]         ── 物理表结构由 schema.sql / 迁移脚本初始化
```

### 2.3 目录结构预览（Directory Tree Preview）

<!-- 填写说明：精确到文件级别；Mode 2 下需标明哪些是已有文件、哪些是本次新增文件。 -->

```text
<project-or-module-root>/
├── AGENTS.md                   # 本文件：AI 开发总控方向盘
├── .env.example                # 环境变量示例模板（不含真实密钥）
├── requirements.txt            # 依赖清单（或 package.json / go.mod / pom.xml）
├── docs/
│   └── contract.md             # 数据表字段与接口对接契约（唯一真源）
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口、路由挂载、全局异常处理与健康检查
│   ├── config.py               # 环境变量读取与默认配置
│   ├── database.py             # 数据库连接与 Session 管理
│   ├── models.py               # 数据库表 ORM 定义（严格对齐 docs/contract.md）
│   ├── schemas.py              # 请求/响应 DTO 校验模型（严格对齐 docs/contract.md）
│   ├── services.py             # 核心业务逻辑与状态机校验
│   └── routers.py              # API 路由处理函数
├── sql/
│   └── schema.sql              # 可直接执行的建表 DDL 与种子测试数据
└── tests/
    └── test_smoke.py           # 核心闭环自动化冒烟测试
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

### 3.2 一键安装与启动命令（Quickstart Commands）

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库表结构（如使用 SQLite/MySQL 初始化脚本）
sqlite3 data.db < sql/schema.sql

# 4. 启动本地服务
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3.3 分步开发强制校验命令（Mandatory Step Verification）

> **Agent 铁律**：Phase 2 每完成一个 Step，必须真实运行对应命令并贴出终端输出；未跑通前禁止进入下一步，更禁止口头宣称“已完成”。

- **Step 1 校验（环境骨架 + 数据库建表/Model 对齐检查）**：
  ```bash
  sqlite3 /tmp/test_init.db < sql/schema.sql && python3 -c "import app.models, app.schemas; print('Step 1 Schema & Models OK')"
  ```
- **Step 2 校验（核心业务与接口自动化测试）**：
  ```bash
  pytest -v tests/test_smoke.py
  ```
- **Step 3 校验（真实进程启动 + `curl` 端到端冒烟验证）**：
  ```bash
  # 健康检查
  curl -s http://127.0.0.1:8000/api/v1/health
  # 正常闭环请求示例（如创建记录 -> 查询 -> 状态流转）
  curl -s -X POST http://127.0.0.1:8000/api/v1/items -H "Content-Type: application/json" -d '{"title":"示例"}'
  ```

---

## 4. Agent 编码红线（Guardrails）

### 4.1 允许修改范围（File Whitelist）
- ✅ 允许新建/修改：`AGENTS.md`、`docs/contract.md`、`.env.example`、`sql/schema.sql`、`app/**`、`tests/**`。

### 4.2 禁止触碰边界（Forbidden Zones）
- 🚫 **Mode 2 已有仓库特别红线**：严禁修改白名单之外的邻接模块代码、公共鉴权中间件、全局数据库迁移历史或已有接口的返回结构。
- 🚫 **禁止私自扩栈**：未经负责人确认，严禁往依赖清单里添加未在 §2.1 声明的重型框架、外部云 SDK 或付费 API。

### 4.3 契约同步与反幻觉约定（Single Source of Truth & Anti-Hallucination）
1. **字段与路径零偏差**：代码中的表名、列名、状态枚举值、URL 路径、JSON 请求/响应字段名，必须与 `docs/contract.md` **100% 一致**（注意大小写与 `snake_case` / `camelCase` 规范）。
2. **变更先改契约**：开发过程中若发现必须增删字段或调整接口路径，**必须先更新 `docs/contract.md` 与本文件并说明原因**，再修改代码。
3. **拒绝假数据桩代码**：严禁在接口中直接 `return [{"id": 1, "mock": true}]` 冒充已落库功能；若某外部依赖在 MVP 阶段采用 Mock，必须在 `docs/contract.md` §3 与交付报告中显式标注 `[MOCK]`。
4. **安全底线**：严禁将真实密码、私钥、Token 或生产公网 IP 写入代码库或 Git 提交历史。
