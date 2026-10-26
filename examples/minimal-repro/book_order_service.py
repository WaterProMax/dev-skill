"""Minimal reproducible reference implementation for dev-skill v1.1.0.

Enforces:
- SQLite per-connection foreign key pragma (PRAGMA foreign_keys = ON)
- INV-1: Single active PENDING order per book (DB partial unique index + rowcount == 1)
- INV-2: Atomic book lock + order creation in the same transaction with full rollback on error
- INV-3: Targeted lock release on order cancellation & terminal state protection (40903)
- INV-4: Explicit separation of Mock Identity carrier vs real Owner Authorization (40301)
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

VALID_CONDITIONS = {"NEW", "LIKE_NEW", "GOOD", "ACCEPTABLE"}


@dataclass
class ContractError(Exception):
    http_status: int
    code: int
    message: str

    def to_envelope(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "data": None}


def create_connection(db_path: str = ":memory:") -> sqlite3.Connection:
    """Create a SQLite connection with PRAGMA foreign_keys = ON enforced."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    fk_enabled = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    if fk_enabled != 1:
        raise RuntimeError("SQLite PRAGMA foreign_keys failed to enable")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON;")


class BookOrderService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def publish_book(
        self,
        *,
        title: str,
        isbn: str,
        seller_id: str,
        price_cents: int,
        condition_level: str = "GOOD",
        course_name: str | None = None,
    ) -> dict[str, Any]:
        # Request Validation Layer
        clean_title = (title or "").strip()
        clean_isbn = (isbn or "").strip()
        clean_seller = (seller_id or "").strip()
        if not (1 <= len(clean_title) <= 128):
            raise ContractError(400, 40001, "Invalid title length (must be 1..128 chars)")
        if not (10 <= len(clean_isbn) <= 20):
            raise ContractError(400, 40001, "Invalid isbn length (must be 10..20 chars)")
        if not clean_seller or len(clean_seller) > 64:
            raise ContractError(400, 40001, "Invalid seller_id")
        if not isinstance(price_cents, int) or price_cents <= 0:
            raise ContractError(400, 40001, "price_cents must be a positive integer")
        if condition_level not in VALID_CONDITIONS:
            raise ContractError(400, 40001, f"Invalid condition_level: {condition_level}")

        with self.conn:
            cur = self.conn.execute(
                """
                INSERT INTO books (title, isbn, course_name, seller_id, price_cents, condition_level, status)
                VALUES (?, ?, ?, ?, ?, ?, 'ON_SALE')
                """,
                (clean_title, clean_isbn, course_name, clean_seller, price_cents, condition_level),
            )
            book_id = cur.lastrowid
            row = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return {"code": 0, "message": "ok", "data": dict(row)}

    def change_shelf_status(
        self,
        *,
        book_id: int,
        action: str,
        operator_id: str,
    ) -> dict[str, Any]:
        if action not in ("OFF_SHELF", "ON_SALE"):
            raise ContractError(400, 40001, f"Unsupported shelf action: {action}")

        with self.conn:
            book = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            if not book:
                raise ContractError(404, 40401, f"Book {book_id} not found")
            # INV-4: Only seller_id owns shelf transitions
            if book["seller_id"] != operator_id:
                raise ContractError(
                    403,
                    40301,
                    f"Forbidden: operator {operator_id} is not seller of book {book_id}",
                )

            expected_from = "ON_SALE" if action == "OFF_SHELF" else "OFF_SHELF"
            if book["status"] != expected_from:
                raise ContractError(
                    409,
                    40902,
                    f"Cannot transition book from {book['status']} to {action}",
                )

            cur = self.conn.execute(
                """
                UPDATE books
                SET status = ?, updated_at = datetime('now')
                WHERE id = ? AND status = ?
                """,
                (action, book_id, expected_from),
            )
            if cur.rowcount != 1:
                raise ContractError(409, 40902, "Concurrent book status conflict")

            updated = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return {"code": 0, "message": "ok", "data": dict(updated)}

    def create_order(
        self,
        *,
        book_id: int,
        buyer_id: str,
        before_order_insert_hook: Callable[[], None] | None = None,
    ) -> dict[str, Any]:
        clean_buyer = (buyer_id or "").strip()
        if not clean_buyer:
            raise ContractError(400, 40001, "buyer_id is required")

        # INV-1 & INV-2: Lock book and create order atomically in the SAME transaction
        with self.conn:
            book = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            if not book:
                raise ContractError(404, 40401, f"Book {book_id} not found")
            if book["seller_id"] == clean_buyer:
                raise ContractError(400, 40002, "Seller cannot purchase their own book")

            # Conditional atomic update: only succeeds if status is currently ON_SALE
            lock_cur = self.conn.execute(
                """
                UPDATE books
                SET status = 'RESERVED', updated_at = datetime('now')
                WHERE id = ? AND status = 'ON_SALE'
                """,
                (book_id,),
            )
            if lock_cur.rowcount != 1:
                raise ContractError(
                    409,
                    40901,
                    f"Book is not available for purchase (current status: {book['status']})",
                )

            if before_order_insert_hook is not None:
                before_order_insert_hook()

            order_no = f"ORD{uuid.uuid4().hex[:16].upper()}"
            order_cur = self.conn.execute(
                """
                INSERT INTO orders (order_no, book_id, buyer_id, amount_cents, status)
                VALUES (?, ?, ?, ?, 'PENDING')
                """,
                (order_no, book_id, clean_buyer, book["price_cents"]),
            )
            order_id = order_cur.lastrowid
            order_row = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            data = dict(order_row)
            data["book_status"] = "RESERVED"
        return {"code": 0, "message": "ok", "data": data}

    def transition_order(
        self,
        *,
        order_id: int,
        action: str,
        operator_id: str,
    ) -> dict[str, Any]:
        if action not in ("COMPLETE", "CANCEL"):
            raise ContractError(400, 40001, f"Invalid action: {action}")

        with self.conn:
            order = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not order:
                raise ContractError(404, 40401, f"Order {order_id} not found")
            book = self.conn.execute("SELECT * FROM books WHERE id = ?", (order["book_id"],)).fetchone()
            if not book:
                raise ContractError(404, 40401, f"Associated book {order['book_id']} not found")

            # INV-4: Only the order's buyer_id or the book's seller_id may complete/cancel
            if operator_id not in (order["buyer_id"], book["seller_id"]):
                raise ContractError(
                    403,
                    40301,
                    f"Forbidden: operator {operator_id} is neither buyer nor seller of order {order_id}",
                )

            # INV-3: Terminal state orders cannot transition again
            if order["status"] != "PENDING":
                raise ContractError(
                    409,
                    40903,
                    f"Order {order_id} is already in terminal state {order['status']}",
                )

            target_order_status = "COMPLETED" if action == "COMPLETE" else "CANCELLED"
            target_book_status = "SOLD" if action == "COMPLETE" else "ON_SALE"

            ord_cur = self.conn.execute(
                """
                UPDATE orders
                SET status = ?, updated_at = datetime('now')
                WHERE id = ? AND status = 'PENDING'
                """,
                (target_order_status, order_id),
            )
            if ord_cur.rowcount != 1:
                raise ContractError(409, 40903, "Concurrent order transition conflict")

            # INV-3: Targeted release/completion ONLY on the book associated with this order in RESERVED state
            book_cur = self.conn.execute(
                """
                UPDATE books
                SET status = ?, updated_at = datetime('now')
                WHERE id = ? AND status = 'RESERVED'
                """,
                (target_book_status, order["book_id"]),
            )
            if book_cur.rowcount != 1:
                raise ContractError(
                    409,
                    40902,
                    f"Associated book {order['book_id']} is not in RESERVED state",
                )

            updated_order = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            data = dict(updated_order)
            data["book_status"] = target_book_status
        return {"code": 0, "message": "ok", "data": data}
