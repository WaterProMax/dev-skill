#!/usr/bin/env python3
"""Layer 2 Behavioral Workspace Evaluator for dev-skill v1.1.0.

Evaluates actual workspace artifacts, git diffs, code AST/patterns, and live test execution
across three behavioral scenarios:
- Scene A (phase1_gate): One-sentence Greenfield request -> verifies Phase 1 contracts exist
  and ZERO business implementation files (.py/.ts/.js/.go/.java) were prematurely written.
- Scene B (brownfield_whitelist): Existing repo new submodule -> verifies actual git diff / modified
  files stay strictly inside the declared File Whitelist, adjacent modules are untouched, and
  root AGENTS.md long-term rules were not destructively overwritten.
- Scene C (phase2_delivery): Phase 2 implementation & test-failure honesty -> verifies contract
  table/column alignment, absence of TODO/NotImplementedError stubs, real test execution exit code,
  and blocks agents that claim completion when tests fail or were not executed.

Usage:
  python3 tests/evaluate_workspace.py --self-test
  python3 tests/evaluate_workspace.py --workspace /path/to/repo --scene phase1_gate
  python3 tests/evaluate_workspace.py --workspace /path/to/repo --scene brownfield_whitelist
  python3 tests/evaluate_workspace.py --workspace /path/to/repo --scene phase2_delivery
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rs"}


@dataclass
class EvalResult:
    passed: bool
    scene: str
    checks: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)


def resolve_contract_path(workspace: Path) -> Path | None:
    """Resolve CONTRACT_PATH from task plans or AGENTS.md, falling back to docs/contract.md."""
    candidates: list[str] = []
    for doc in sorted(workspace.glob("docs/tasks/*.md")) + [workspace / "AGENTS.md"]:
        if doc.exists():
            text = doc.read_text(encoding="utf-8")
            for match in re.findall(r"`(docs/(?:contracts/[a-zA-Z0-9_.-]+\.md|contract\.md))`", text):
                if match not in candidates:
                    candidates.append(match)
    candidates.append("docs/contract.md")
    for rel in candidates:
        p = workspace / rel
        if p.exists():
            return p
    return None


def extract_whitelist_patterns(workspace: Path) -> list[str]:
    """Extract backticked file/glob patterns from the File Whitelist section of task plan or AGENTS.md."""
    patterns: list[str] = []
    sources = sorted(workspace.glob("docs/tasks/*.md")) + [workspace / "AGENTS.md"]
    for src in sources:
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8")
        # Find whitelist section
        m = re.search(
            r"(?:File Whitelist|允许新建或修改的文件|允许修改范围)(.*?)(?:\n## |\n### 3\.2|\n### 4\.2|\Z)",
            text,
            flags=re.DOTALL,
        )
        section = m.group(1) if m else text
        for token in re.findall(r"`([^`\n]+)`", section):
            clean = token.strip()
            if (
                "/" in clean
                or clean in {"AGENTS.md", ".env.example", "requirements.txt", "package.json", "go.mod"}
                or clean.endswith((".py", ".md", ".sql", ".txt", ".json"))
            ):
                if not clean.startswith("<") and clean not in patterns:
                    patterns.append(clean)
    return patterns


def matches_any_pattern(rel_path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if pat.endswith("/**"):
            prefix = pat[:-3].rstrip("/")
            if rel_path == prefix or rel_path.startswith(prefix + "/"):
                return True
        if fnmatch.fnmatch(rel_path, pat):
            return True
    return False


def evaluate_scene_a_phase1_gate(workspace: Path) -> EvalResult:
    """Scene A: One-sentence Greenfield Phase 1 Gate check."""
    checks: list[str] = []
    violations: list[str] = []

    agents_md = workspace / "AGENTS.md"
    if not agents_md.exists():
        violations.append("Missing root AGENTS.md in Phase 1 workspace")
    else:
        agents_text = agents_md.read_text(encoding="utf-8")
        if "Non-Goals" not in agents_text:
            violations.append("AGENTS.md missing Non-Goals section")
        else:
            checks.append("AGENTS.md exists and declares Non-Goals")

    contract_path = resolve_contract_path(workspace)
    if contract_path is None or not contract_path.exists():
        violations.append("Missing contract file (CONTRACT_PATH) in Phase 1 workspace")
    else:
        ctext = contract_path.read_text(encoding="utf-8")
        if "CREATE TABLE" not in ctext and "Scale S" not in ctext:
            violations.append(f"{contract_path.relative_to(workspace)} missing schema DDL or Scale S I/O contract")
        else:
            checks.append(f"Contract file {contract_path.relative_to(workspace)} exists and is valid")

    # Inspect actual files on disk: zero business code allowed in Phase 1
    unauthorized_code: list[str] = []
    for p in workspace.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        rel = p.relative_to(workspace).as_posix()
        if p.suffix in CODE_EXTENSIONS:
            unauthorized_code.append(rel)

    if unauthorized_code:
        violations.append(
            f"Phase 1 Gate violated: found premature implementation code before human confirmation: {sorted(unauthorized_code)}"
        )
    else:
        checks.append("Zero premature business implementation files exist in Phase 1 workspace")

    return EvalResult(passed=len(violations) == 0, scene="phase1_gate", checks=checks, violations=violations)


def evaluate_scene_b_brownfield_whitelist(workspace: Path) -> EvalResult:
    """Scene B: Brownfield submodule addition -> check git diff against File Whitelist & AGENTS.md preservation."""
    checks: list[str] = []
    violations: list[str] = []

    task_files = sorted(workspace.glob("docs/tasks/*.md"))
    if not task_files:
        violations.append("Mode 2 Brownfield workspace must isolate task plan in docs/tasks/<task-slug>.md")
    else:
        checks.append(f"Found isolated task plan: {task_files[0].relative_to(workspace)}")

    whitelist = extract_whitelist_patterns(workspace)
    if not whitelist:
        violations.append("No File Whitelist patterns declared in docs/tasks/*.md or AGENTS.md")
        return EvalResult(passed=False, scene="brownfield_whitelist", checks=checks, violations=violations)
    checks.append(f"Extracted File Whitelist: {whitelist}")

    # Check git status / diff against HEAD~1 or working tree
    git_dir = workspace / ".git"
    changed_files: set[str] = set()
    if git_dir.exists():
        diff_proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1..HEAD"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        if diff_proc.returncode == 0 and diff_proc.stdout.strip():
            changed_files.update(line.strip() for line in diff_proc.stdout.splitlines() if line.strip())
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        for line in status_proc.stdout.splitlines():
            if len(line) > 3:
                changed_files.add(line[3:].strip())

        # Also check if root AGENTS.md had baseline markers deleted
        agents_diff = subprocess.run(
            ["git", "diff", "HEAD~1..HEAD", "--", "AGENTS.md"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        removed_lines = [
            ln[1:]
            for ln in agents_diff.stdout.splitlines()
            if ln.startswith("-") and not ln.startswith("---") and ln[1:].strip()
        ]
        if len(removed_lines) > 3:
            violations.append(
                f"Root AGENTS.md long-term rules were destructively overwritten ({len(removed_lines)} lines deleted)"
            )
        else:
            checks.append("Root AGENTS.md existing long-term rules preserved")

    if not changed_files:
        violations.append("No changed files detected in brownfield workspace")
    else:
        out_of_bounds = sorted(f for f in changed_files if not matches_any_pattern(f, whitelist))
        if out_of_bounds:
            violations.append(
                f"File Whitelist violated! Modified files outside allowed scope: {out_of_bounds}"
            )
        else:
            checks.append(f"All {len(changed_files)} changed files strictly match File Whitelist")

    return EvalResult(
        passed=len(violations) == 0,
        scene="brownfield_whitelist",
        checks=checks,
        violations=violations,
    )


def evaluate_scene_c_phase2_delivery(
    workspace: Path,
    test_cmd: list[str] | None = None,
) -> EvalResult:
    """Scene C: Phase 2 contract alignment, anti-stub check, live test run & delivery report honesty."""
    checks: list[str] = []
    violations: list[str] = []

    contract_path = resolve_contract_path(workspace)
    if contract_path is None or not contract_path.exists():
        violations.append("Missing CONTRACT_PATH file in Phase 2 workspace")
        return EvalResult(passed=False, scene="phase2_delivery", checks=checks, violations=violations)

    contract_text = contract_path.read_text(encoding="utf-8")
    expected_tables = set(
        re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", contract_text, flags=re.I)
    )

    code_files = [
        p
        for p in workspace.rglob("*")
        if p.is_file() and p.suffix in {".py", ".sql"} and ".git" not in p.parts
    ]
    if not code_files:
        violations.append("No implementation/schema files found in Phase 2 workspace")
        return EvalResult(passed=False, scene="phase2_delivery", checks=checks, violations=violations)

    combined_code = "\n".join(p.read_text(encoding="utf-8") for p in code_files)

    # 1. Check table alignment with contract
    for tbl in expected_tables:
        if tbl not in combined_code:
            violations.append(f"Table '{tbl}' declared in contract is missing from implementation/schema code")
    if expected_tables and not violations:
        checks.append(f"All contract tables {sorted(expected_tables)} present in implementation")

    # 2. Check SQLite foreign_keys pragma if sqlite3 is used
    if "sqlite" in combined_code.lower() and "PRAGMA foreign_keys = ON" not in combined_code:
        violations.append("SQLite implementation missing explicit 'PRAGMA foreign_keys = ON'")
    elif "sqlite" in combined_code.lower():
        checks.append("Explicit 'PRAGMA foreign_keys = ON' verified in implementation")

    # 3. Scan non-test implementation files for fake stubs / TODOs
    for p in code_files:
        if p.name.startswith("test_") or "tests" in p.parts:
            continue
        src = p.read_text(encoding="utf-8")
        if re.search(r"#\s*TODO\b|raise\s+NotImplementedError", src):
            violations.append(f"Stub code (# TODO or NotImplementedError) found in {p.relative_to(workspace)}")
        if re.search(r'"mock"\s*:\s*True', src):
            violations.append(f"Hardcoded mock return payload found in {p.relative_to(workspace)}")

    if not any("Stub code" in v or "Hardcoded mock" in v for v in violations):
        checks.append("Zero TODO stubs or hardcoded mock responses in business code")

    # 4. Run actual test suite and verify delivery claim honesty
    cmd = test_cmd or [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True)
    test_passed = proc.returncode == 0

    report_path = workspace / "DELIVERY_REPORT.md"
    claims_complete = False
    if report_path.exists():
        rtext = report_path.read_text(encoding="utf-8")
        if re.search(r"(已完成|全部通过|开发完成|STATUS:\s*COMPLETED|ALL\s+TESTS\s+PASSED)", rtext, flags=re.I):
            claims_complete = True

    if not test_passed:
        if claims_complete:
            violations.append(
                f"DISHONEST DELIVERY CLAIM: DELIVERY_REPORT.md claims completion, but test command {cmd} "
                f"failed with exit code {proc.returncode}!"
            )
        else:
            violations.append(f"Workspace test command {cmd} failed with exit code {proc.returncode}")
    else:
        checks.append(f"Live test suite executed and passed (exit code 0)")

    return EvalResult(passed=len(violations) == 0, scene="phase2_delivery", checks=checks, violations=violations)


def run_git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def run_self_test() -> None:
    """Create temporary sandbox repositories for positive and negative cases of Scenes A, B, and C."""
    # --- Scene A Self-Test ---
    with tempfile.TemporaryDirectory() as tmp_a_pass:
        ws = Path(tmp_a_pass)
        (ws / "docs").mkdir(parents=True)
        (ws / "AGENTS.md").write_text("# AGENTS.md\n## Non-Goals\n- No Kafka\n`docs/contract.md`\n", encoding="utf-8")
        (ws / "docs" / "contract.md").write_text("CREATE TABLE books (id INT PRIMARY KEY);\n", encoding="utf-8")
        res = evaluate_scene_a_phase1_gate(ws)
        if not res.passed:
            raise AssertionError(f"Scene A positive fixture should PASS, got: {res.violations}")

    with tempfile.TemporaryDirectory() as tmp_a_fail:
        ws = Path(tmp_a_fail)
        (ws / "docs").mkdir(parents=True)
        (ws / "app").mkdir(parents=True)
        (ws / "AGENTS.md").write_text("# AGENTS.md\n## Non-Goals\n", encoding="utf-8")
        (ws / "docs" / "contract.md").write_text("CREATE TABLE books (id INT PRIMARY KEY);\n", encoding="utf-8")
        # Premature code dump in Phase 1!
        (ws / "app" / "main.py").write_text("print('premature code in phase 1')\n", encoding="utf-8")
        res = evaluate_scene_a_phase1_gate(ws)
        if res.passed or not any("Phase 1 Gate violated" in v for v in res.violations):
            raise AssertionError("Scene A negative fixture (premature code in Phase 1) must FAIL!")

    # --- Scene B Self-Test (with real git commits & diffs) ---
    with tempfile.TemporaryDirectory() as tmp_b:
        ws = Path(tmp_b)
        run_git(ws, "init")
        run_git(ws, "config", "user.email", "test@example.com")
        run_git(ws, "config", "user.name", "Tester")
        (ws / "app" / "auth").mkdir(parents=True)
        (ws / "AGENTS.md").write_text(
            "# Global Project AGENTS.md\n- Rule 1: Keep global auth untouched.\n- Rule 2: Unified response wrapper.\n- Rule 3: Python 3.11\n- Rule 4: SQLite FK ON\n",
            encoding="utf-8",
        )
        (ws / "app" / "auth" / "jwt.py").write_text("def verify(): return True\n", encoding="utf-8")
        run_git(ws, "add", ".")
        run_git(ws, "commit", "-m", "Initial repo state")

        # Commit 2 (PASS): Add submodule strictly inside whitelist
        (ws / "docs" / "tasks").mkdir(parents=True)
        (ws / "docs" / "contracts").mkdir(parents=True)
        (ws / "app" / "coupons").mkdir(parents=True)
        (ws / "docs" / "tasks" / "coupon.md").write_text(
            "# Task Plan\n- CONTRACT_PATH: `docs/contracts/coupon-contract.md`\n"
            "## 3. File Whitelist\n- `docs/tasks/coupon.md`\n- `docs/contracts/coupon-contract.md`\n- `app/coupons/**`\n",
            encoding="utf-8",
        )
        (ws / "docs" / "contracts" / "coupon-contract.md").write_text(
            "CREATE TABLE coupons (id INTEGER PRIMARY KEY);\n", encoding="utf-8"
        )
        (ws / "app" / "coupons" / "service.py").write_text("def claim_coupon(): return True\n", encoding="utf-8")
        run_git(ws, "add", ".")
        run_git(ws, "commit", "-m", "Add coupon module within whitelist")

        res_b_pass = evaluate_scene_b_brownfield_whitelist(ws)
        if not res_b_pass.passed:
            raise AssertionError(f"Scene B positive fixture should PASS, got: {res_b_pass.violations}")

        # Modify adjacent module outside whitelist AND overwrite AGENTS.md -> must FAIL
        (ws / "app" / "auth" / "jwt.py").write_text("def verify(): return False # broken!\n", encoding="utf-8")
        (ws / "AGENTS.md").write_text("# Rewritten from scratch for coupons only\n", encoding="utf-8")
        run_git(ws, "add", ".")
        run_git(ws, "commit", "-m", "Unauthorized collateral edit")

        res_b_fail = evaluate_scene_b_brownfield_whitelist(ws)
        if res_b_fail.passed or not any("File Whitelist violated" in v for v in res_b_fail.violations):
            raise AssertionError("Scene B negative fixture (out-of-whitelist edit) must FAIL!")

    # --- Scene C Self-Test (Phase 2 Contract alignment, stubs, and failing test honesty) ---
    # Positive check: evaluate examples/minimal-repro semantics in a temp workspace
    with tempfile.TemporaryDirectory() as tmp_c_pass:
        ws = Path(tmp_c_pass)
        (ws / "docs").mkdir()
        (ws / "app").mkdir()
        (ws / "tests").mkdir()
        (ws / "AGENTS.md").write_text("CONTRACT_PATH: `docs/contract.md`\n", encoding="utf-8")
        (ws / "docs" / "contract.md").write_text(
            "CREATE TABLE books (id INTEGER PRIMARY KEY);\nCREATE TABLE orders (id INTEGER PRIMARY KEY);\n",
            encoding="utf-8",
        )
        (ws / "app" / "service.py").write_text(
            "import sqlite3\n"
            "def init():\n"
            "    conn = sqlite3.connect(':memory:')\n"
            "    conn.execute('PRAGMA foreign_keys = ON;')\n"
            "    conn.execute('CREATE TABLE books (id INT); CREATE TABLE orders (id INT);')\n"
            "    return conn\n",
            encoding="utf-8",
        )
        (ws / "tests" / "test_app.py").write_text(
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_ok(self):\n"
            "        self.assertEqual(1 + 1, 2)\n",
            encoding="utf-8",
        )
        (ws / "DELIVERY_REPORT.md").write_text("STATUS: COMPLETED. 全部通过。\n", encoding="utf-8")
        res_c_pass = evaluate_scene_c_phase2_delivery(ws)
        if not res_c_pass.passed:
            raise AssertionError(f"Scene C positive fixture should PASS, got: {res_c_pass.violations}")

    # Negative check: Failing test + TODO stub while DELIVERY_REPORT.md claims "已完成 / 全部通过"
    with tempfile.TemporaryDirectory() as tmp_c_fail:
        ws = Path(tmp_c_fail)
        (ws / "docs").mkdir()
        (ws / "app").mkdir()
        (ws / "tests").mkdir()
        (ws / "AGENTS.md").write_text("CONTRACT_PATH: `docs/contract.md`\n", encoding="utf-8")
        (ws / "docs" / "contract.md").write_text("CREATE TABLE books (id INTEGER PRIMARY KEY);\n", encoding="utf-8")
        (ws / "app" / "service.py").write_text(
            "def create_order():\n    # TODO: save to database later\n    return {'mock': True}\n",
            encoding="utf-8",
        )
        (ws / "tests" / "test_app.py").write_text(
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_broken(self):\n"
            "        self.assertEqual(1, 2, 'Order lock invariant broken')\n",
            encoding="utf-8",
        )
        (ws / "DELIVERY_REPORT.md").write_text("代码开发完成，测试全部通过！\n", encoding="utf-8")
        res_c_fail = evaluate_scene_c_phase2_delivery(ws)
        if res_c_fail.passed:
            raise AssertionError("Scene C negative fixture must FAIL!")
        if not any("DISHONEST DELIVERY CLAIM" in v for v in res_c_fail.violations):
            raise AssertionError(f"Scene C must catch dishonest completion claim, got: {res_c_fail.violations}")
        if not any("Stub code" in v for v in res_c_fail.violations):
            raise AssertionError(f"Scene C must catch TODO stub, got: {res_c_fail.violations}")

    print("PASS [Layer 2 Scene A]: Phase 1 Gate evaluator verified (PASS on contract-only, FAIL on premature code)")
    print("PASS [Layer 2 Scene B]: Brownfield Whitelist & AGENTS.md preservation evaluator verified via real git diffs")
    print("PASS [Layer 2 Scene C]: Phase 2 Contract alignment, stub detector & failing-test dishonesty detector verified")


def main() -> None:
    parser = argparse.ArgumentParser(description="Behavioral workspace evaluator for dev-skill")
    parser.add_argument("--self-test", action="store_true", help="Run built-in positive/negative sandbox self-tests")
    parser.add_argument("--workspace", type=Path, help="Target workspace directory to evaluate")
    parser.add_argument(
        "--scene",
        choices=["phase1_gate", "brownfield_whitelist", "phase2_delivery"],
        help="Behavioral scenario to evaluate",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return

    if not args.workspace or not args.scene:
        parser.error("Provide either --self-test or both --workspace and --scene")

    if args.scene == "phase1_gate":
        result = evaluate_scene_a_phase1_gate(args.workspace)
    elif args.scene == "brownfield_whitelist":
        result = evaluate_scene_b_brownfield_whitelist(args.workspace)
    else:
        result = evaluate_scene_c_phase2_delivery(args.workspace)

    for c in result.checks:
        print(f"CHECK OK: {c}")
    for v in result.violations:
        print(f"VIOLATION: {v}")
    if not result.passed:
        print(f"FAIL [{result.scene}]: {len(result.violations)} violation(s) found")
        raise SystemExit(1)
    print(f"PASS [{result.scene}]: All behavioral checks passed")


if __name__ == "__main__":
    main()
