"""
Custom template — renders from a user-provided markdown template file.
Supports simple {variable} placeholders.
"""

from __future__ import annotations

import structlog
from pathlib import Path
from typing import Optional

from models import ReviewResult, IssueSeverity
from review_templates.base import BaseTemplate, SEVERITY_EMOJI, score_icon

logger = structlog.get_logger()

TEMPLATES_DIR = Path(__file__).parent.parent / "custom_templates"


class CustomTemplate(BaseTemplate):
    name = "custom"
    description = "Kullanıcı tanımlı markdown şablon dosyasından render eder"

    def __init__(self, template_file: Optional[str] = None):
        self.template_file = template_file
        self._template_content: Optional[str] = None
        if template_file:
            self._load(template_file)

    def _load(self, filename: str) -> None:
        path = TEMPLATES_DIR / filename
        if path.exists():
            self._template_content = path.read_text(encoding="utf-8")
            logger.info("custom_template_loaded", file=filename)
        else:
            logger.warning("custom_template_not_found", file=filename, dir=str(TEMPLATES_DIR))

    def render_summary(
        self,
        result: ReviewResult,
        *,
        show_detailed_table: bool = False,
    ) -> str:
        if not self._template_content:
            logger.warning("custom_template_empty_falling_back")
            from review_templates.default import DefaultTemplate
            return DefaultTemplate().render_summary(result, show_detailed_table=show_detailed_table)

        issues_table = self._build_issues_table(result)
        recommendation = self._build_recommendation(result)

        placeholders = {
            "score": str(result.score),
            "score_icon": score_icon(result.score),
            "total_issues": str(result.total_issues),
            "critical_count": str(result.critical_count),
            "high_count": str(result.high_count),
            "medium_count": str(result.medium_count),
            "low_count": str(result.low_count),
            "info_count": str(result.info_count),
            "summary": result.summary,
            "issues_table": issues_table,
            "recommendation": recommendation,
            "block_merge": str(result.block_merge).lower(),
            "approval_recommended": str(result.approval_recommended).lower(),
        }

        output = self._template_content
        for key, value in placeholders.items():
            output = output.replace("{" + key + "}", value)

        return output

    @staticmethod
    def _build_issues_table(result: ReviewResult) -> str:
        if not result.issues:
            return "*No issues found.*"
        lines = [
            "| # | Severity | File | Line | Title |",
            "|---|----------|------|------|-------|",
        ]
        for idx, issue in enumerate(result.issues, 1):
            emoji = SEVERITY_EMOJI[issue.severity]
            loc = f"`{issue.file_path}`" if issue.file_path else "-"
            ln = str(issue.line_number) if issue.line_number else "-"
            lines.append(f"| {idx} | {emoji} {issue.severity.value.upper()} | {loc} | {ln} | {issue.title} |")
        return "\n".join(lines)

    @staticmethod
    def _build_recommendation(result: ReviewResult) -> str:
        if result.block_merge:
            return "❌ **Do not merge** — Critical issues must be fixed first."
        if result.approval_recommended:
            return "✅ **Approved** — Code looks good!"
        return "⚠️ **Review recommended** — Please address the issues above."
