"""
Default template — compact: score, issue counts, critical/high details only.
Includes AI Slop badge when low-quality AI-generated code patterns are detected.
"""

from __future__ import annotations

from urllib.parse import quote

from models import ReviewResult, IssueSeverity
from review_templates.base import (
    BaseTemplate,
    SEVERITY_EMOJI,
    score_icon,
)


def _badge(label: str, value: str, color: str) -> str:
    l = quote(label, safe="")
    v = quote(str(value), safe="")
    return f"![{label}](https://img.shields.io/badge/{l}-{v}-{color}?style=flat-square)"


class DefaultTemplate(BaseTemplate):
    name = "default"
    description = "Kompakt review — skor, issue sayıları, kritik issue detayları"

    def render_summary(
        self,
        result: ReviewResult,
        *,
        show_detailed_table: bool = False,
    ) -> str:
        lines = [
            f"**Score:** {result.score}/10 {score_icon(result.score)}",
            "",
        ]

        badges = []
        if result.security_issues_count > 0:
            sec_color = "red" if result.security_score <= 4 else "orange" if result.security_score <= 7 else "brightgreen"
            badges.append(_badge("Security", f"{result.security_score}/10", sec_color))
        if result.secret_leak_detected:
            badges.append(_badge("Secret Leak", "DETECTED", "red"))
        if result.ai_slop_detected:
            badges.append(_badge("AI Slop", f"{result.ai_slop_count} detected", "ff6723"))
        if badges:
            lines.extend([" ".join(badges), ""])

        if result.total_issues > 0:
            lines.extend(["### 📊 Issues Found", f"- Total: **{result.total_issues}**"])
            for sev, attr in [
                (IssueSeverity.CRITICAL, "critical_count"),
                (IssueSeverity.HIGH, "high_count"),
                (IssueSeverity.MEDIUM, "medium_count"),
                (IssueSeverity.LOW, "low_count"),
                (IssueSeverity.INFO, "info_count"),
            ]:
                cnt = getattr(result, attr, 0)
                if cnt > 0:
                    lines.append(f"- {SEVERITY_EMOJI[sev]} {sev.value.capitalize()}: **{cnt}**")
            lines.append("")

        critical_high = [i for i in result.issues if i.severity in (IssueSeverity.CRITICAL, IssueSeverity.HIGH)]
        if critical_high:
            lines.extend(["### ⚠️ Important Issues", ""])
            for issue in critical_high[:10]:
                emoji = SEVERITY_EMOJI[issue.severity]
                loc = ""
                if issue.file_path:
                    loc = f"`{issue.file_path}`"
                    if issue.line_number:
                        loc += f":{issue.line_number}"
                lines.extend([
                    f"#### {emoji} {issue.title}",
                    f"📍 {loc} • {issue.category}" if loc else f"📍 {issue.category}",
                    "",
                    issue.description,
                    "",
                ])
                if issue.suggestion:
                    lines.extend(["**Suggestion:**", f"> {issue.suggestion}", ""])

        sec_issues = [i for i in result.issues if i.category == "security"]
        if sec_issues:
            lines.extend(["### 🔒 Security Deep Scan", ""])
            if result.owasp_categories_hit:
                lines.append(f"OWASP hit: {', '.join(result.owasp_categories_hit)}")
                lines.append("")
            for issue in sec_issues[:8]:
                emoji = SEVERITY_EMOJI[issue.severity]
                loc = ""
                if issue.file_path:
                    loc = f"`{issue.file_path}`"
                    if issue.line_number:
                        loc += f":{issue.line_number}"
                tag_parts = []
                if issue.owasp_id:
                    tag_parts.append(f"OWASP {issue.owasp_id}")
                if issue.cwe_id:
                    tag_parts.append(issue.cwe_id)
                if issue.threat_type:
                    tag_parts.append(issue.threat_type)
                tag = " • ".join(tag_parts) if tag_parts else "security"
                lines.extend([
                    f"#### {emoji} {issue.title}",
                    f"📍 {loc} • {tag}" if loc else f"📍 {tag}",
                    "",
                    issue.description,
                    "",
                ])
                if issue.code_snippet:
                    lines.extend(["**Vulnerable code:**", "```", issue.code_snippet, "```", ""])
                if issue.suggestion:
                    lines.extend(["**Fix:**", f"> {issue.suggestion}", ""])

        slop_issues = [i for i in result.issues if i.category == "ai_slop"]
        if slop_issues:
            lines.extend(["### 🤖 AI Slop Detected", ""])
            for issue in slop_issues[:5]:
                emoji = SEVERITY_EMOJI[issue.severity]
                loc = ""
                if issue.file_path:
                    loc = f"`{issue.file_path}`"
                    if issue.line_number:
                        loc += f":{issue.line_number}"
                lines.extend([
                    f"#### {emoji} {issue.title}",
                    f"📍 {loc} • ai_slop" if loc else "📍 ai_slop",
                    "",
                    issue.description,
                    "",
                ])
                if issue.code_snippet:
                    lines.extend([
                        "**Problematic code:**",
                        "```",
                        issue.code_snippet,
                        "```",
                        "",
                    ])
                if issue.suggestion:
                    lines.extend(["**Suggestion:**", f"> {issue.suggestion}", ""])

        return "\n".join(lines).rstrip()
