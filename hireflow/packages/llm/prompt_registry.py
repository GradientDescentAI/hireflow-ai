"""
Version-controlled prompt store.

Prompts live in packages/llm/prompts/<stage>/<version>.txt (system)
and packages/llm/prompts/<stage>/<version>_user.txt (user template).

Version is pinned globally; individual tenants can be pinned to a specific
version for scoring reproducibility (SC-001).
"""

import os
from pathlib import Path
from string import Template

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_CURRENT_VERSION = "v1"


def _load(stage: str, role: str, version: str) -> str:
    path = _PROMPTS_DIR / stage / f"{version}_{role}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def get_system_prompt(stage: str, version: str | None = None) -> str:
    return _load(stage, "system", version or _CURRENT_VERSION)


def get_user_prompt(stage: str, variables: dict, version: str | None = None) -> str:
    template_text = _load(stage, "user", version or _CURRENT_VERSION)
    return Template(template_text).safe_substitute(variables)


def list_versions(stage: str) -> list[str]:
    stage_dir = _PROMPTS_DIR / stage
    if not stage_dir.exists():
        return []
    return sorted(
        p.stem.replace("_system", "").replace("_user", "")
        for p in stage_dir.glob("*_system.txt")
    )
