"""
Service for formatting and posting review comments.
Delegates rendering to the active review template.
"""

import structlog
from typing import List, Optional

from models import ReviewResult, ReviewIssue
from review_templates import BaseTemplate, get_template

logger = structlog.get_logger()


class CommentService:
    """Format review results as comments using a configurable template."""

    def __init__(self, template_config: Optional[dict] = None):
        self.template: BaseTemplate = get_template(template_config)
        logger.info(
            "comment_service_initialized",
            template=self.template.name,
        )

    def format_summary_comment(
        self,
        result: ReviewResult,
        show_detailed_table: bool = False,
    ) -> str:
        return self.template.render_summary(
            result,
            show_detailed_table=show_detailed_table,
        )

    def format_inline_comment(self, issue: ReviewIssue) -> str:
        return self.template.render_inline(issue)

    def format_inline_comments(self, result: ReviewResult) -> List[dict]:
        return self.template.render_inline_comments(result)
