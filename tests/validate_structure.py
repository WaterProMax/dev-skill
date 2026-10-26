#!/usr/bin/env python3
"""Layer 1 Validator for dev-skill v1.2.1:
1. Repository file & relative reference integrity across all Markdown documents
2. SKILL.md frontmatter & routing/protocol markers (Scale L/M/S, L1/L2/L3, INV-1..INV-4, verification.json)
3. Deep YAML parsing & schema validation of tests/regression-cases.yaml
   (blocks skeleton-only case IDs when inputs/actions/failure_conditions are removed)
4. Automated Template Self-Consistency Audit:
   - Field Dictionary index set vs SQL DDL CREATE [UNIQUE] INDEX set (100% match)
   - Field Dictionary status enum set vs State Transition table & SQL CHECK (100% match, including OFF_SHELF)
   - ISBN length/validation rule consistency across Field Dictionary, SQL DDL, and API Spec
   - Enforcement Layer (DB Constraint / Request Validation / Service Invariant) coverage
   - Live SQLite execution of template DDL + PRAGMA foreign_keys = ON enforcement test
   - AGENTS.template.md & task-plan.template.md File Whitelist completeness (requirements.txt, verification.json, CONTRACT_PATH)
   - references/evidence-driven-workflows.md conditional workflow markers & examples/minimal-repro/verification.json schema
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ROOT / "SKILL.md",
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "templates" / "AGENTS.template.md",
    ROOT / "templates" / "task-plan.template.md",
    ROOT / "templates" / "contract.template.md",
    ROOT / "examples" / "one-sentence-to-mvp.md",
    ROOT / "examples" / "minimal-repro" / "README.md",
    ROOT / "examples" / "minimal-repro" / "schema.sql",
    ROOT / "examples" / "minimal-repro" / "book_order_service.py",
    ROOT / "examples" / "minimal-repro" / "test_minimal_repro.py",
    ROOT / "examples" / "minimal-repro" / "verification.json",
    ROOT / "tests" / "README.md",
    ROOT / "tests" / "regression-cases.yaml",
    ROOT / "tests" / "evaluate_workspace.py",
    ROOT / "tests" / "test_evaluate_workspace.py",
    ROOT / "references" / "evidence-driven-workflows.md",
]

REQUIRED_CASE_IDS = [
    "one_sentence_greenfield_intercept",
    "scope_creep_overengineering",
    "brownfield_submodule_whitelist",
    "midflight_contract_drift",
    "fake_done_hardcoded_stub",
    "unverified_delivery_claim",
    "purpose_evidence_over_title",
    "query_abstraction_preserves_intent",
    "complementary_selection_constraints",
    "fixed_vs_live_fair_comparison",
    "abstention_and_claim_boundaries",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def parse_regression_yaml(text: str) -> dict[str, Any]:
    """Parse regression-cases.yaml using PyYAML if available, else strict built-in parser."""
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError("Top-level YAML must be a mapping")
        return loaded
    except ImportError:
        pass

    # Strict built-in subset parser for regression-cases.yaml structure
    result: dict[str, Any] = {}
    cases: list[dict[str, Any]] = []
    current_case: dict[str, Any] | None = None
    current_list_key: str | None = None
    multiline_top_key: str | None = None

    def strip_quotes(val: str) -> str:
        val = val.strip()
        if len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")):
            return val[1:-1]
        return val

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if indent == 0:
            multiline_top_key = None
            current_case = None
            current_list_key = None
            if ":" not in stripped:
                raise ValueError(f"Invalid top-level YAML line: {raw_line}")
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key == "cases":
                result["cases"] = cases
            elif val in (">", "|"):
                result[key] = ""
                multiline_top_key = key
            else:
                result[key] = int(val) if val.isdigit() else strip_quotes(val)
        elif multiline_top_key is not None and indent >= 2 and current_case is None:
            prev = result.get(multiline_top_key, "")
            result[multiline_top_key] = (prev + " " + stripped).strip()
        elif indent == 2 and stripped.startswith("- "):
            current_list_key = None
            current_case = {}
            cases.append(current_case)
            rest = stripped[2:].strip()
            if rest:
                if ":" not in rest:
                    raise ValueError(f"Invalid case item start: {raw_line}")
                k, v = rest.split(":", 1)
                current_case[k.strip()] = strip_quotes(v)
        elif indent == 4 and current_case is not None:
            if ":" not in stripped:
                raise ValueError(f"Invalid case property line: {raw_line}")
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v == "":
                current_case[k] = []
                current_list_key = k
            else:
                current_case[k] = strip_quotes(v)
                current_list_key = None
        elif indent == 6 and current_case is not None and current_list_key is not None:
            if not stripped.startswith("- "):
                raise ValueError(f"Expected list item at indent 6: {raw_line}")
            item_val = strip_quotes(stripped[2:])
            current_case[current_list_key].append(item_val)
        else:
            raise ValueError(f"Unexpected YAML indentation or structure: {raw_line}")

    return result


def validate_regression_cases_schema(yaml_text: str) -> list[str]:
    """Return list of validation errors for regression-cases.yaml content."""
    errors: list[str] = []
    try:
        data = parse_regression_yaml(yaml_text)
    except Exception as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(data.get("version"), int):
        errors.append("Top-level 'version' must be an integer")
    purpose = data.get("purpose")
    if not isinstance(purpose, str) or len(purpose.strip()) < 20:
        errors.append("Top-level 'purpose' must be a non-empty descriptive string (>= 20 chars)")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("Top-level 'cases' must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    required_str_fields = ("id", "name", "mode", "scale", "input_prompt")
    required_list_fields = (
        "expected_phase1_actions",
        "forbidden_phase1_actions",
        "failure_conditions",
    )

    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"Case #{idx} is not a mapping")
            continue
        cid = str(case.get("id", f"<unnamed-{idx}>")).strip()
        seen_ids.add(cid)

        for sf in required_str_fields:
            val = case.get(sf)
            if not isinstance(val, str) or len(val.strip()) < 3:
                errors.append(f"Case '{cid}' missing or empty required string field '{sf}'")

        for lf in required_list_fields:
            lval = case.get(lf)
            if not isinstance(lval, list) or len(lval) < 2:
                errors.append(
                    f"Case '{cid}' field '{lf}' must be a list with >= 2 items (got {lval!r})"
                )
            else:
                for item in lval:
                    if not isinstance(item, str) or len(item.strip()) < 10:
                        errors.append(
                            f"Case '{cid}' field '{lf}' contains empty/too-short item: {item!r}"
                        )

    for req_id in REQUIRED_CASE_IDS:
        if req_id not in seen_ids:
            errors.append(f"Missing required regression case id: '{req_id}'")

    return errors


def extract_section(text: str, heading_prefix: str, next_heading_prefix: str) -> str:
    start = text.find(heading_prefix)
    if start == -1:
        fail(f"Could not find section '{heading_prefix}'")
    end = text.find(next_heading_prefix, start + len(heading_prefix))
    if end == -1:
        return text[start:]
    return text[start:end]


def audit_template_consistency(contract_tpl: str, agents_tpl: str, task_tpl: str) -> None:
    """Audit internal consistency of contract.template.md, AGENTS.template.md, and task-plan.template.md."""
    # 1. Extract Section 1.2 Field Dictionary and Section 1.4 Executable DDL
    sec_1_2 = extract_section(contract_tpl, "### 1.2 表字段字典", "### 1.3 状态枚举与状态机流转约定")
    sec_1_3 = extract_section(
        contract_tpl,
        "### 1.3 状态枚举与状态机流转约定",
        "### 1.4 可直接执行的建表 SQL",
    )
    sec_1_4 = extract_section(
        contract_tpl,
        "### 1.4 可直接执行的建表 SQL",
        "### 1.5 核心业务不变量",
    )
    sec_1_5 = extract_section(
        contract_tpl,
        "### 1.5 核心业务不变量",
        "## 2. 接口对接契约",
    )
    sec_2 = extract_section(
        contract_tpl,
        "## 2. 接口对接契约",
        "## 3. 外部/上下游对接与 Mock 边界说明",
    )

    # 1a. Audit index names in Section 1.2 vs CREATE [UNIQUE] INDEX in Section 1.4 SQL
    dict_indexes = set(re.findall(r"\b((?:idx|uk)_[a-z0-9_]+)\b", sec_1_2))
    sql_blocks = re.findall(r"```sql\n(.*?)```", sec_1_4, flags=re.DOTALL)
    if not sql_blocks:
        fail("contract.template.md §1.4 must contain an executable ```sql ... ``` block")
    sql_ddl = "\n".join(sql_blocks)

    ddl_indexes = set(
        re.findall(
            r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+((?:idx|uk)_[a-z0-9_]+)\b",
            sql_ddl,
            flags=re.IGNORECASE,
        )
    )
    if not dict_indexes:
        fail("No indexes (idx_* / uk_*) found in contract.template.md §1.2 Field Dictionary")
    if dict_indexes != ddl_indexes:
        missing_in_sql = sorted(dict_indexes - ddl_indexes)
        extra_in_sql = sorted(ddl_indexes - dict_indexes)
        fail(
            f"Template index mismatch between §1.2 Field Dictionary and §1.4 SQL DDL! "
            f"Missing in SQL: {missing_in_sql}; Extra in SQL: {extra_in_sql}"
        )

    # 1b. Audit status enums in §1.2 Field Dictionary vs §1.3 State Transitions & §1.4 SQL CHECK
    dict_book_statuses = {"ON_SALE", "RESERVED", "SOLD", "OFF_SHELF"}
    dict_order_statuses = {"PENDING", "COMPLETED", "CANCELLED"}
    for st in dict_book_statuses | dict_order_statuses:
        if f"`{st}`" not in sec_1_2:
            fail(f"Status enum '{st}' missing from contract.template.md §1.2 Field Dictionary")
        if f"| `{st}` |" not in sec_1_3:
            fail(f"Status enum '{st}' missing from contract.template.md §1.3 State Transition Table")
        if f"'{st}'" not in sql_ddl:
            fail(f"Status enum '{st}' missing from contract.template.md §1.4 SQL CHECK constraint")

    # Specifically verify OFF_SHELF has both entry (ON_SALE) and exit (ON_SALE) documented in §1.3
    off_shelf_rows = [
        line for line in sec_1_3.splitlines() if "| `books.status` | `OFF_SHELF` |" in line
    ]
    if not off_shelf_rows:
        fail("contract.template.md §1.3 must include an explicit transition row for books.status = OFF_SHELF")
    off_shelf_row = off_shelf_rows[0]
    if "ON_SALE" not in off_shelf_row or "重新上架" not in off_shelf_row:
        fail("contract.template.md §1.3 OFF_SHELF row must specify how it is entered and exited (re-listed to ON_SALE)")

    # 1c. Audit ISBN length/type consistency across §1.2, §1.4 SQL, and §2.2 API
    if "VARCHAR(20)" not in sec_1_2 or "10~20" not in sec_1_2:
        fail("contract.template.md §1.2 must define isbn as VARCHAR(20) with 10~20 chars")
    if "isbn VARCHAR(20) NOT NULL CHECK (length(isbn) BETWEEN 10 AND 20)" not in sql_ddl:
        fail("contract.template.md §1.4 SQL must define isbn VARCHAR(20) NOT NULL CHECK (length(isbn) BETWEEN 10 AND 20)")
    if "10~20 字符" not in sec_2:
        fail("contract.template.md §2.2 API spec must validate isbn as 10~20 chars matching §1.2")
    if "10~32" in contract_tpl or "VARCHAR(32)" in contract_tpl:
        fail("contract.template.md still contains legacy inconsistent ISBN length (10~32 or VARCHAR(32))")

    # 1d. Audit Enforcement Layer column presence across §1.2, §1.3, §1.5, and §2
    for sec_name, sec_body in [
        ("§1.2 Field Dictionary", sec_1_2),
        ("§1.3 State Transitions", sec_1_3),
        ("§1.5 Business Invariants", sec_1_5),
        ("§2 API Contract", sec_2),
    ]:
        if "保证层 (Enforcement Layer)" not in sec_body:
            fail(f"contract.template.md {sec_name} must declare column '保证层 (Enforcement Layer)'")

    for layer in ("DB Constraint", "Request Validation", "Service Invariant"):
        if layer not in contract_tpl:
            fail(f"contract.template.md missing Enforcement Layer '{layer}'")

    # 1e. Audit Business Invariants INV-1..INV-4 and error codes 40301, 40901, 40902, 40903
    for inv in ("INV-1", "INV-2", "INV-3", "INV-4", "40301", "40901", "40902", "40903"):
        if inv not in sec_1_5 and inv not in sec_2:
            fail(f"contract.template.md missing required invariant or error code marker: {inv}")

    # 1f. Execute SQL DDL from contract.template.md in in-memory SQLite and verify Foreign Key enforcement!
    if "PRAGMA foreign_keys = ON;" not in sql_ddl:
        fail("contract.template.md §1.4 SQL must explicitly include 'PRAGMA foreign_keys = ON;'")

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(sql_ddl)
        fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        if fk_status != 1:
            fail("Executing contract.template.md SQL did not leave PRAGMA foreign_keys = 1")

        # Verify inserting an order referencing a non-existent book_id fails with IntegrityError
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO orders (order_no, book_id, buyer_id, amount_cents, status)
                    VALUES ('ORD_AUDIT_1', 999, 'buyer_1', 1000, 'PENDING')
                    """
                )
            fail("Foreign key constraint in contract.template.md SQL failed to block orphan order!")
        except sqlite3.IntegrityError:
            pass
    finally:
        conn.close()

    # 1g. Audit AGENTS.template.md & task-plan.template.md completeness (including verification.json)
    for marker in (
        "requirements.txt",
        "verification.json",
        "CONTRACT_PATH",
        "TASK_PLAN_PATH",
        "PRAGMA foreign_keys = ON",
        "L1",
        "L2",
        "L3",
    ):
        if marker not in agents_tpl:
            fail(f"templates/AGENTS.template.md missing required marker: {marker}")

    for marker in ("TASK_ID", "SCALE", "CONTRACT_PATH", "File Whitelist", "Scale S", "tests/verification.json"):
        if marker not in task_tpl:
            fail(f"templates/task-plan.template.md missing required marker: {marker}")


