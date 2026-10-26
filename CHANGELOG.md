# Changelog

## 1.0.0 — Contract-First MVP & Scoped Development Skill (`dev-skill`)

Initial public release of `WaterProMax/dev-skill`, completing the team's AI engineering skill triad alongside `drawing-skill` and `writing-skill`.

### Added

1. **Two Operating Modes (`SKILL.md`)**
   - **Mode 1 — Greenfield MVP (`从零立项`)**: Converts vague, one-sentence novice requests (e.g., *"我要做后端的XX"*) into a bounded MVP contract package before any business code is written.
   - **Mode 2 — Brownfield / Scoped Dev (`已有仓库开发 / 子模块扩展`)**: Enforces pre-contract repository reconnaissance (existing stack, directory structure, DB entities, response wrappers) and locks an explicit **File Whitelist** so agents never break adjacent modules.
2. **Phase 1 Hard Contract Gate (`A+B 混合双契约门禁`)**
   - **`AGENTS.md` Master Steering Contract** (`templates/AGENTS.template.md`): Fixed 4-section structure covering (1) MVP Scope & Non-Goals, (2) Architecture & file-level directory tree, (3) Environment variables & step-by-step verification commands, and (4) Agent coding guardrails & file whitelist.
   - **`docs/contract.md` Schema & API Contract** (`templates/contract.template.md`): Fixed 3-section structure covering (1) Database tables, full column dictionary, state enum transition matrix, and executable DDL, (2) Unified response envelope, error code dictionary, and endpoint request/response JSON examples, and (3) Upstream/downstream integration & explicit `REAL` vs `MOCK` boundaries.
3. **Phase 2 Stepwise Verifiable Coding Discipline**
   - Enforces **Single Source of Truth** (100% alignment between implementation code and `docs/contract.md`) and a **Contract Synchronization Protocol** (update contract first when mid-flight changes occur).
   - 3-step execution pipeline: **Step 1** (`.env.example` + Skeleton + DB Schema/Model) → **Step 2** (Core Service + API Endpoints + Unit Tests) → **Step 3** (Live Server Startup + `curl` End-to-End Smoke Verification).
4. **Anti-Patterns, Rationalization Counters & End-to-End Walkthrough**
   - Documented the 5 classic novice failure modes (*Zero-Contract Code Dump*, *Scope Creep & Over-Engineering*, *Schema & API Drift*, *Fake-Done Stubs*, and *Brownfield Collateral Damage*) and their interception rules.
   - Added `examples/one-sentence-to-mvp.md` showing a complete 2-round walkthrough from *"我要做后端的二手书交易模块"* to verified delivery.
   - Added `tests/validate_structure.py` and `tests/regression-cases.yaml` for automated structural and behavioral regression verification.
