# Changelog

## 1.2.1 — Evaluator Adversarial Hardening, Template Alignment & Scale S Inline Contract Support

- **Template & Skill Alignment for `tests/verification.json`**: Explicitly documented `tests/verification.json` in `SKILL.md` (Phase 2 execution & pre-completion checklist), `templates/task-plan.template.md` (§3.1 File Whitelist and §5.1 runtime verification mapping), and `templates/AGENTS.template.md` (§2.3 directory tree and §4.1 File Whitelist), and bundled a live-verified `examples/minimal-repro/verification.json` mapping `initialization` and `INV-1`..`INV-4` to `test_minimal_repro.py` and `book_order_service.py`.
- **Inline-Backtick & Heading Hardening in `scope_markdown_content` (`tests/evaluate_workspace.py`)**: Fixed HTML comment parsing so inline code spans containing literal comment openers (`` `<!--` `` or ```` ``<!--`` ````) never swallow subsequent `## Non-Goals` sections; excluded 4-space/tab indented code blocks from declaring fake scope sections; added Setext heading (`===` / `---`) support alongside ATX (`#`) headings.
- **Scale S Inline Contract & Comment-Filtered Contract IDs (`tests/evaluate_workspace.py`)**: `resolve_contract_path` now falls back to `docs/tasks/<task>.md` when a `Scale S` task declares an inline contract (`CONTRACT_PATH: NONE (Scale S 内联契约)`); `evaluate_scene_c_phase2_delivery` strips Markdown comments and fenced code blocks via `scope_markdown_content` before extracting `INV-N` / `AC-N` IDs so commented/example IDs (`<!-- INV-99 -->`) do not trigger false `UNVERIFIED` failures.
- **Anti-Bypass Hardening for Static SQL/PRAGMA Scan & Runtime Call Probe (`tests/evaluate_workspace.py`)**:
  - Stripped Python `#` comments (via `tokenize`) and SQL `--` / `/* */` comments before checking contract table presence and `PRAGMA foreign_keys = ON`, blocking `# PRAGMA foreign_keys = ON` comment spoofing.
  - Hardened `run_runtime_check` to verify bytecode normal returns (`RETURN_VALUE` / `RETURN_CONST`) on `event == "return"` (or explicit `unittest.TestCase.assertRaises` verification on contract checks), blocking broken targets that raise immediately while a test swallows the exception with `try: ... except: pass`.
  - Added Python 3.10 qualified-name fallback (`self` / `cls` inspection when `co_qualname` is absent).
- **Expanded Verification Suite (`tests/validate_structure.py`, `tests/test_evaluate_workspace.py`)**: Added `tests/test_evaluate_workspace.py` and `examples/minimal-repro/verification.json` to `REQUIRED_FILES`, audited `references/evidence-driven-workflows.md` markers and Markdown links across all repository docs, and expanded `tests/test_evaluate_workspace.py` from 18 to 26 tests.

---

## 1.2.0 — Evidence-Driven Outcomes & Conditional Search Workflow Guidance

- Added `references/evidence-driven-workflows.md`, loaded only for search/recommendation/RAG/AI evaluation tasks. It turns relevant user goals into purpose-specific acceptance items, source snapshot/span checks, semantic support checks, executable artifact assertions, bounded split retries, complementary external/local coverage and learner hard/soft constraints.
- Added query abstraction guidance: remove task-specific table/column noise for general tutorials while preserving technical semantics and explicit dataset/API intent; log transformations and use bounded source relaxation rather than hardcoded golden URLs.
- Defined fixed-material vs. live-search evaluation boundaries, fair baseline disclosure, zero-denominator handling, recommendation success/abstention alongside error, and evidence limits for optimality and real learner outcomes. Illustrative SQLite cases are not presented as measured project results.
- Updated `SKILL.md`, task-plan and repository-rule templates with outcome/evidence checks; corrected the task template evaluator example to use `--scene phase2_delivery`.
- Added five regression scenario specifications (11 total); structure validation now checks Markdown reference links and reports the actual case count. Documentation explicitly distinguishes schema checks, existing workspace self-tests and unexecuted AI/live-search behavior evaluations.

---

## 1.1.0 — Verifiable Governance, Template Self-Consistency & Flexible Scale Adaptation

Upgrades `WaterProMax/dev-skill` based on comprehensive engineering review of `00a0ad4`, focusing on **rule verifiability (`规则能否被验证`)** and **flexible project adaptation (`遇到不同项目时能否灵活适配`)**.

### Added & Fixed

