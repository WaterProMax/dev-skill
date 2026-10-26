"""Regressions for scope-language and unrelated-green-suite evaluator failures."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from evaluate_workspace import evaluate_scene_a_phase1_gate, evaluate_scene_c_phase2_delivery


def runtime_workspace(ws: Path) -> None:
    (ws / "docs").mkdir()
    (ws / "app").mkdir()
    (ws / "tests").mkdir()
    (ws / "AGENTS.md").write_text("CONTRACT_PATH: `docs/contract.md`\n")
    (ws / "docs/contract.md").write_text(
        "INV-1: initialized tables must exist.\nCREATE TABLE books (id INTEGER PRIMARY KEY);\n"
        "CREATE TABLE orders (id INTEGER PRIMARY KEY);\n"
    )
    (ws / "app/service.py").write_text(
        "import sqlite3\n"
        "def init():\n"
        "    conn = sqlite3.connect(':memory:')\n"
        "    conn.execute('PRAGMA foreign_keys = ON;')\n"
        "    conn.executescript('CREATE TABLE books (id INT); CREATE TABLE orders (id INT);')\n"
        "    return conn\n"
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
        "        finally:\n            conn.close()\n"
    )
    write_plan(ws)
    (ws / "DELIVERY_REPORT.md").write_text("STATUS: COMPLETED\n")


def write_plan(ws: Path, selector: str = "test_app.T.test_init") -> None:
    check = {"test": selector, "targets": ["app/service.py:init"]}
    (ws / "tests/verification.json").write_text(json.dumps({
        "initialization": check, "contract_tests": {"INV-1": check},
    }))


class ScopeTests(unittest.TestCase):
    def evaluate(self, agents: str, task: str = ""):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory)
            (ws / "AGENTS.md").write_text(agents)
            (ws / "docs/tasks").mkdir(parents=True)
            (ws / "docs/contract.md").write_text("CREATE TABLE books (id INT);\n")
            if task:
                (ws / "docs/tasks/task.md").write_text(task)
            return evaluate_scene_a_phase1_gate(ws)

    def test_english_and_chinese_sections_in_either_document(self):
        for heading in ["Non-Goals", "不做项", "非目标", "本轮明确不做", "长期边界"]:
            for location in ["agents", "task"]:
                with self.subTest(heading=heading, location=location):
                    section = f"## {heading}\n本轮不实现支付、登录与物流。\n"
                    result = self.evaluate(section if location == "agents" else "# Rules\n",
                                           section if location == "task" else "")
                    self.assertTrue(result.passed, result.violations)

    def test_empty_heading_or_keyword_in_unrelated_prose_is_insufficient(self):
        for content in ["## Non-Goals\n## Scope\n- Add orders\n", "# Rules\nRead Non-Goals later.\n",
                        "## 长期边界\n<!-- fill this section -->\n"]:
            with self.subTest(content=content):
                result = self.evaluate(content)
                self.assertFalse(result.passed)
                self.assertTrue(any("scope exclusions" in v for v in result.violations))


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
        service.write_text(service.read_text().replace("conn.executescript(", "conn.execute("))
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
        payload = json.loads(plan.read_text())
        payload["contract_tests"] = {}
        plan.write_text(json.dumps(payload))
        self.assertFalse(self.evaluate().passed)

    def test_skipped_acceptance_cannot_pass(self):
        test = self.ws / "tests/test_app.py"
        test.write_text(test.read_text().replace("    def test_init", "    @unittest.skip('not run')\n    def test_init"))
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("skipped=1" in v for v in result.violations), result.violations)

    def test_schema_drift_is_rejected_by_actual_assertions(self):
        service = self.ws / "app/service.py"
        service.write_text(service.read_text().replace("CREATE TABLE orders (id INT)", "CREATE TABLE invoices (id INT)"))
        result = self.evaluate()
        self.assertFalse(result.passed)
        self.assertTrue(any("AssertionError" in v for v in result.violations), result.violations)

    def test_test_code_cannot_be_declared_as_production_target(self):
        plan = self.ws / "tests/verification.json"
        payload = json.loads(plan.read_text())
        payload["initialization"]["targets"] = ["tests/test_app.py:T.test_unrelated"]
        plan.write_text(json.dumps(payload))
        self.assertFalse(self.evaluate().passed)


if __name__ == "__main__":
    unittest.main()
