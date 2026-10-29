# Phase 3 清单示例（验证通过之后）

本文件演示 `templates/task-plan.template.md` §6 与 `templates/pull-request.template.md` 怎么填。二手书订单只是例子；优惠券、工单等模块换成自己的 `TASK_ID` 与资源名，四类不变量与 Git 红线不变。

## 工作示例：校园二手书订单（`TASK-2026-001-book-order-mvp`）

- **分支名**：`feature/book-order-mvp`（从 `develop` 切出，对应 `docs/tasks/book-order-mvp.md`）
- **PR 链接**：`https://github.com/<org>/<repo>/pull/42`
- **评审人**：仓库所有者 `@owner`，另加 `@reviewer-a`、`@reviewer-b`（已各给 LGTM）
- **CI**：全绿（单元测试、集成测试、Linter、`COVERAGE_GATE: 95`）
- **合入**：squash merge 到 `develop`，等待下一次发版，不向 `main` commit / force-push
- **Conventional Commits**：`feat(book-order): enforce single-active resource lock`
- **契约**：`CONTRACT_PATH = docs/contract.md`。`INV-1`～`INV-4` 在本模块实例化为待交易订单唯一、锁书与建单同事务、取消只释放本单、归属人鉴权（模拟身份不等于跳过 `40301`）。

## 同一清单用于非交易模块（优惠券，无教材措辞）

- **分支名**：`feature/coupon-claim`
- **PR 链接**：`https://github.com/<org>/<repo>/pull/43`
- **评审人**：单人仓库，写 `solo`；所有者自检 1 次 + CI 全绿
- **集成分支**：仓库没有 `develop`，任务单声明 `INTEGRATION_BRANCH: main`，因此从 `main` **切出** `feature/coupon-claim`，PR 指向 `main`，提交不在 `main` 上
- **不变量**：`INV-1` 同一用户一张未使用券；`INV-2` 扣库存与写领取记录同事务；`INV-3` 退回只释放本次领取且终态不可重复核销；`INV-4` `X-User-Id` 只是身份载体，核销仍校验归属人
