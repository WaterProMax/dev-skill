"""Regressions for scope-language, inline-backtick comments, Scale S inline contracts, and runtime evaluator checks."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from evaluate_workspace import (
    evaluate_scene_a_phase1_gate,
    evaluate_scene_b_brownfield_whitelist,
    evaluate_scene_c_phase2_delivery,
    run_git,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def runtime_workspace(ws: Path) -> None:
    (ws / "docs").mkdir()
    (ws / "app").mkdir()
    (ws / "tests").mkdir()
    (ws / "AGENTS.md").write_text("CONTRACT_PATH: `docs/contract.md`\n", encoding="utf-8")
    (ws / "docs/contract.md").write_text(
        "INV-1: initialized tables must exist.\nCREATE TABLE books (id INTEGER PRIMARY KEY);\n"
        "CREATE TABLE orders (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    (ws / "app/service.py").write_text(
        "import sqlite3\n"
        "def init():\n"
        "    conn = sqlite3.connect(':memory:')\n"
        "    conn.execute('PRAGMA foreign_keys = ON;')\n"
        "    conn.executescript('CREATE TABLE books (id INT); CREATE TABLE orders (id INT);')\n"
        "    return conn\n",
        encoding="utf-8",
    )
    (ws / "tests/test_app.py").write_text(
        "import unittest\nfrom app.service import init\n"
        "class T(unittest.TestCase):\n"
        "    def test_unrelated(self):\n        self.assertEqual(1 + 1, 2)\n"
        "    def test_init(self):\n"
        "        conn = init()\n"
        "        try:\n"
        "            tables = {r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}\n"
        "            self.assertEqual(tables, {'books', 'orders'})\n"
        "            self.assertEqual(conn.execute('PRAGMA foreign_keys').fetchone()[0], 1)\n"
        "        finally:\n            conn.close()\n",
        encoding="utf-8",
    )
    write_plan(ws)
    (ws / "DELIVERY_REPORT.md").write_text("STATUS: COMPLETED\n", encoding="utf-8")


def write_plan(ws: Path, selector: str = "test_app.T.test_init") -> None:
    check = {"test": selector, "targets": ["app/service.py:init"]}
    (ws / "tests/verification.json").write_text(
        json.dumps({"initialization": check, "contract_tests": {"INV-1": check}}),
        encoding="utf-8",
    )


class ScopeTests(unittest.TestCase):
    def evaluate(self, agents: str, task: str = ""):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory)
            (ws / "AGENTS.md").write_text(agents, encoding="utf-8")
            (ws / "docs/tasks").mkdir(parents=True)
            (ws / "docs/contract.md").write_text("CREATE TABLE books (id INT);\n", encoding="utf-8")
            if task:
                (ws / "docs/tasks/task.md").write_text(task, encoding="utf-8")
            return evaluate_scene_a_phase1_gate(ws)

    def test_english_and_chinese_sections_in_either_document(self):
        for heading in ["Non-Goals", "不做项", "非目标", "本轮明确不做", "长期边界"]:
            for location in ["agents", "task"]:
                with self.subTest(heading=heading, location=location):
                    section = f"## {heading}\n本轮不实现支付、登录与物流。\n"
                    result = self.evaluate(
                        section if location == "agents" else "# Rules\n",
                        section if location == "task" else "",
                    )
                    self.assertTrue(result.passed, result.violations)

    def test_empty_heading_or_keyword_in_unrelated_prose_is_insufficient(self):
        for content in [
            "## Non-Goals\n## Scope\n- Add orders\n",
            "# Rules\nRead Non-Goals later.\n",
            "## 长期边界\n<!-- fill this section -->\n",
        ]:
            with self.subTest(content=content):
                result = self.evaluate(content)
                self.assertFalse(result.passed)
                self.assertTrue(any("scope exclusions" in v for v in result.violations))

    def test_comment_wrapped_sections_do_not_declare_scope(self):
        for closing in ["-->\n", ""]:
            with self.subTest(closing=closing):
                result = self.evaluate("# Rules\n<!--\n## Non-Goals\n- No payment.\n" + closing)
                self.assertFalse(result.passed, result.checks)

    def test_fenced_examples_do_not_declare_scope(self):
        for marker in ["```", "````", "~~~"]:
            with self.subTest(marker=marker):
                example = f"# Rules\n{marker}markdown\n## Non-Goals\n- No payment.\n{marker}\n"
                self.assertFalse(self.evaluate(example).passed)

    def test_scope_requires_body_beyond_nested_headings(self):
        result = self.evaluate("## Non-Goals\n### Pending details\n<!-- pending -->\n## Scope\n- Add orders\n")
        self.assertFalse(result.passed)

    def test_hidden_examples_do_not_hide_real_scope(self):
        examples = "<!--\n## Non-Goals\n- Example only.\n-->\n```markdown\n## Scope\n<!-- literal comment\n```\n"
        result = self.evaluate(examples, "   ## 本轮明确不做\n### 排除项\n- 本轮不实现支付。\n")
        self.assertTrue(result.passed, result.violations)

    def test_inline_backtick_comment_token_does_not_swallow_following_scope(self):
        doc = (
            "# Rules\n"
            "Do not leave unclosed `<!--` or ``<!--`` tokens in templates.\n\n"
            "## Non-Goals\n"
            "- No payment gateway integration in this round.\n"
        )
        result = self.evaluate(doc)
        self.assertTrue(result.passed, result.violations)

    def test_indented_code_block_does_not_declare_scope(self):
        doc = "# Rules\n\n    ## Non-Goals\n    - Fake item inside 4-space indented code block\n"
        result = self.evaluate(doc)
        self.assertFalse(result.passed)

    def test_setext_heading_declares_scope(self):
        doc = "Rules\n=====\n\nNon-Goals\n---------\n- No Redis or Kafka in MVP.\n"
        result = self.evaluate(doc)
        self.assertTrue(result.passed, result.violations)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.ws = Path(self.directory.name)
        runtime_workspace(self.ws)

    def evaluate(self):
        # Keep the reported independent suite green, to isolate the runtime gate.
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-k", "unrelated"]
        return evaluate_scene_c_phase2_delivery(self.ws, test_cmd=command)

    def test_real_initialization_and_contract_assertions_pass(self):
        result = self.evaluate()
        self.assertTrue(result.passed, result.violations)

    def test_original_two_statement_execute_crash_is_rejected(self):
        service = self.ws / "app/service.py"
        service.write_text(service.read_text(encoding="utf-8").replace("conn.executescript(", "conn.execute("), encoding="utf-8")
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("ProgrammingError" in v for v in result.violations), result.violations)

    def test_unrelated_passing_test_does_not_satisfy_runtime_target(self):
        write_plan(self.ws, "test_app.T.test_unrelated")
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("missing calls" in v for v in result.violations), result.violations)

    def test_missing_plan_is_unverified(self):
        (self.ws / "tests/verification.json").unlink()
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("UNVERIFIED" in v for v in result.violations))

    def test_missing_contract_item_is_unverified(self):
        plan = self.ws / "tests/verification.json"
        payload = json.loads(plan.read_text(encoding="utf-8"))
        payload["contract_tests"] = {}
        plan.write_text(json.dumps(payload), encoding="utf-8")
        self.assertFalse(self.evaluate().passed)

    def test_skipped_acceptance_cannot_pass(self):
        test = self.ws / "tests/test_app.py"
        test.write_text(
            test.read_text(encoding="utf-8").replace("    def test_init", "    @unittest.skip('not run')\n    def test_init"),
            encoding="utf-8",
        )
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("skipped=1" in v for v in result.violations), result.violations)

    def test_schema_drift_is_rejected_by_actual_assertions(self):
        service = self.ws / "app/service.py"
        service.write_text(
            service.read_text(encoding="utf-8").replace("CREATE TABLE orders (id INT)", "CREATE TABLE invoices (id INT)"),
            encoding="utf-8",
        )
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("AssertionError" in v for v in result.violations), result.violations)

    def test_test_code_cannot_be_declared_as_production_target(self):
        plan = self.ws / "tests/verification.json"
        payload = json.loads(plan.read_text(encoding="utf-8"))
        payload["initialization"]["targets"] = ["tests/test_app.py:T.test_unrelated"]
        plan.write_text(json.dumps(payload), encoding="utf-8")
        self.assertFalse(self.evaluate().passed)

    def threaded_test(self, warm_on_import=False):
        setup = "pool = ThreadPoolExecutor(max_workers=1)\npool.submit(lambda: None).result()\n" if warm_on_import else ""
        pool_expression = "pool" if warm_on_import else "ThreadPoolExecutor(max_workers=1)"
        (self.ws / "tests/test_app.py").write_text(
            "import unittest\nfrom concurrent.futures import ThreadPoolExecutor\nfrom app.service import init\n"
            "def initialize_in_worker():\n"
            "    conn = init()\n"
            "    try:\n"
            "        tables = {r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}\n"
            "        return tables, conn.execute('PRAGMA foreign_keys').fetchone()[0]\n"
            "    finally:\n        conn.close()\n"
            + setup
            + "class T(unittest.TestCase):\n"
            "    def test_unrelated(self):\n        self.assertEqual(1 + 1, 2)\n"
            "    def test_init(self):\n"
            f"        with {pool_expression} as executor:\n"
            "            tables, fk = executor.submit(initialize_in_worker).result(timeout=5)\n"
            "        self.assertEqual(tables, {'books', 'orders'})\n"
            "        self.assertEqual(fk, 1)\n",
            encoding="utf-8",
        )

    def test_real_initialization_in_worker_thread_passes(self):
        self.threaded_test()
        result = self.evaluate()
        self.assertTrue(result.passed, result.violations)

    def test_pool_created_during_import_is_observed_during_test(self):
        self.threaded_test(warm_on_import=True)
        result = self.evaluate()
        self.assertTrue(result.passed, result.violations)

    def test_threaded_schema_assertion_failure_is_rejected(self):
        self.threaded_test()
        service = self.ws / "app/service.py"
        service.write_text(
            service.read_text(encoding="utf-8").replace("CREATE TABLE orders (id INT)", "CREATE TABLE invoices (id INT)"),
            encoding="utf-8",
        )
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("AssertionError" in v for v in result.violations), result.violations)

    def test_import_time_calls_do_not_satisfy_runtime_target(self):
        (self.ws / "tests/test_app.py").write_text(
            "import unittest\nfrom app.service import init\nconn = init()\nconn.close()\n"
            "class T(unittest.TestCase):\n"
            "    def test_unrelated(self):\n        self.assertEqual(1 + 1, 2)\n",
            encoding="utf-8",
        )
        write_plan(self.ws, "test_app.T.test_unrelated")
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("missing calls" in v for v in result.violations), result.violations)

    def test_commented_or_fenced_inv_id_in_contract_is_ignored(self):
        contract = self.ws / "docs/contract.md"
        contract.write_text(
            "<!-- Example only: INV-99 and AC-98 should not require tests -->\n"
            "```markdown\nINV-97 inside fenced block\n```\n"
            "INV-1: initialized tables must exist.\n"
            "CREATE TABLE books (id INTEGER PRIMARY KEY);\n"
            "CREATE TABLE orders (id INTEGER PRIMARY KEY);\n",
            encoding="utf-8",
        )
        result = self.evaluate()
        self.assertTrue(result.passed, result.violations)

    def test_commented_out_pragma_or_table_in_python_is_rejected(self):
        (self.ws / "app/service.py").write_text(
            "import sqlite3\n"
            "def init():\n"
            "    conn = sqlite3.connect(':memory:')\n"
            "    # PRAGMA foreign_keys = ON\n"
            "    # CREATE TABLE books (id INT); CREATE TABLE orders (id INT);\n"
            "    return conn\n",
            encoding="utf-8",
        )
        (self.ws / "tests/test_app.py").write_text(
            "import unittest\nfrom app.service import init\n"
            "class T(unittest.TestCase):\n"
            "    def test_unrelated(self):\n        self.assertEqual(1 + 1, 2)\n"
            "    def test_init(self):\n"
            "        conn = init()\n"
            "        conn.close()\n",
            encoding="utf-8",
        )
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("PRAGMA foreign_keys = ON" in v for v in result.violations), result.violations)
        self.assertTrue(any("Table 'books'" in v for v in result.violations), result.violations)

    def test_swallowed_exception_in_target_does_not_satisfy_runtime_check(self):
        (self.ws / "app/service.py").write_text(
            "import sqlite3\n"
            "def init():\n"
            "    if True:\n"
            "        raise RuntimeError('broken service initialization')\n"
            "    conn = sqlite3.connect(':memory:')\n"
            "    conn.execute('PRAGMA foreign_keys = ON;')\n"
            "    conn.executescript('CREATE TABLE books (id INT); CREATE TABLE orders (id INT);')\n"
            "    return conn\n",
            encoding="utf-8",
        )
        (self.ws / "tests/test_app.py").write_text(
            "import unittest\nfrom app.service import init\n"
            "class T(unittest.TestCase):\n"
            "    def test_unrelated(self):\n        self.assertEqual(1 + 1, 2)\n"
            "    def test_init(self):\n"
            "        try:\n"
            "            init()\n"
            "        except RuntimeError:\n"
            "            pass\n",
            encoding="utf-8",
        )
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("missing calls" in v for v in result.violations), result.violations)

    def test_scale_s_inline_contract_in_task_plan_passes_scene_a_and_scene_c(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "docs/tasks").mkdir(parents=True)
            (ws / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
            (ws / "docs/tasks/isbn-fix.md").write_text(
                "# Task Plan\n"
                "- **任务规模（`SCALE`）**：`Scale S`\n"
                "- **关联契约路径（`CONTRACT_PATH`）**：`NONE (Scale S 内联契约)`\n"
                "## 2.2 本轮明确不做（Non-Goals）\n"
                "- 不新增数据库表或 HTTP 接口\n"
                "## 3.1 允许新建或修改的文件（File Whitelist）\n"
                "- `docs/tasks/isbn-fix.md`\n"
                "- `app/isbn.py`\n"
                "- `tests/test_isbn.py`\n"
                "- `tests/verification.json`\n"
                "## 4. Scale S 轻量内联契约\n"
                "- `AC-1`: `parse_isbn(raw: str) -> str` strips hyphens and validates length.\n",
                encoding="utf-8",
            )
            res_a = evaluate_scene_a_phase1_gate(ws)
            self.assertTrue(res_a.passed, res_a.violations)

            (ws / "app").mkdir()
            (ws / "tests").mkdir()
            (ws / "app/isbn.py").write_text(
                "def parse_isbn(raw: str) -> str:\n    return raw.replace('-', '')\n",
                encoding="utf-8",
            )
            (ws / "tests/test_isbn.py").write_text(
                "import unittest\nfrom app.isbn import parse_isbn\n"
                "class T(unittest.TestCase):\n"
                "    def test_parse(self):\n        self.assertEqual(parse_isbn('978-7-111'), '9787111')\n",
                encoding="utf-8",
            )
            check = {"test": "test_isbn.T.test_parse", "targets": ["app/isbn.py:parse_isbn"]}
            (ws / "tests/verification.json").write_text(
                json.dumps({"initialization": check, "contract_tests": {"AC-1": check}}),
                encoding="utf-8",
            )
            res_c = evaluate_scene_c_phase2_delivery(ws)
            self.assertTrue(res_c.passed, res_c.violations)

    def test_minimal_repro_verification_plan_passes_runtime_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "docs").mkdir()
            (ws / "tests").mkdir()
            repro_dir = REPO_ROOT / "examples" / "minimal-repro"
            for name in ("book_order_service.py", "test_minimal_repro.py", "schema.sql"):
                shutil.copy2(repro_dir / name, ws / name)
            shutil.copy2(repro_dir / "verification.json", ws / "tests" / "verification.json")
            (ws / "AGENTS.md").write_text("CONTRACT_PATH: `docs/contract.md`\n", encoding="utf-8")
            (ws / "docs/contract.md").write_text(
                (REPO_ROOT / "templates" / "contract.template.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            res = evaluate_scene_c_phase2_delivery(
                ws,
                test_cmd=[sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_minimal_repro.py", "-v"],
            )
            self.assertTrue(res.passed, res.violations)


if __name__ == "__main__":
    unittest.main()