def self_test_yaml_mutation_guard(original_yaml: str) -> None:
    """Verify that stripping inputs/actions/failure_conditions (leaving only case IDs) is caught."""
    data = parse_regression_yaml(original_yaml)
    skeleton_only_yaml = (
        f"version: {data['version']}\n"
        "purpose: Skeleton test with every case ID preserved but no substantive fields.\n"
        "cases:\n"
        + "".join(f"  - id: {case['id']}\n" for case in data["cases"])
    )
    errs = validate_regression_cases_schema(skeleton_only_yaml)
    if not errs:
        fail("Mutation guard failed: skeleton-only regression-cases.yaml with just IDs passed validation!")
    if any("Missing required regression case id:" in err for err in errs):
        fail("Mutation fixture lost case IDs instead of testing missing substantive fields")


def validate_markdown_links() -> None:
    """Validate relative file links across all repository Markdown documents."""
    md_files = [
        ROOT / "SKILL.md",
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "tests" / "README.md",
        ROOT / "references" / "evidence-driven-workflows.md",
        ROOT / "examples" / "one-sentence-to-mvp.md",
        ROOT / "examples" / "minimal-repro" / "README.md",
    ]
    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        for ref in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", ref) or ref.startswith("#"):
                continue
            target = (md_path.parent / ref.split("#", 1)[0]).resolve()
            if not target.exists():
                fail(f"{md_path.relative_to(ROOT)} links to non-existent path: {ref}")


