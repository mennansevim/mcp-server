"""
Base template interface for PR review comments.
All templates must implement render_summary() and render_inline().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from models import ReviewResult, ReviewIssue, IssueSeverity


SEVERITY_EMOJI = {
    IssueSeverity.CRITICAL: "🔴",
    IssueSeverity.HIGH: "🟠",
    IssueSeverity.MEDIUM: "🟡",
    IssueSeverity.LOW: "🔵",
    IssueSeverity.INFO: "ℹ️",
}

CATEGORY_TYPE_MAP = {
    "security": "Security",
    "injection": "Security",
    "broken_auth": "Security",
    "sensitive_data": "Security",
    "xxe": "Security",
    "broken_access": "Security",
    "misconfig": "Security",
    "xss": "Security",
    "deserialization": "Security",
    "vulnerable_deps": "Security",
    "insufficient_logging": "Security",
    "secret_leak": "Security",
    "bugs": "Reliability",
    "bug": "Reliability",
    "performance": "Reliability",
    "reliability": "Reliability",
    "code_quality": "Maintainability",
    "best_practices": "Maintainability",
    "maintainability": "Maintainability",
    "style": "Maintainability",
    "compilation": "Reliability",
    "general": "Maintainability",
    "ai_slop": "Maintainability",
}


def score_icon(score: int) -> str:
    if score >= 8:
        return "✅"
    if score >= 6:
        return "⚠️"
    return "❌"


class BaseTemplate(ABC):
    """Every review comment template must subclass this."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    def render_summary(
        self,
        result: ReviewResult,
        *,
        show_detailed_table: bool = False,
    ) -> str:
        """Return the full markdown summary comment."""

    def render_inline(self, issue: ReviewIssue) -> str:
        """Return markdown for a single inline comment (shared default)."""
        emoji = SEVERITY_EMOJI[issue.severity]
        lines = [
            f"{emoji} **{issue.severity.value.upper()}: {issue.title}**",
            "",
            issue.description,
        ]
        if issue.suggestion:
            lines.extend(["", "**Suggestion:**", f"> {issue.suggestion}"])
        lines.extend(["", f"*Category: {issue.category}*"])
        return "\n".join(lines)

    def render_inline_comments(self, result: ReviewResult) -> List[dict]:
        """Build the list of inline comment payloads."""
        comments = []
        for issue in result.issues:
            if issue.file_path and issue.line_number:
                comments.append({
                    "file_path": issue.file_path,
                    "line": issue.line_number,
                    "body": self.render_inline(issue),
                })
        return comments
