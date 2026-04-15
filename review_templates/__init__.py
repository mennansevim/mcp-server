"""
Review Templates Registry
Provides get_template() to resolve a template by name from config.
"""

from __future__ import annotations

import structlog
from typing import Optional

from review_templates.base import BaseTemplate
from review_templates.default import DefaultTemplate
from review_templates.detailed import DetailedTemplate
from review_templates.executive import ExecutiveTemplate
from review_templates.custom import CustomTemplate

logger = structlog.get_logger()

BUILTIN_TEMPLATES: dict[str, type[BaseTemplate]] = {
    "default": DefaultTemplate,
    "detailed": DetailedTemplate,
    "executive": ExecutiveTemplate,
}


def get_template(template_config: Optional[dict] = None) -> BaseTemplate:
    """
    Resolve a template instance from review.template config block.

    Config examples:
        template:
          name: "default"

        template:
          name: "detailed"

        template:
          name: "custom"
          file: "my_team_template.md"
    """
    if template_config is None:
        template_config = {}
    if isinstance(template_config, str):
        template_config = {"name": template_config}

    name = template_config.get("name", "default").lower().strip()

    if name == "custom":
        tmpl_file = template_config.get("file")
        if not tmpl_file:
            logger.warning("custom_template_no_file_specified_using_default")
            return DefaultTemplate()
        return CustomTemplate(template_file=tmpl_file)

    cls = BUILTIN_TEMPLATES.get(name)
    if cls is None:
        logger.warning("unknown_template_falling_back", requested=name)
        return DefaultTemplate()

    logger.info("template_resolved", name=name)
    return cls()


__all__ = [
    "BaseTemplate",
    "DefaultTemplate",
    "DetailedTemplate",
    "ExecutiveTemplate",
    "CustomTemplate",
    "get_template",
    "BUILTIN_TEMPLATES",
]
