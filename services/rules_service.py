"""
Rules helper: reads rule markdown files directly from the local filesystem.
No external service dependency — used as an in-process utility.
"""

from __future__ import annotations

import structlog
from pathlib import Path
from typing import Any, Optional

logger = structlog.get_logger()

RULES_DIR = Path(__file__).parent.parent / "rules"

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


class RulesHelper:
    """Reads and resolves rule .md files from the local rules/ directory."""

    def __init__(self, rules_dir: Optional[Path] = None):
        self.rules_dir = rules_dir or RULES_DIR
        logger.info("rules_helper_initialized", rules_dir=str(self.rules_dir))

    def list_rules(
        self,
        language: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if not self.rules_dir.exists():
            return []

        items: list[dict[str, Any]] = []
        for p in sorted(self.rules_dir.glob("*.md")):
            parts = p.stem.split("-", 1)
            lang = parts[0] if len(parts) == 2 else None
            cat = parts[1] if len(parts) == 2 else p.stem
            items.append({"filename": p.name, "language": lang, "category": cat})

        if language:
            items = [x for x in items if (x.get("language") or "").lower() == language.lower()]
        if category:
            items = [x for x in items if (x.get("category") or "").lower() == category.lower()]
        return items

    def get_rule(self, filename: str) -> Optional[str]:
        if "/" in filename or "\\" in filename or ".." in filename:
            logger.warning("invalid_rule_filename", filename=filename)
            return None

        p = self.rules_dir / filename
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None

    def resolve_rules(
        self,
        focus_areas: list[str],
        language: Optional[str] = None,
    ) -> dict[str, Any]:
        used_files: list[str] = []
        parts: list[str] = []

        for area in focus_areas:
            area_l = (area or "").lower()
            base_file = FOCUS_RULE_FILES.get(area_l)
            if not base_file:
                continue

            if language:
                cat = base_file.replace(".md", "")
                lang_file = f"{language}-{cat}.md"
                lang_path = self.rules_dir / lang_file
                if lang_path.exists():
                    used_files.append(lang_file)
                    parts.append(f"\n## Rules for {language.upper()}: {area_l.upper()}\n{lang_path.read_text(encoding='utf-8')}")
                    continue

            base_path = self.rules_dir / base_file
            if base_path.exists():
                used_files.append(base_file)
                parts.append(f"\n## Rules for: {area_l.upper()}\n{base_path.read_text(encoding='utf-8')}")

        return {
            "language": language,
            "focus_areas": focus_areas,
            "files": used_files,
            "content": "\n\n".join(parts).strip(),
        }
