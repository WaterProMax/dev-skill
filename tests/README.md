# Skill Structural, Consistency & Behavioral Evaluation Suite (`dev-skill`)

`dev-skill` (`v1.2.0`) uses a **two-layer verification architecture** for internal template consistency, SQLite foreign-key enforcement, and bounded workspace checks. These checks do not establish general agent compliance or production workflow quality.

| Layer | Script | What It Verifies |
|---|---|---|
| **Layer 1: Structural, YAML Schema & Template Consistency** | `tests/validate_structure.py` | 1) File & relative link existence;<br>2) `SKILL.md` frontmatter, Scale routing (`L/M/S`), and Contract Change Protocol (`L1/L2/L3`);<br>3) Deep YAML schema validation of `tests/regression-cases.yaml` (catches skeleton-only IDs if `input_prompt`, `expected_phase1_actions`, or `failure_conditions` are removed);<br>4) **Automated Template Consistency Audit** (`templates/contract.template.md` §1.2 Field Dictionary index names vs §1.4 SQL `CREATE INDEX` set, 100% status enum coverage including `OFF_SHELF`, ISBN `10~20` consistency, Enforcement Layer columns, `requirements.txt` in `AGENTS.template.md` whitelist, and live in-memory SQLite DDL execution verifying `PRAGMA foreign_keys = ON` blocks orphan orders). |
| **Layer 2: Behavioral Workspace Evaluation** | `tests/evaluate_workspace.py` | Evaluates an actual target workspace across three behavioral scenarios:<br>- **Scene A (`phase1_gate`)**: Verifies Phase 1 contract artifacts exist and **zero** business code files (`.py/.ts/.js/.go/.java`) were written prematurely;<br>- **Scene B (`brownfield_whitelist`)**: Inspects actual `git diff` against the File Whitelist in `docs/tasks/<task>.md`, catching out-of-whitelist edits to adjacent modules and destructive overwrites of root `AGENTS.md`;<br>- **Scene C (`phase2_delivery`)**: Verifies code-to-contract table alignment, `PRAGMA foreign_keys = ON`, absence of `# TODO`/`NotImplementedError`/mock stubs, and **executes the workspace test suite**, catching dishonest completion claims when tests fail. |
| **Reproducible Invariant Suite** | `examples/minimal-repro/test_minimal_repro.py` | Zero-dependency `sqlite3` + `unittest` suite verifying foreign key constraints (`PRAGMA foreign_keys = ON`) and all 4 Business Invariants (`INV-1` atomic lock & `40901`, `INV-2` transaction failure rollback, `INV-3` targeted cancel lock release & `40903` terminal retry block, `INV-4` owner permission `40301` & `OFF_SHELF` `40902`). |

## Running All Checks

`regression-cases.yaml` now defines 11 scenarios, including five conditional search/recommendation cases for source and executable evidence, query intent preservation, complementary selection and user constraints, fair fixed/live comparisons, and abstention/claim boundaries. Layer 1 validates the scenario definitions and links; it **does not run an agent, a search provider, or the recommendation workflow**. The existing Layer 2 self-tests execute workspace fixtures for the original three scenes only. To assess the new behavior, run the relevant prompts against an actual target project in an isolated workspace, retain artifacts/logs, and evaluate each stated failure condition; do not count schema validation as those scenarios passing.

Run from the repository root:

```bash
# 1. Layer 1: Deep structure, YAML schema & template consistency audit
python3 tests/validate_structure.py

# 2. Layer 2: Behavioral workspace evaluator (positive & negative sandbox self-tests)
python3 tests/evaluate_workspace.py --self-test

# 3. Reproducible Minimal Example (5 invariant tests on SQLite with PRAGMA foreign_keys = ON)
python3 -m unittest discover -s examples/minimal-repro -v
```

## Workspace evaluator limits and runtime plan

Scene A accepts a non-empty Markdown exclusions section in either `AGENTS.md` or `docs/tasks/*.md`. Supported titles include `Non-Goals`, `不做项`, `非目标`, `明确不做`, and `长期边界`; an empty heading, HTML comment, or an unrelated mention of the keyword is insufficient. This is a document-structure check, not a semantic scope audit.

Scene C no longer treats an unrelated passing suite as runtime acceptance. It requires `tests/verification.json` in the target workspace (override with `--verification-plan`, relative to that workspace), with a named initialization test and a mapping for every stable `INV-N` / `AC-N` ID found in the active contract:

```json
{
  "initialization": {
    "test": "test_app.T.test_init",
    "targets": ["app/service.py:init"]
  },
  "contract_tests": {
    "INV-1": {
      "test": "test_app.T.test_tables_and_foreign_keys",
      "targets": ["app/service.py:init"]
    }
  }
}
```

The target workspace must supply the actual tests and plan; the evaluator does not generate a passing plan automatically. `test` is a Python `unittest` selector, resolved from the workspace and its `tests/` directory. `targets` lists relative production Python files and callable qualified names (for example `app/service.py:BookOrderService.create_order` on Python 3.11+). Each check runs in a fresh process, observes calls while the test executes, and rejects no tests, skipped/expected-failure tests, failed assertions, or missing declared production calls. Each subprocess has a 30-second timeout. Initialization tests should actually initialize the service and assert the resulting schema/environment; contract tests should assert the mapped behavior, including relevant failure paths.

**Compatibility change:** missing plans, missing acceptance IDs, or incomplete mappings produce `UNVERIFIED` violations and a nonzero exit rather than PASS. This runtime probe currently supports in-process Python/unittest calls; HTTP clients, child-process services, other languages/frameworks and source-less/dynamically generated targets need a suitable external verification method and are not automatically certified. Target code/tests execute with the caller's permissions; use an authorized isolated workspace.

Observed calls plus green assertions still do not prove the assertions adequately represent the contract. Review the mapping, test code and results; do not interpret PASS as complete service correctness. Static table/PRAGMA scans remain preliminary checks. This change does not address the separate Brownfield diff/whitelist heuristics.

Run the targeted evaluator regressions (including the formerly green broken-initialization fixture and English/Chinese scope declarations):

```bash
python3 -m unittest discover -s tests -p 'test_evaluate_workspace.py' -v
```
