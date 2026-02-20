"""
Rules service: list and fetch rule markdown files safely, and resolve which
rules apply for a given language + focus areas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from services.language_detector import LanguageDetector


RULES_DIR = Path(__file__).parent.parent / "rules"


# Mapping of focus areas to rule files (shared with AIReviewer logic)
FOCUS_RULE_FILES: dict[str, str] = {
    "compilation": "compilation.md",
    "security": "security.md",
    "performance": "performance.md",
    "dotnet": "dotnet-fundamentals.md",
    "dotnet_fundamentals": "dotnet-fundamentals.md",
    "best_practices": "best-practices.md",
    "code_quality": "best-practices.md",
    "bugs": "compilation.md",
}


def _safe_rule_path(filename: str) -> Path:
    # Disallow path traversal
    if "/" in filename or "\\" in filename or filename.startswith(".") or ".." in filename:
        raise ValueError("Invalid rule filename")
    p = (RULES_DIR / filename).resolve()
    if RULES_DIR.resolve() not in p.parents:
        raise ValueError("Invalid rule filename")
    return p


def list_rule_files() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not RULES_DIR.exists():
        return items

    supported_langs = set(LanguageDetector.get_supported_languages())

    for p in sorted(RULES_DIR.glob("*.md")):
        name = p.name
        stem = p.stem  # without .md
        language: Optional[str] = None
        category: Optional[str] = None

        # Heuristic: language-specific rules are like "{lang}-{category}.md"
        # where lang is one of supported languages.
        parts = stem.split("-", 1)
        if len(parts) == 2 and parts[0] in supported_langs:
            language, category = parts[0], parts[1]
        else:
            category = stem

        items.append(
            {
                "filename": name,
                "language": language,
                "category": category,
            }
        )

    return items


def get_rule_content(filename: str) -> str:
    p = _safe_rule_path(filename)
    if not p.exists():
        raise FileNotFoundError(filename)
    return p.read_text(encoding="utf-8")


def resolve_rules(focus_areas: list[str], language: Optional[str] = None) -> dict[str, Any]:
    """
    Resolve which rule files to use for given focus areas and optional language.
    """
    used_files: list[str] = []
    parts: list[str] = []

    supported_langs = set(LanguageDetector.get_supported_languages())
    if language and language not in supported_langs:
        # keep behavior strict
        raise ValueError(f"Unsupported language: {language}")

    for area in focus_areas:
        area_l = (area or "").lower()
        base_file = FOCUS_RULE_FILES.get(area_l)
        if not base_file:
            continue

        # Prefer language-specific rule file if it exists: "{language}-{category}.md"
        if language:
            category = base_file.replace(".md", "")
            lang_file = f"{language}-{category}.md"
            lang_path = RULES_DIR / lang_file
            if lang_path.exists():
                used_files.append(lang_file)
                parts.append(f"\n## Rules for {language.upper()}: {area_l.upper()}\n{lang_path.read_text(encoding='utf-8')}")
                continue

        # Fallback to general file
        base_path = RULES_DIR / base_file
        if base_path.exists():
            used_files.append(base_file)
            parts.append(f"\n## Rules for: {area_l.upper()}\n{base_path.read_text(encoding='utf-8')}")

    return {
        "language": language,
        "focus_areas": focus_areas,
        "files": used_files,
        "content": "\n\n".join(parts).strip(),
    }

