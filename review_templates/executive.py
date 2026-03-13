"""
Executive template — visually rich with shields.io badges, Unicode bars,
risk breakdown, and code snippets for problematic lines.
"""

from __future__ import annotations

from urllib.parse import quote

from models import ReviewResult, ReviewIssue, IssueSeverity
from review_templates.base import (
    BaseTemplate,
    SEVERITY_EMOJI,
    CATEGORY_TYPE_MAP,
)


def _badge(label: str, value: str, color: str) -> str:
    l = quote(label, safe="")
    v = quote(str(value), safe="")
    return f"![{label}](https://img.shields.io/badge/{l}-{v}-{color}?style=flat-square)"


def _score_color(score: int) -> str:
    if score >= 8:
        return "brightgreen"
    if score >= 6:
        return "yellow"
    if score >= 4:
        return "orange"
    return "red"


def _progress_bar(value: int, total: int = 10, width: int = 10) -> str:
    filled = round(value / total * width) if total > 0 else 0
    return "🟩" * filled + "⬜" * (width - filled)


def _risk_level(result: ReviewResult) -> tuple[str, str, str]:
    if result.critical_count > 0:
        return "HIGH", "🔴", "red"
    if result.high_count > 0:
        return "MEDIUM", "🟠", "orange"
    if result.medium_count > 0:
        return "LOW", "🟡", "yellow"
    return "NONE", "🟢", "brightgreen"


def _estimate_debt_hours(result: ReviewResult) -> float:
    weights = {
        IssueSeverity.CRITICAL: 2.0,
        IssueSeverity.HIGH: 1.0,
        IssueSeverity.MEDIUM: 0.5,
        IssueSeverity.LOW: 0.15,
        IssueSeverity.INFO: 0.0,
    }
    return round(sum(weights.get(i.severity, 0) for i in result.issues), 1)


CATEGORY_LABELS = {
    "compilation": "🔧 Compilation",
    "syntax": "🔧 Syntax",
    "security": "🔒 Security",
    "performance": "⚡ Performance",
    "bugs": "🐛 Bug",
    "bug": "🐛 Bug",
    "code_quality": "✨ Code Quality",
    "best_practices": "📐 Best Practices",
    "style": "🎨 Style",
    "reliability": "🛡️ Reliability",
    "maintainability": "🔩 Maintainability",
    "general": "📋 General",
    "linter": "📏 Linter",
    "ai_slop": "🤖 AI Slop",
}


class ExecutiveTemplate(BaseTemplate):
    name = "executive"
    description = "Görsel review — badge'ler, risk analizi, kod snippet'leri"

    def render_summary(
        self,
        result: ReviewResult,
        *,
        show_detailed_table: bool = False,
    ) -> str:
        risk_label, risk_emoji, risk_color = _risk_level(result)
        debt_hours = _estimate_debt_hours(result)
        sc = _score_color(result.score)

        sec_color = "red" if result.security_score <= 4 else "orange" if result.security_score <= 7 else "brightgreen"
        badge_list = [
            _badge("Quality", f"{result.score}/10", sc),
            _badge("Security", f"{result.security_score}/10", sec_color),
            _badge("Risk", risk_label, risk_color),
            _badge("Issues", str(result.total_issues), "blue"),
            _badge("Tech Debt", f"+{debt_hours}h", "blueviolet"),
            _badge("Merge",
                   "BLOCK" if result.block_merge else "OK" if result.approval_recommended else "REVIEW",
                   "red" if result.block_merge else "brightgreen" if result.approval_recommended else "orange"),
        ]
        if result.secret_leak_detected:
            badge_list.append(_badge("Secret Leak", "DETECTED", "red"))
        if result.ai_slop_detected:
            badge_list.append(_badge("AI Slop", f"{result.ai_slop_count} detected", "ff6723"))
        badges = " ".join(badge_list)

        lines = [
            "## 📊 MCP AI Code Review",
            "",
            badges,
            "",
            "---",
            "",
        ]

        # --- Combined summary table ---
        if result.total_issues > 0:
            lines.extend(self._summary_table(result))

        # --- Issues with code snippets ---
        critical_high = [i for i in result.issues if i.severity in (IssueSeverity.CRITICAL, IssueSeverity.HIGH)]
        if critical_high:
            lines.extend(self._issue_details(critical_high))

        # --- Verdict ---
        lines.append("---")
        lines.append("")
        if result.block_merge:
            lines.append(
                f"> ❌ **MERGE BLOCKED** — {result.critical_count} critical issue(s). "
                f"Fix effort: ~{debt_hours}h"
            )
        elif result.approval_recommended:
            lines.append("> ✅ **APPROVED** — No blocking issues. Safe to merge.")
        else:
            lines.append(
                f"> ⚠️ **REVIEW NEEDED** — {result.high_count} high-severity issue(s). "
                f"Consider fixing before merge."
            )

        return "\n".join(lines).rstrip()

    # ------------------------------------------------------------------

    @staticmethod
    def _summary_table(result: ReviewResult) -> list[str]:
        """Single merged table: Risk Area | Level | Issues count."""
        type_data: dict[str, dict] = {}
        for issue in result.issues:
            itype = CATEGORY_TYPE_MAP.get(issue.category.lower(), "Maintainability")
            if itype not in type_data:
                type_data[itype] = {"count": 0, "max_sev": IssueSeverity.INFO}
            type_data[itype]["count"] += 1
            sev_order = [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM, IssueSeverity.LOW, IssueSeverity.INFO]
            if sev_order.index(issue.severity) < sev_order.index(type_data[itype]["max_sev"]):
                type_data[itype]["max_sev"] = issue.severity

        lines = [
            "### Overview",
            "",
            "| Risk Area | Level | Issues |",
            "|-----------|:-----:|:------:|",
        ]
        for t in ("Security", "Reliability", "Maintainability"):
            if t in type_data:
                td = type_data[t]
                sev = td["max_sev"]
                lines.append(f"| **{t}** | {SEVERITY_EMOJI[sev]} {sev.value.capitalize()} | {td['count']} |")
        lines.append("")
        return lines

    @staticmethod
    def _issue_details(issues: list[ReviewIssue]) -> list[str]:
        lines = ["### 🎯 Issues", ""]
        seen_descriptions: set[str] = set()

        for issue in issues[:8]:
            emoji = SEVERITY_EMOJI[issue.severity]
            cat_label = CATEGORY_LABELS.get(issue.category.lower(), issue.category)
            loc = ""
            if issue.file_path:
                loc = f"`{issue.file_path}`"
                if issue.line_number:
                    loc += f":{issue.line_number}"

            lines.append(f"#### {emoji} {issue.title}")
            if loc:
                lines.append(f"📍 {loc} • {cat_label}")
            else:
                lines.append(f"📍 {cat_label}")
            lines.append("")

            desc_key = issue.description[:80].lower()
            if desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                lines.extend([issue.description, ""])

            if issue.code_snippet:
                lines.extend([
                    "**Problematic code:**",
                    "```",
                    issue.code_snippet,
                    "```",
                    "",
                ])

            if issue.suggestion:
                lines.extend([
                    "<details>",
                    "<summary><b>💡 Suggestion</b></summary>",
                    "",
                    f"> {issue.suggestion}",
                    "",
                    "</details>",
                    "",
                ])

        return lines
