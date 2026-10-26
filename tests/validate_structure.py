#!/usr/bin/env python3
"""Static structural and behavioral regression validator for dev-skill."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ROOT / "SKILL.md",
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "templates" / "AGENTS.template.md",
    ROOT / "templates" / "contract.template.md",
    ROOT / "examples" / "one-sentence-to-mvp.md",
    ROOT / "tests" / "README.md",
    ROOT / "tests" / "regression-cases.yaml",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


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

    # 2. Check core sections and markers in SKILL.md
    required_skill_markers = [
        "Mode 1",
        "Mode 2",
        "Phase 1",
        "Phase 2",
        "AGENTS.md",
        "docs/contract.md",
        "Step 1",
        "Step 2",
        "Step 3",
        "Single Source of Truth",
        "Contract Synchronization Protocol",
        "Common Anti-Patterns",
        "Rationalization Counter-Table",
        "Pre-Completion Verification Checklist",
    ]
    missing_skill = [m for m in required_skill_markers if m not in skill_text]
    if missing_skill:
        fail(f"SKILL.md missing required markers: {missing_skill}")

    # 3. Check relative file references in SKILL.md
    for ref in re.findall(r"`((?:templates|examples)/[^`]+\.md|CHANGELOG\.md)`", skill_text):
        if not (ROOT / ref).exists():
            fail(f"SKILL.md references non-existent file: {ref}")

    # 4. Check AGENTS.template.md 4 fixed blocks
    agents_tpl = (ROOT / "templates" / "AGENTS.template.md").read_text(encoding="utf-8")
    required_agents_blocks = [
        "1. MVP 最小闭环（Scope & Non-Goals）",
        "2. Architecture 总体框架与目录树",
        "3. 环境与启动/校验约定",
        "4. Agent 编码红线（Guardrails）",
        ".env.example",
        "Step 1 校验",
        "Step 2 校验",
        "Step 3 校验",
    ]
    missing_agents = [b for b in required_agents_blocks if b not in agents_tpl]
    if missing_agents:
        fail(f"templates/AGENTS.template.md missing required sections: {missing_agents}")

    # 5. Check contract.template.md 3 fixed blocks
    contract_tpl = (ROOT / "templates" / "contract.template.md").read_text(encoding="utf-8")
    required_contract_blocks = [
        "1. 数据库与字段设计（Database Schema）",
        "1.2 表字段字典（Field Dictionary）",
        "1.3 状态枚举与状态机流转约定",
        "1.4 可直接执行的建表 SQL",
        "2. 接口对接契约（API Contract）",
        "2.1 统一响应信封与错误码字典",
        "2.2 接口明细列表",
        "3. 外部/上下游对接与 Mock 边界说明",
    ]
    missing_contract = [b for b in required_contract_blocks if b not in contract_tpl]
    if missing_contract:
        fail(f"templates/contract.template.md missing required sections: {missing_contract}")

    # 6. Check examples/one-sentence-to-mvp.md
    example_text = (ROOT / "examples" / "one-sentence-to-mvp.md").read_text(encoding="utf-8")
    for marker in [
        "我要做后端的二手书交易模块",
        "Phase 1",
        "Phase 2",
        "AGENTS.md",
        "docs/contract.md",
        "course_name",
        "Step 1",
        "Step 2",
        "Step 3",
    ]:
        if marker not in example_text:
            fail(f"examples/one-sentence-to-mvp.md missing marker: {marker}")

    # 7. Check regression cases
    cases_text = (ROOT / "tests" / "regression-cases.yaml").read_text(encoding="utf-8")
    for case_id in [
        "one_sentence_greenfield_intercept",
        "scope_creep_overengineering",
        "brownfield_submodule_whitelist",
        "midflight_contract_drift",
        "fake_done_hardcoded_stub",
        "unverified_delivery_claim",
    ]:
        if case_id not in cases_text:
            fail(f"tests/regression-cases.yaml missing case: {case_id}")

    print("PASS: dev-skill repository structure and all required files are valid")
    print("PASS: SKILL.md frontmatter (name + SDO description) and Mode/Phase routers verified")
    print("PASS: AGENTS.template.md (4 blocks) and contract.template.md (3 blocks) verified")
    print("PASS: End-to-end walkthrough example and 6 regression cases verified")


if __name__ == "__main__":
    main()
