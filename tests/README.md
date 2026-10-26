# Skill Regression & Structure Tests (`dev-skill`)

These tests protect the structural completeness and behavioral guardrails of `dev-skill`.

## Static structure check

Run from the repository root:

```bash
python3 tests/validate_structure.py
```

The script verifies:
- Existence of `SKILL.md`, `README.md`, `CHANGELOG.md`, `templates/AGENTS.template.md`, `templates/contract.template.md`, and `examples/one-sentence-to-mvp.md`;
- Valid YAML frontmatter in `SKILL.md` (`name: dev-skill`, SDO-compliant `description` starting with `Use when` and under 500 characters);
- Presence of both operating modes (`Mode 1`, `Mode 2`), `Phase 1` Hard Contract Gate, and `Phase 2` Stepwise Coding Discipline (`Step 1`, `Step 2`, `Step 3`);
- Presence of all 4 required blocks in `templates/AGENTS.template.md` and all 3 required blocks in `templates/contract.template.md`;
- Resolution of all relative markdown file references (`templates/...`, `examples/...`, `CHANGELOG.md`) in `SKILL.md`;
- Presence of all 6 behavioral regression scenarios in `tests/regression-cases.yaml`.
