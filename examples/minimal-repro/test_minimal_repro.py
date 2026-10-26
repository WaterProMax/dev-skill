"""Executable invariant & contract verification suite for examples/minimal-repro.

Run from repository root:
    python3 -m unittest discover -s examples/minimal-repro -v
"""

from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from book_order_service import (  # noqa: E402
    BookOrderService,
    ContractError,
    create_connection,
    init_db,
)


class MinimalReproInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = create_connection(":memory:")
        init_db(self.conn)
        self.svc = BookOrderService(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    def test_01_sqlite_foreign_key_enforced(self) -> None:
        """Verify PRAGMA foreign_keys = ON blocks inserting orders for non-existent books."""
        with self.assertRaises(sqlite3.IntegrityError):
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO orders (order_no, book_id, buyer_id, amount_cents, status)
                    VALUES ('ORD_FK_FAIL', 99999, 'stu_buyer', 3500, 'PENDING')
                    """
                )

    def test_02_inv1_atomic_lock_and_duplicate_order_rejected_40901(self) -> None:
        """INV-1: At most one active PENDING order per book; duplicate lock returns 40901."""
        pub = self.svc.publish_book(
            title="深入理解计算机系统（原书第3版）",
            isbn="978-7-111-54493-7",
            course_name="计算机系统基础",
            seller_id="stu_seller_01",
            price_cents=3500,
            condition_level="LIKE_NEW",
        )
        book_id = pub["data"]["id"]

        # First buyer locks book and creates PENDING order
        ord1 = self.svc.create_order(book_id=book_id, buyer_id="stu_buyer_01")
        self.assertEqual(ord1["data"]["status"], "PENDING")
        self.assertEqual(ord1["data"]["book_status"], "RESERVED")

        # Second buyer attempting to buy the same locked book gets 40901
        with self.assertRaises(ContractError) as ctx:
            self.svc.create_order(book_id=book_id, buyer_id="stu_buyer_02")
        self.assertEqual(ctx.exception.code, 40901)

        # Partial unique index uk_orders_active_book also prevents raw duplicate PENDING insert
        with self.assertRaises(sqlite3.IntegrityError):
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO orders (order_no, book_id, buyer_id, amount_cents, status)
                    VALUES ('ORD_DUP_PENDING', ?, 'stu_buyer_03', 3500, 'PENDING')
                    """,
                    (book_id,),
                )

    def test_03_inv2_transaction_rollback_on_order_failure(self) -> None:
        """INV-2: If order creation fails after locking book, transaction rolls back book to ON_SALE."""
        pub = self.svc.publish_book(
            title="算法导论",
            isbn="9787111407010",
            seller_id="stu_seller_01",
            price_cents=4200,
        )
        book_id = pub["data"]["id"]

        def boom() -> None:
            raise RuntimeError("Simulated DB crash after book lock before order insert")

        with self.assertRaises(RuntimeError):
            self.svc.create_order(
                book_id=book_id,
                buyer_id="stu_buyer_01",
                before_order_insert_hook=boom,
            )

        # Book must still be ON_SALE and zero orders must exist
        book_row = self.conn.execute("SELECT status FROM books WHERE id = ?", (book_id,)).fetchone()
        order_count = self.conn.execute(
            "SELECT count(*) FROM orders WHERE book_id = ?", (book_id,)
        ).fetchone()[0]
        self.assertEqual(book_row["status"], "ON_SALE")
        self.assertEqual(order_count, 0)

    def test_04_inv3_cancel_releases_only_target_book_and_blocks_terminal_retry_40903(self) -> None:
        """INV-3: Cancelling releases only the target book; repeating transition on terminal order returns 40903."""
        b1 = self.svc.publish_book(
            title="编译原理", isbn="9787111251217", seller_id="stu_seller_01", price_cents=2800
        )["data"]["id"]
        b2 = self.svc.publish_book(
            title="操作系统概念", isbn="9787111609216", seller_id="stu_seller_01", price_cents=3000
        )["data"]["id"]

        o1 = self.svc.create_order(book_id=b1, buyer_id="stu_buyer_01")["data"]["id"]
        o2 = self.svc.create_order(book_id=b2, buyer_id="stu_buyer_02")["data"]["id"]

        # Cancel o1 -> b1 becomes ON_SALE, while b2 remains RESERVED
        res_cancel = self.svc.transition_order(order_id=o1, action="CANCEL", operator_id="stu_buyer_01")
        self.assertEqual(res_cancel["data"]["status"], "CANCELLED")
        self.assertEqual(res_cancel["data"]["book_status"], "ON_SALE")

        b1_status = self.conn.execute("SELECT status FROM books WHERE id = ?", (b1,)).fetchone()["status"]
        b2_status = self.conn.execute("SELECT status FROM books WHERE id = ?", (b2,)).fetchone()["status"]
        self.assertEqual(b1_status, "ON_SALE")
        self.assertEqual(b2_status, "RESERVED")

        # Repeating CANCEL or COMPLETE on already CANCELLED order o1 returns 40903
        with self.assertRaises(ContractError) as ctx:
            self.svc.transition_order(order_id=o1, action="CANCEL", operator_id="stu_buyer_01")
        self.assertEqual(ctx.exception.code, 40903)

        # Complete o2 -> b2 becomes SOLD, and repeating returns 40903
        res_comp = self.svc.transition_order(order_id=o2, action="COMPLETE", operator_id="stu_seller_01")
        self.assertEqual(res_comp["data"]["status"], "COMPLETED")
        self.assertEqual(res_comp["data"]["book_status"], "SOLD")

        with self.assertRaises(ContractError) as ctx2:
            self.svc.transition_order(order_id=o2, action="COMPLETE", operator_id="stu_seller_01")
        self.assertEqual(ctx2.exception.code, 40903)

    def test_05_inv4_authorization_40301_and_self_purchase_40002_and_offshelf_40902(self) -> None:
        """INV-4: Enforce owner permissions (40301), self-purchase block (40002), and OFF_SHELF transitions (40902)."""
        book_id = self.svc.publish_book(
            title="计算机网络", isbn="9787121302954", seller_id="stu_seller_01", price_cents=2500
        )["data"]["id"]

        # Self-purchase blocked with 40002
        with self.assertRaises(ContractError) as self_buy:
            self.svc.create_order(book_id=book_id, buyer_id="stu_seller_01")
        self.assertEqual(self_buy.exception.code, 40002)

        # Non-owner cannot off-shelf book -> 40301
        with self.assertRaises(ContractError) as non_owner_shelf:
            self.svc.change_shelf_status(book_id=book_id, action="OFF_SHELF", operator_id="stu_stranger")
        self.assertEqual(non_owner_shelf.exception.code, 40301)

        # Owner can off-shelf ON_SALE -> OFF_SHELF, and buyer cannot order OFF_SHELF book (40901)
        off = self.svc.change_shelf_status(book_id=book_id, action="OFF_SHELF", operator_id="stu_seller_01")
        self.assertEqual(off["data"]["status"], "OFF_SHELF")
        with self.assertRaises(ContractError) as buy_off:
            self.svc.create_order(book_id=book_id, buyer_id="stu_buyer_01")
        self.assertEqual(buy_off.exception.code, 40901)

        # Owner re-lists OFF_SHELF -> ON_SALE
        on = self.svc.change_shelf_status(book_id=book_id, action="ON_SALE", operator_id="stu_seller_01")
        self.assertEqual(on["data"]["status"], "ON_SALE")

        # Buyer locks book; seller cannot directly off-shelf a RESERVED book -> 40902
        order_id = self.svc.create_order(book_id=book_id, buyer_id="stu_buyer_01")["data"]["id"]
        with self.assertRaises(ContractError) as locked_shelf:
            self.svc.change_shelf_status(book_id=book_id, action="OFF_SHELF", operator_id="stu_seller_01")
        self.assertEqual(locked_shelf.exception.code, 40902)

        # Stranger (neither buyer nor seller) cannot cancel or complete the order -> 40301
        with self.assertRaises(ContractError) as stranger_cancel:
            self.svc.transition_order(order_id=order_id, action="CANCEL", operator_id="stu_stranger")
        self.assertEqual(stranger_cancel.exception.code, 40301)


if __name__ == "__main__":
    unittest.main(verbosity=2)
