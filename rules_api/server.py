"""
Standalone Rules API server.

This is intentionally separate from the main MCP server so it can be deployed
as its own service without requiring platform tokens or AI provider keys.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query


def get_rules_dir() -> Path:
    # Default is repo-local "rules/" when running from source,
    # or "/app/rules" in the container.
    return Path(os.getenv("RULES_DIR", "rules")).resolve()


# Mapping of focus areas to rule files (kept consistent with main server behavior)
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


def _safe_rule_path(rules_dir: Path, filename: str) -> Path:
    # Disallow path traversal
    if "/" in filename or "\\" in filename or filename.startswith(".") or ".." in filename:
        raise ValueError("Invalid rule filename")

    p = (rules_dir / filename).resolve()
    if rules_dir not in p.parents:
        raise ValueError("Invalid rule filename")
    return p


def list_rule_files(rules_dir: Path) -> list[dict[str, Any]]:
    if not rules_dir.exists():
        return []

    items: list[dict[str, Any]] = []
    for p in sorted(rules_dir.glob("*.md")):
        name = p.name
        stem = p.stem

        language: Optional[str] = None
        category: Optional[str] = None

        # Heuristic: language-specific rules are like "{lang}-{category}.md"
        parts = stem.split("-", 1)
        if len(parts) == 2:
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


def get_rule_content(rules_dir: Path, filename: str) -> str:
    p = _safe_rule_path(rules_dir, filename)
    if not p.exists():
        raise FileNotFoundError(filename)
    return p.read_text(encoding="utf-8")


def resolve_rules(rules_dir: Path, focus_areas: list[str], language: Optional[str] = None) -> dict[str, Any]:
    used_files: list[str] = []
    parts: list[str] = []

    for area in focus_areas:
        area_l = (area or "").lower()
        base_file = FOCUS_RULE_FILES.get(area_l)
        if not base_file:
            continue

        # Prefer language-specific file if present: "{language}-{category}.md"
        if language:
            category = base_file.replace(".md", "")
            lang_file = f"{language}-{category}.md"
            lang_path = rules_dir / lang_file
            if lang_path.exists():
                used_files.append(lang_file)
                parts.append(f"\n## Rules for {language.upper()}: {area_l.upper()}\n{lang_path.read_text(encoding='utf-8')}")
                continue

        base_path = rules_dir / base_file
        if base_path.exists():
            used_files.append(base_file)
            parts.append(f"\n## Rules for: {area_l.upper()}\n{base_path.read_text(encoding='utf-8')}")

    return {
        "rules_dir": str(rules_dir),
        "language": language,
        "focus_areas": focus_areas,
        "files": used_files,
        "content": "\n\n".join(parts).strip(),
    }


app = FastAPI(
    title="Rules API",
    description="Standalone API to list/fetch/resolve rule markdown files.",
    version="1.0.0",
)


@app.get("/")
async def health():
    rules_dir = get_rules_dir()
    return {"status": "healthy", "rules_dir": str(rules_dir)}


@app.get("/rules")
async def rules_index(language: str | None = None, category: str | None = None):
    rules_dir = get_rules_dir()
    items = list_rule_files(rules_dir)
    if language:
        items = [x for x in items if (x.get("language") or "").lower() == language.lower()]
    if category:
        items = [x for x in items if (x.get("category") or "").lower() == category.lower()]
    return {"count": len(items), "rules": items}


@app.get("/rules/resolve")
async def rules_resolve(focus: list[str] = Query(default=[]), language: str | None = None):
    rules_dir = get_rules_dir()
    return resolve_rules(rules_dir, focus_areas=focus, language=language)


@app.get("/rules/{filename}")
async def rules_get(filename: str):
    rules_dir = get_rules_dir()
    try:
        return {"filename": filename, "content": get_rule_content(rules_dir, filename)}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

