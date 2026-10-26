# Dev Skill (`dev-skill`)

> **开发 Skill — 从「一句话需求」到 MVP 边界、Architecture、`AGENTS.md` 总控与数据/接口契约的可验收开发流程**  
> **Contract-First MVP & Scoped Development Skill for AI-Assisted Engineering**

---

## 为什么需要这个 Skill？（团队 AI 协作三件套）

在课程项目、比赛开发与团队协作中，我们已经有了另外两块拼图：
1. 🎨 **画图 Skill（[`WaterProMax/drawing-skill`](https://github.com/WaterProMax/drawing-skill)）**：管架构图与机制图怎么画对、画好看；
2. 📝 **写作 Skill（[`WaterProMax/writing-skill`](https://github.com/WaterProMax/writing-skill)）**：管知识库生成与技术文档怎么基于源码证据不撒谎；
3. 🛠️ **开发 Skill（本仓库 `WaterProMax/dev-skill`）**：**管不会写代码或没有工程经验的队友，怎么用一句话让 AI 把功能做对、合得拢、可验收**。

### 解决的真实痛点
没有经验的同学让 AI 写代码时，往往只会甩出一句话：
> *「我要做后端的订单模块」* / *「帮我做个校园二手交易系统」*

如果没有本 Skill 约束，AI 会立刻一口气吐出十几个代码文件：
- **没 MVP 边界**：擅自引入 JWT + RBAC + Redis + 消息队列，本地根本跑不起来；
- **没总体框架（Architecture）**：目录乱放，Controller 里直接拼 SQL；
- **没数据库与接口契约**：表名字段全靠猜，前端队友拿不到接口文档，联调全部报错；
- **假数据冒充完工**：接口里直接 `return` 硬编码假数组，也不跑真实测试就宣布“开发完成”。

`dev-skill` 用一条铁律彻底堵死这些问题：
> **「契约先行，点头再动代码；契约唯一，分步真实校验。」**

---

## 核心工作流（两阶段硬门禁 + 两大模式）

### 两大路由模式（Operating Modes）

| 模式 | 适用场景 | 核心动作 |
|---|---|---|
| **Mode 1：从零立项** (`Greenfield MVP`) | 空白目录起步，或组员只丢出一句话需求（如「我要做后端的二手书交易模块」） | **禁止直接写业务代码**。先收拢产出根目录 `AGENTS.md` + `docs/contract.md`，等确认后再搭骨架、建表、写接口、跑冒烟测试 |
| **Mode 2：已有仓库开发 / 子模块扩展** (`Brownfield / Scoped Dev`) | 在团队已有代码库中新增子模块或扩展功能 | **先盘点真实仓库**（技术栈、目录、已有数据库表、统一响应封装），划定允许修改的**文件白名单**，补齐/更新 `AGENTS.md` 与 `docs/contract.md`，确认后再动代码；**严禁破坏已有接口和邻接模块** |

---

### Phase 1：契约硬门禁（点头确认前，绝不写业务代码）

收到开发需求后，AI 必须先停在 **Phase 1**，对照 `templates/` 一次性产出两份契约文件请人拍板：

1. **`AGENTS.md`（总控方向盘，放在仓库或子模块根目录）**
   - **① MVP 最小闭环（Scope & Non-Goals）**：本轮只做哪 3–5 个可验收动作 + **明确列出本轮不做（Non-Goals）**，防止 AI 自己加戏。
   - **② Architecture 总体框架与目录树**：优先选简单稳妥、本地一键能跑的技术栈；写清分层职责与精确到文件的目录结构预览。
   - **③ 环境与启动/校验约定**：运行时与数据库版本、环境变量表（对应 `.env.example`）、一键启动命令、**每步开发完必须跑通的验证命令**。
   - **④ Agent 编码红线（Guardrails）**：允许修改的文件白名单、禁止触碰的边界、依赖引入限制与安全底线。
2. **`docs/contract.md`（数据表字段 & 接口对接契约）**
   - **① 数据库与字段设计（Database Schema）**：每张表的完整字段字典（字段名、类型/长度、是否必填、默认值、主键/外键/索引、业务含义）、**状态枚举与状态机流转表**、可直接执行的建表 SQL。
   - **② 接口对接契约（API Contract）**：统一响应信封、错误码字典、每个接口的 `Method + Path`、请求参数与 JSON 示例、成功/失败响应 JSON 示例、前后端联调说明。
   - **③ 外部/上下游对接与 Mock 边界**：写清跨模块或第三方调用方式，若某部分在 MVP 采用 Mock 必须显式标为 `MOCK`。

---

### Phase 2：确认后的三步可验收开发（Stepwise Execution）

只有当人回复「确认 / 可以开始」后，AI 才进入编码阶段，并严格遵守：

- **契约即唯一真相（Single Source of Truth）**：代码里的表名、字段名、状态枚举、URL 路径、JSON 键名必须与 `docs/contract.md` **100% 一致**；中途若需调整字段或接口，**必须先更新 `docs/contract.md` 并说明**。
- **分三步推进并附真实终端验证输出**：
  - **Step 1**：生成 `.env.example` + 目录骨架 + 数据库建表 SQL / ORM Model → 跑通建表与导入校验；
  - **Step 2**：实现核心业务状态机与 API 接口 → 跑通编译与自动化单元测试（`pytest` / `npm test` / `go test`）；
  - **Step 3**：真实启动本地服务 + 执行 `curl` 端到端冒烟请求（覆盖正常闭环与错误码拦截）→ 贴出真实返回结果。

---

## 一键复制话术模板（直接喂给 Cursor / Claude Code / Cloud Agent）

### 场景 A：从零立项（组员只会说一句话需求时）

```text
请严格加载并遵循 `dev-skill`（SKILL.md）的 Mode 1（从零立项 Greenfield MVP）流程。
我的需求是：【在这里填你的一句话需求，例如：我要做后端的校园二手书交易模块】

注意硬门禁要求：
1. 现在处于 Phase 1（契约对齐阶段），在我确认之前，严禁编写任何业务实现代码！
2. 请先参考 `templates/AGENTS.template.md` 和 `templates/contract.template.md`，帮我规划并生成：
   - 根目录 `AGENTS.md`（包含：MVP 3~5 个核心动作与明确不做的 Non-Goals、Architecture 与精确到文件的目录树、环境变量表与分步校验命令、编码红线）
   - `docs/contract.md`（包含：完整数据库表字段字典、状态枚举与流转规则、可执行建表 SQL、每个接口的 Method+Path+请求/响应 JSON 示例+错误码字典）
3. 输出这两份契约后请立即停下，向我列出需要确认的 3 个关键问题，等我回复“确认”后再进入 Phase 2 分步写代码。
```

### 场景 B：已有仓库开发（在团队现有项目里新增/修改一个子模块）

```text
请严格加载并遵循 `dev-skill`（SKILL.md）的 Mode 2（已有仓库扩展 Brownfield / Scoped Dev）流程。
我要在当前仓库中开发：【在这里填一句话需求，例如：在后端新增一个活动报名审核子模块】

注意硬门禁要求：
1. 请先扫描当前仓库的真实目录结构、技术栈/依赖版本、已有数据库表/Entity 以及统一响应/错误码封装，绝对不要另起炉灶引入冲突框架。
2. 现在处于 Phase 1（契约对齐阶段），在我确认之前，严禁修改任何业务代码！
3. 请先产出或更新 `AGENTS.md`（必须明确列出本次允许新建/修改的【文件白名单】，严禁触碰邻接模块）和本模块的接口/库表契约文件 `docs/contract.md`。
4. 输出这两份契约后立即停下等我确认；我确认后，再严格按 Step 1（库表/Model）→ Step 2（业务/接口）→ Step 3（真实启动与冒烟校验）推进。
```

### 场景 C：Phase 1 契约确认后，放行 AI 开始写代码

```text
Phase 1 的 `AGENTS.md` 和 `docs/contract.md` 我已确认通过（如有微调请先同步更新契约文件）。
现在请进入 `dev-skill` 的 Phase 2，严格按 `docs/contract.md` 的表字段和接口定义（100% 对齐，禁止私自改名或用假数据桩代码敷衍），依次执行：
- Step 1：环境配置 `.env.example` + 目录骨架 + 数据库建表与 Model，并运行 Step 1 校验命令；
- Step 2：核心业务逻辑与 API 接口实现，并运行 Step 2 测试命令；
- Step 3：真实启动服务并执行 `curl` 端到端冒烟测试（含正常闭环与异常错误码验证），把每一步的真实终端输出贴给我验收。
```

---

## 目录结构（Repository Layout）

```text
dev-skill/
├── SKILL.md                             # Skill 核心入口：Mode 1/2 路由、Phase 1 契约门禁、Phase 2 编码纪律、5 大反模式与自检清单
├── README.md                            # 面向队友/新手的仓库说明与一键复制调用话术
├── CHANGELOG.md                         # 版本演进记录
├── templates/                           # 标准双契约文件模板（可直接复制到业务仓库）
│   ├── AGENTS.template.md               # AGENTS.md 总控模板（MVP 闭环、架构目录树、环境与校验命令、编码红线）
│   └── contract.template.md             # docs/contract.md 契约模板（库表字段字典、状态机、建表 SQL、REST 接口与错误码）
├── examples/                            # 端到端实战示范
│   └── one-sentence-to-mvp.md           # 从一句话「我要做后端的二手书交易模块」到 Phase 1 确认再到 Phase 2 冒烟验收全流程
└── tests/                               # 静态结构完整性校验与行为回归测试集
    ├── README.md
    ├── regression-cases.yaml
    └── validate_structure.py
```

---

## 快速校验（Validation）

在仓库根目录下运行静态结构与回归集校验脚本：

```bash
python3 tests/validate_structure.py
```