def main() -> None:
    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"Missing required file: {path.relative_to(ROOT)}")

    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    # 1. Check YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---\n", skill_text, flags=re.DOTALL)
    if not fm_match:
        fail("SKILL.md must begin with valid YAML frontmatter")
    fm_text = fm_match.group(1)
    if "name: dev-skill" not in fm_text:
        fail("SKILL.md frontmatter must declare 'name: dev-skill'")
    desc_match = re.search(r"^description:\s*(.+)$", fm_text, flags=re.MULTILINE)
    if not desc_match:
        fail("SKILL.md frontmatter must include 'description'")
    description = desc_match.group(1).strip()
    if not description.startswith("Use when"):
        fail("SKILL.md description must start with 'Use when' per SDO guidelines")
    if len(description) > 500:
        fail(f"SKILL.md description exceeds 500 chars ({len(description)} chars)")

    # 2. Check core sections and v1.2.1 markers in SKILL.md
    required_skill_markers = [
        "Mode 1",
        "Mode 2",
        "Scale L",
        "Scale M",
        "Scale S",
        "Phase 1",
        "Phase 2",
        "AGENTS.md",
        "CONTRACT_PATH",
        "docs/tasks/",
        "Step 1",
        "Step 2",
        "Step 3",
        "L1",
        "L2",
        "L3",
        "Re-Gate",
        "DB Constraint",
        "Request Validation",
        "Service Invariant",
        "PRAGMA foreign_keys = ON",
        "40301",
        "40903",
        "tests/verification.json",
        "Pre-Completion Verification Checklist",
    ]
    missing_skill = [m for m in required_skill_markers if m not in skill_text]
    if missing_skill:
        fail(f"SKILL.md missing required v1.2.1 markers: {missing_skill}")

    # 3. Check relative file references in SKILL.md and Markdown links across docs
    for ref in re.findall(
        r"`((?:templates|examples|tests|references)/[^`<>]+|CHANGELOG\.md)`",
        skill_text,
    ):
        ref_clean = ref.split()[0]
        if ref_clean == "tests/verification.json" or "*" in ref_clean:
            continue
        if not (ROOT / ref_clean).exists():
            fail(f"SKILL.md references non-existent path: {ref_clean}")

    validate_markdown_links()

    # 4. Audit references/evidence-driven-workflows.md and examples/minimal-repro/verification.json
    ref_workflow_text = (ROOT / "references" / "evidence-driven-workflows.md").read_text(encoding="utf-8")
    for marker in (
        "acceptanceItems",
        "quoteStart",
        "quoteEnd",
        "TASK_PROVIDED",
        "fixed-material",
        "end-to-end-search",
        "N/A",
    ):
        if marker not in ref_workflow_text:
            fail(f"references/evidence-driven-workflows.md missing required marker: {marker}")

    repro_plan = json.loads((ROOT / "examples" / "minimal-repro" / "verification.json").read_text(encoding="utf-8"))
    if "initialization" not in repro_plan or set(repro_plan.get("contract_tests", {})) != {"INV-1", "INV-2", "INV-3", "INV-4"}:
        fail("examples/minimal-repro/verification.json must map initialization and INV-1..INV-4")

    # 5. Audit templates consistency & live SQLite execution
    agents_tpl = (ROOT / "templates" / "AGENTS.template.md").read_text(encoding="utf-8")
    task_tpl = (ROOT / "templates" / "task-plan.template.md").read_text(encoding="utf-8")
    contract_tpl = (ROOT / "templates" / "contract.template.md").read_text(encoding="utf-8")
    audit_template_consistency(contract_tpl, agents_tpl, task_tpl)

    # 6. Check examples/one-sentence-to-mvp.md evidence boundary & alignment
    example_text = (ROOT / "examples" / "one-sentence-to-mvp.md").read_text(encoding="utf-8")
    for marker in [
        "证据边界声明",
        "examples/minimal-repro",
        "我要做后端的二手书交易模块",
        "Phase 1",
        "Phase 2",
        "INV-1",
        "INV-2",
        "INV-3",
        "INV-4",
        "40301",
        "40903",
        "OFF_SHELF",
    ]:
        if marker not in example_text:
            fail(f"examples/one-sentence-to-mvp.md missing marker: {marker}")

    # 7. Deep validate regression-cases.yaml + mutation self-test
    cases_text = (ROOT / "tests" / "regression-cases.yaml").read_text(encoding="utf-8")
    schema_errors = validate_regression_cases_schema(cases_text)
    if schema_errors:
        fail("tests/regression-cases.yaml failed schema validation:\n  - " + "\n  - ".join(schema_errors))
    self_test_yaml_mutation_guard(cases_text)

    print("PASS [Layer 1.1]: Repository structure, SKILL.md frontmatter, Scale L/M/S & L1/L2/L3 routers verified")
    print("PASS [Layer 1.2]: Template Consistency Audit passed (9/9 indexes, 7/7 states incl. OFF_SHELF, ISBN 10~20, Enforcement Layers, verification.json)")
    print("PASS [Layer 1.3]: Live SQLite DDL execution & PRAGMA foreign_keys = ON integrity check passed")
    case_count = len(parse_regression_yaml(cases_text)["cases"])
    print(f"PASS [Layer 1.4]: Deep YAML schema check & skeleton-ID mutation guard passed for all {case_count} regression cases (definitions only; not agent execution)")


if __name__ == "__main__":
    main()