1. **Two-Layer Verification Suite (`tests/validate_structure.py` + `tests/evaluate_workspace.py`)**
   - **Layer 1 (`tests/validate_structure.py`)**: Replaced shallow string-search checks on `tests/regression-cases.yaml` with full YAML parsing and required-field schema validation (`id`, `name`, `mode`, `scale`, `input_prompt`, `expected_phase1_actions`, `forbidden_phase1_actions`, `failure_conditions`), plus an internal mutation guard that verifies skeleton-only YAML files (with only case IDs) are rejected. Added **Automated Template Consistency Audit** comparing Field Dictionary index sets against SQL `CREATE INDEX` statements, status enum sets against transition rows, ISBN rules across sections, and executing template DDL in in-memory SQLite with `PRAGMA foreign_keys = ON`.
   - **Layer 2 (`tests/evaluate_workspace.py`)**: Added an executable behavioral workspace evaluator supporting `--self-test` and `--workspace` across 3 core scenarios:
     - **Scene A (`phase1_gate`)**: Verifies Phase 1 contracts exist and blocks premature `.py/.ts/.js/.go/.java` implementation code.
     - **Scene B (`brownfield_whitelist`)**: Checks actual `git diff` modified files against the declared `File Whitelist` in `docs/tasks/<task>.md` and verifies root `AGENTS.md` long-term rules were not destructively overwritten.
     - **Scene C (`phase2_delivery`)**: Verifies contract table alignment, `PRAGMA foreign_keys = ON`, absence of `# TODO`/`NotImplementedError`/mock stubs, and executes live workspace tests to block dishonest completion claims when tests fail.

2. **100% Template Self-Consistency, Enforcement Layers & SQLite Foreign Keys (`templates/contract.template.md`, `templates/AGENTS.template.md`)**
   - Aligned all 9 declared indexes (`idx_books_title`, `idx_books_isbn`, `idx_books_seller`, `idx_books_status`, `uk_orders_order_no`, `idx_orders_book_id`, `uk_orders_active_book`, `idx_orders_buyer_id`, `idx_orders_status`) 100% between §1.2 Field Dictionary and §1.4 Executable DDL.
   - Completed §1.3 State Transition Matrix to cover `OFF_SHELF` entry (`ON_SALE -> OFF_SHELF` by seller only, forbidden when `RESERVED`/`SOLD` with `40902`) and exit (`OFF_SHELF -> ON_SALE` re-listing), and marked terminal vs. non-terminal states explicitly.
   - Unified `isbn` type and validation rules to `VARCHAR(20)` (`10~20` chars) across §1.2 Field Dictionary, §1.4 SQL `CHECK`, and §2.2 API Request Validation.
   - Added `requirements.txt`, `docs/tasks/**`, and `CONTRACT_PATH` to the File Whitelist in `templates/AGENTS.template.md`.
   - Added explicit `PRAGMA foreign_keys = ON;` per-connection instructions and code snippets (`sqlite3` and SQLAlchemy Engine event hook) in §1.4.
   - Added the **`保证层 (Enforcement Layer)`** column (`DB Constraint` / `Request Validation` / `Service Invariant`) across Field Dictionary, State Transitions, Business Invariants, and API Error Codes.

3. **Three-Tier Contract Synchronization Protocol (`L1 / L2 / L3`)**
   - Distinguished **L1 Clarification** (editorial/example fixes, no behavioral change -> direct sync) and **L2 Internal Detail** (within whitelist and external contract -> execute in scope) from **L3 Breaking / Behavior / Scope Change** (deleting/renaming fields, changing field semantics, altering state transitions/auth rules, or expanding scope -> **Mandatory Re-Gate** requiring human re-confirmation before editing code).

4. **Long-Term `AGENTS.md` Rules Decoupled from Per-Task Plans (`templates/task-plan.template.md`)**
   - Refactored `templates/AGENTS.template.md` around long-term repository conventions and **Source of Truth Hierarchy** (preserving existing `AGENTS.md`, OpenAPI specs, and DB migrations in Mode 2).
   - Added `templates/task-plan.template.md` (`docs/tasks/<task-slug>.md`) for current-iteration scope, `File Whitelist`, `CONTRACT_PATH` reference, and verification plan.

5. **Verifiable Business Invariants (`INV-1` ~ `INV-4`)**
   - Codified 4 mandatory business invariants in `SKILL.md` and `templates/contract.template.md` §1.5:
     - `INV-1`: Single active `PENDING` order per book (`uk_orders_active_book` partial unique index + conditional update `rowcount == 1`, returning `40901`).
     - `INV-2`: Atomic book lock and order insertion within the same database transaction with full rollback on failure.
     - `INV-3`: Targeted lock release on cancellation (`PENDING -> CANCELLED` releases only its own `RESERVED` book) and terminal state repeat rejection (`40903`).
     - `INV-4`: Explicit separation of Mock Identity carrier vs. real Owner Authorization rules (`40301 FORBIDDEN_NOT_OWNER`, `40002 SELF_PURCHASE_FORBIDDEN`).

6. **Task Scale Routing (`Scale L / Scale M / Scale S`)**
   - Added three task scale tiers in `SKILL.md` and `templates/task-plan.template.md` so pure frontend components, CLI tools, algorithm modules, and small bugfixes (`Scale S`) expand only the I/O contract and targeted tests they actually need without inventing unnecessary DB tables or REST APIs.

7. **Clear Evidence Boundary & Zero-Dependency Reproducible Example (`examples/minimal-repro/`)**
   - Added an explicit Evidence Boundary banner to `examples/one-sentence-to-mvp.md` and bundled `examples/minimal-repro/` (`schema.sql`, `book_order_service.py`, `test_minimal_repro.py`) runnable via `python3 -m unittest discover -s examples/minimal-repro -v`.

---

## 1.0.0 — Contract-First MVP & Scoped Development Skill (`dev-skill`)

Initial public release of `WaterProMax/dev-skill`, completing the team's AI engineering skill triad alongside `drawing-skill` and `writing-skill`.
