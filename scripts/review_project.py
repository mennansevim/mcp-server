"""
Toplu Proje Review Script
Bir klasördeki tüm kaynak dosyaları MCP AI Review Server üzerinden review eder.

Kullanım:
    python scripts/review_project.py /path/to/project
    python scripts/review_project.py /path/to/project --extensions .cs .py
    python scripts/review_project.py /path/to/project --provider anthropic --model claude-3-5-sonnet-20241022
    python scripts/review_project.py /path/to/project --focus security
    python scripts/review_project.py /path/to/project --output report.json
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.ai_reviewer import AIReviewer
from services.diff_analyzer import DiffAnalyzer
from tools.review_tools import ReviewTools

DEFAULT_EXTENSIONS = {
    ".py", ".cs", ".java", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".swift", ".kt", ".scala", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".dart", ".vue", ".sh",
}

SKIP_DIRS = {
    "node_modules", ".git", "bin", "obj", "dist", "build",
    "__pycache__", ".venv", "venv", ".next", "coverage",
    "packages", ".vs", ".idea", "vendor", "target",
}

MAX_FILE_SIZE = 50_000


def collect_files(project_path: Path, extensions: set[str]) -> list[Path]:
    files = []
    for f in sorted(project_path.rglob("*")):
        if any(skip in f.parts for skip in SKIP_DIRS):
            continue
        if f.is_file() and f.suffix.lower() in extensions and f.stat().st_size <= MAX_FILE_SIZE:
            files.append(f)
    return files


def detect_language(ext: str) -> str:
    mapping = {
        ".py": "python", ".cs": "csharp", ".java": "java",
        ".js": "javascript", ".ts": "typescript", ".tsx": "typescript",
        ".jsx": "javascript", ".go": "go", ".rs": "rust",
        ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
        ".rb": "ruby", ".php": "php", ".c": "c", ".cpp": "cpp",
        ".h": "c", ".hpp": "cpp", ".dart": "dart", ".vue": "vue",
        ".sh": "shell",
    }
    return mapping.get(ext.lower(), "auto")


async def review_file(
    tools: ReviewTools,
    file_path: Path,
    project_path: Path,
    focus: list[str],
    provider: str | None,
    model: str | None,
) -> dict:
    relative = file_path.relative_to(project_path)
    code = file_path.read_text(encoding="utf-8", errors="replace")
    language = detect_language(file_path.suffix)

    if len(code.strip()) < 10:
        return {"file": str(relative), "skipped": True, "reason": "empty"}

    truncated = False
    if len(code) > 10_000:
        code = code[:10_000]
        truncated = True

    args = {
        "code": code,
        "language": language,
        "focus": focus,
    }
    if provider:
        args["provider"] = provider
    if model:
        args["model"] = model

    start = time.time()
    raw = await tools._review_code(args)
    elapsed = round(time.time() - start, 1)

    result = json.loads(raw)
    result["file"] = str(relative)
    result["language"] = language
    result["lines"] = code.count("\n") + 1
    result["truncated"] = truncated
    result["review_time_sec"] = elapsed
    return result


def severity_rank(s: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(s, 5)


def print_file_result(r: dict, idx: int, total: int):
    if r.get("skipped"):
        print(f"  [{idx}/{total}] {r['file']} — atlandı ({r.get('reason', '')})")
        return

    score = r.get("score", "?")
    issues = r.get("total_issues", 0)
    secs = r.get("review_time_sec", 0)

    if score >= 8:
        icon = "🟢"
    elif score >= 5:
        icon = "🟡"
    else:
        icon = "🔴"

    trunc = " (truncated)" if r.get("truncated") else ""
    print(f"  [{idx}/{total}] {icon} {r['file']}{trunc} — Score: {score}/10 | Issues: {issues} | {secs}s")


def print_summary(results: list[dict], total_time: float):
    reviewed = [r for r in results if not r.get("skipped") and not r.get("error")]
    skipped = [r for r in results if r.get("skipped")]
    errors = [r for r in results if r.get("error")]

    if not reviewed:
        print("\n  Review edilecek dosya bulunamadı.")
        return

    scores = [r["score"] for r in reviewed if "score" in r]
    all_issues = []
    for r in reviewed:
        for iss in r.get("issues", []):
            iss["_file"] = r["file"]
            all_issues.append(iss)

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    critical = sum(1 for i in all_issues if i.get("severity") == "critical")
    high = sum(1 for i in all_issues if i.get("severity") == "high")
    medium = sum(1 for i in all_issues if i.get("severity") == "medium")
    low = sum(1 for i in all_issues if i.get("severity") == "low")

    print("\n" + "=" * 70)
    print("  PROJE REVIEW RAPORU")
    print("=" * 70)
    print(f"  Dosya sayısı   : {len(reviewed)} reviewed | {len(skipped)} skipped | {len(errors)} error")
    print(f"  Ortalama Score : {avg_score}/10")
    print(f"  Toplam Issue   : {len(all_issues)}")
    print(f"  Critical       : {critical}")
    print(f"  High           : {high}")
    print(f"  Medium         : {medium}")
    print(f"  Low            : {low}")
    print(f"  Toplam Süre    : {round(total_time, 1)}s")

    if critical + high > 0:
        print(f"\n  ⚠️  CRITICAL / HIGH SORUNLAR:")
        important = sorted(
            [i for i in all_issues if i.get("severity") in ("critical", "high")],
            key=lambda x: severity_rank(x.get("severity", "")),
        )
        for i, iss in enumerate(important, 1):
            sev = iss.get("severity", "?").upper()
            print(f"    {i}. [{sev}] {iss.get('title', '')} — {iss['_file']}")
            if iss.get("suggestion"):
                print(f"       → {iss['suggestion'][:120]}")

    worst = sorted(reviewed, key=lambda r: r.get("score", 10))[:5]
    print(f"\n  📉 EN DÜŞÜK PUANLI DOSYALAR:")
    for r in worst:
        print(f"    {r.get('score', '?')}/10  {r['file']} ({r.get('total_issues', 0)} issue)")

    print("=" * 70)


async def main():
    parser = argparse.ArgumentParser(description="Proje genelini AI ile review et")
    parser.add_argument("project_path", help="Review edilecek proje klasörü")
    parser.add_argument("--extensions", nargs="+", default=None, help="Dosya uzantıları (ör: .cs .py)")
    parser.add_argument("--focus", nargs="+", default=["security", "bugs", "performance", "compilation"], help="Focus alanları")
    parser.add_argument("--provider", default=None, help="AI provider (groq, openai, anthropic)")
    parser.add_argument("--model", default=None, help="AI model override")
    parser.add_argument("--output", default=None, help="JSON rapor çıktı dosyası")
    parser.add_argument("--max-files", type=int, default=100, help="Maksimum dosya sayısı")
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        print(f"  Hata: {project_path} klasörü bulunamadı.")
        sys.exit(1)

    extensions = set(args.extensions) if args.extensions else DEFAULT_EXTENSIONS

    print(f"\n  MCP AI Project Review")
    print(f"  Proje   : {project_path}")
    print(f"  Focus   : {', '.join(args.focus)}")
    if args.provider:
        print(f"  Provider: {args.provider}" + (f" / {args.model}" if args.model else ""))
    print()

    files = collect_files(project_path, extensions)
    if not files:
        print("  Uygun dosya bulunamadı.")
        sys.exit(0)

    if len(files) > args.max_files:
        print(f"  ⚠️  {len(files)} dosya bulundu, ilk {args.max_files} tanesi review edilecek.")
        files = files[:args.max_files]
    else:
        print(f"  📂 {len(files)} dosya bulundu. Review başlıyor...\n")

    reviewer = AIReviewer()
    analyzer = DiffAnalyzer()
    tools = ReviewTools(reviewer, analyzer)

    results = []
    start_total = time.time()

    for idx, f in enumerate(files, 1):
        try:
            result = await review_file(tools, f, project_path, args.focus, args.provider, args.model)
            results.append(result)
            print_file_result(result, idx, len(files))
        except Exception as e:
            err = {"file": str(f.relative_to(project_path)), "error": str(e)}
            results.append(err)
            print(f"  [{idx}/{len(files)}] ❌ {err['file']} — HATA: {e}")

    total_time = time.time() - start_total
    print_summary(results, total_time)

    if args.output:
        report = {
            "project": str(project_path),
            "date": datetime.now().isoformat(),
            "provider": args.provider,
            "model": args.model,
            "focus": args.focus,
            "total_files": len(results),
            "total_time_sec": round(total_time, 1),
            "results": results,
        }
        Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\n  📄 Detaylı rapor: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
