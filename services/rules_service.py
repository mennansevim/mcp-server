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
REPO_RULES_DIR = RULES_DIR / "repo"

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

    def get_repo_rule(self, repo: str) -> Optional[str]:
        """Read repo-specific rule file from rules/repo/{owner}_{name}.md."""
        safe_name = repo.replace("/", "_").replace("\\", "_")
        p = REPO_RULES_DIR / f"{safe_name}.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None

    def get_owasp_rule(self) -> Optional[str]:
        """Read the dynamic OWASP Top 10 rule file if present."""
        p = self.rules_dir / "owasp-top10.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None

    def resolve_rules(
        self,
        focus_areas: list[str],
        language: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Resolve rule content for a review.

        Priority order (highest first):
          1. Repo-specific rules  (rules/repo/{owner}_{name}.md)
          2. Language-specific rules  (rules/{lang}-{category}.md)
          3. General rules  (rules/{category}.md)
          4. Dynamic OWASP rules  (rules/owasp-top10.md) — when security is a focus area
        """
        used_files: list[str] = []
        parts: list[str] = []

        # 1) Repo-specific rules (highest priority)
        if repo:
            repo_content = self.get_repo_rule(repo)
            if repo_content:
                safe_name = repo.replace("/", "_").replace("\\", "_")
                used_files.append(f"repo/{safe_name}.md")
                parts.append(f"\n## REPO-SPECIFIC RULES for {repo}\n{repo_content}")

        # 2-3) Language-specific / general rules
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

        # 4) Dynamic OWASP rules when security is a focus area
        security_focus = any(a.lower() in ("security",) for a in focus_areas)
        if security_focus:
            owasp_content = self.get_owasp_rule()
            if owasp_content:
                used_files.append("owasp-top10.md")
                parts.append(f"\n## OWASP Top 10 Rules\n{owasp_content}")

        return {
            "language": language,
            "repo": repo,
            "focus_areas": focus_areas,
            "files": used_files,
            "content": "\n\n".join(parts).strip(),
        }
