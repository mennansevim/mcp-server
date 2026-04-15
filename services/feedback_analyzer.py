"""
Feedback analyzer — detects recurring issue patterns from historical review data.

Consumes data from ReviewStore and produces structured pattern reports that
RuleEvolver uses to generate repo-specific rules.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any, Optional

import structlog

from services.review_store import ReviewStore

logger = structlog.get_logger()


class FeedbackAnalyzer:
    """Analyzes historical review issues for a repo and extracts patterns."""

    def __init__(self, store: Optional[ReviewStore] = None):
        self.store = store or ReviewStore()

    def analyze(self, repo: str, *, max_issues: int = 200) -> dict[str, Any]:
        """
        Produce a full pattern report for *repo*.

        Returns a dict with:
          - category_frequency: [{category, count}]
          - severity_distribution: {severity: count}
          - owasp_frequency: [{owasp_id, count}]
          - threat_type_frequency: [{threat_type, count}]
          - file_hotspots: [{file_path, category, count}]
          - directory_hotspots: [{directory, count}]
          - top_recurring_titles: [{title_pattern, count}]
          - review_stats: {total_reviews, avg_score, avg_security_score}
        """
        issues = self.store.get_repo_issues(repo, limit=max_issues)
        reviews = self.store.get_repo_reviews(repo, limit=100)

        return {
            "repo": repo,
            "total_issues_analyzed": len(issues),
            "category_frequency": self._category_frequency(issues),
            "severity_distribution": self._severity_distribution(issues),
            "owasp_frequency": self._owasp_frequency(issues),
            "threat_type_frequency": self._threat_type_frequency(issues),
            "file_hotspots": self._file_hotspots(issues),
            "directory_hotspots": self._directory_hotspots(issues),
            "top_recurring_titles": self._recurring_titles(issues),
            "review_stats": self._review_stats(reviews),
        }

    # -- private analysis methods -------------------------------------------

    @staticmethod
    def _category_frequency(issues: list[dict]) -> list[dict[str, Any]]:
        freq: dict[str, int] = defaultdict(int)
        for iss in issues:
            freq[iss.get("category", "general")] += 1
        return sorted(
            [{"category": k, "count": v} for k, v in freq.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

    @staticmethod
    def _severity_distribution(issues: list[dict]) -> dict[str, int]:
        dist: dict[str, int] = defaultdict(int)
        for iss in issues:
            dist[iss.get("severity", "info")] += 1
        return dict(dist)

    @staticmethod
    def _owasp_frequency(issues: list[dict]) -> list[dict[str, Any]]:
        freq: dict[str, int] = defaultdict(int)
        for iss in issues:
            oid = iss.get("owasp_id")
            if oid:
                freq[oid] += 1
        return sorted(
            [{"owasp_id": k, "count": v} for k, v in freq.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

    @staticmethod
    def _threat_type_frequency(issues: list[dict]) -> list[dict[str, Any]]:
        freq: dict[str, int] = defaultdict(int)
        for iss in issues:
            tt = iss.get("threat_type")
            if tt:
                freq[tt] += 1
        return sorted(
            [{"threat_type": k, "count": v} for k, v in freq.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

    @staticmethod
    def _file_hotspots(issues: list[dict], limit: int = 15) -> list[dict[str, Any]]:
        freq: dict[tuple[str, str], int] = defaultdict(int)
        for iss in issues:
            fp = iss.get("file_path")
            if fp:
                freq[(fp, iss.get("category", "general"))] += 1
        items = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [
            {"file_path": k[0], "category": k[1], "count": v} for k, v in items
        ]

    @staticmethod
    def _directory_hotspots(issues: list[dict], limit: int = 10) -> list[dict[str, Any]]:
        freq: dict[str, int] = defaultdict(int)
        for iss in issues:
            fp = iss.get("file_path")
            if fp:
                parent = str(PurePosixPath(fp).parent)
                if parent and parent != ".":
                    freq[parent] += 1
        items = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"directory": k, "count": v} for k, v in items]

    @staticmethod
    def _recurring_titles(issues: list[dict], limit: int = 10) -> list[dict[str, Any]]:
        """Group titles by a simplified pattern to find recurring themes."""
        freq: dict[str, int] = defaultdict(int)
        for iss in issues:
            title = iss.get("title", "")
            normalized = re.sub(r"(CRITICAL:\s*)", "", title).strip()
            normalized = re.sub(r"\s*\(.*?\)\s*", " ", normalized).strip()
            normalized = re.sub(r"line \d+", "line N", normalized, flags=re.IGNORECASE)
            if normalized:
                freq[normalized] += 1

        items = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"title_pattern": k, "count": v} for k, v in items]

    @staticmethod
    def _review_stats(reviews: list[dict]) -> dict[str, Any]:
        total = len(reviews)
        if total == 0:
            return {
                "total_reviews": 0,
                "avg_score": 0,
                "avg_security_score": 0,
                "block_rate": 0,
            }
        return {
            "total_reviews": total,
            "avg_score": round(sum(r["score"] for r in reviews) / total, 1),
            "avg_security_score": round(
                sum(r["security_score"] for r in reviews) / total, 1
            ),
            "block_rate": round(
                sum(1 for r in reviews if r["block_merge"]) / total * 100, 1
            ),
        }
