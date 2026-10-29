# 最小可复现示例（`examples/minimal-repro`）

本目录提供与 [`examples/one-sentence-to-mvp.md`](../one-sentence-to-mvp.md) 及 [`templates/contract.template.md`](../../templates/contract.template.md) 100% 对齐的 **零第三方依赖可运行示例**（基于 Python 标准库 `sqlite3` + `unittest`），并附带供 `tests/evaluate_workspace.py --scene phase2_delivery` 使用的运行时验收映射文件 [`verification.json`](./verification.json)。

## 一键运行复现命令

在仓库根目录下直接运行：

```bash
python3 -m unittest discover -s examples/minimal-repro -v
```

## 验证覆盖的契约与业务不变量（`INV-1` ~ `INV-4`）

1. **`test_01_sqlite_foreign_key_enforced`（对应 `verification.json` 的 `initialization`）**：验证每个 SQLite 连接显式开启 `PRAGMA foreign_keys = ON;`，向 `orders` 插入不存在的 `book_id` 时由数据库外键约束直接拦截（`sqlite3.IntegrityError`）。
2. **`test_02_inv1_atomic_lock_and_duplicate_order_rejected_40901`（对应 `INV-1`）**：验证 **INV-1 唯一性 / 单一有效待处理资源** 的二手书实例（唯一有效待交易订单）——通过条件更新 `WHERE id = ? AND status = 'ON_SALE'`（检查 `rowcount == 1`）与部分唯一索引 `uk_orders_active_book`，拦截重复下单并返回 `40901 BOOK_NOT_AVAILABLE`。
3. **`test_03_inv2_transaction_rollback_on_order_failure`（对应 `INV-2`）**：验证 **INV-2 同事务原子性** 的二手书实例（锁书与建单同事务）——模拟锁书成功后、订单插入前发生异常，验证事务整体回滚，`books.status` 恢复为 `ON_SALE` 且无残留脏订单。
4. **`test_04_inv3_cancel_releases_only_target_book_and_blocks_terminal_retry_40903`（对应 `INV-3`）**：验证 **INV-3 精准释放与终态幂等** 的二手书实例——取消订单仅释放该单绑定的 `RESERVED` 教材回 `ON_SALE`（不影响其他已锁定教材），且对已 `CANCELLED` / `COMPLETED` 终态订单重复操作返回 `40903 INVALID_ORDER_TRANSITION`。
5. **`test_05_inv4_authorization_40301_and_self_purchase_40002_and_offshelf_40902`（对应 `INV-4`）**：验证 **INV-4 归属人鉴权 vs 模拟身份** 的二手书实例及 `OFF_SHELF` 状态机——自买返回 `40002`、非卖家上下架或非本单买/卖家操作订单返回 `40301 FORBIDDEN_NOT_OWNER`、卖家在教材被锁定期间直接下架返回 `40902 BOOK_STATUS_CONFLICT`。
