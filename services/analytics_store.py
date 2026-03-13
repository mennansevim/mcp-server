"""
In-memory analytics store for review metrics.
Persists completed review snapshots and exposes aggregated statistics.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from models import ReviewResult


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalyticsStore:
    """Singleton analytics store consumed by /api/analytics endpoints."""

    _instance: AnalyticsStore | None = None
    _lock = threading.Lock()

    def __new__(cls) -> AnalyticsStore:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_store()
            return cls._instance

    def _init_store(self) -> None:
        self._reviews: list[dict[str, Any]] = []

    def record_review(
        self,
        result: ReviewResult,
        *,
        pr_id: str = "",
        repo: str = "",
        author: str = "",
        platform: str = "",
    ) -> None:
        categories: dict[str, int] = defaultdict(int)
        threat_types: dict[str, int] = defaultdict(int)
        for issue in result.issues:
            categories[issue.category] += 1
            if issue.threat_type:
                threat_types[issue.threat_type] += 1

        snapshot = {
            "ts": _utc_now_iso(),
            "pr_id": pr_id,
            "repo": repo,
            "author": author,
            "platform": platform,
            "score": result.score,
            "security_score": result.security_score,
            "total_issues": result.total_issues,
            "critical_count": result.critical_count,
            "high_count": result.high_count,
            "medium_count": result.medium_count,
            "low_count": result.low_count,
            "info_count": result.info_count,
            "ai_slop_count": result.ai_slop_count,
            "security_issues_count": result.security_issues_count,
            "secret_leak_detected": result.secret_leak_detected,
            "owasp_categories_hit": result.owasp_categories_hit,
            "block_merge": result.block_merge,
            "approval_recommended": result.approval_recommended,
            "categories": dict(categories),
            "threat_types": dict(threat_types),
        }
        with self._lock:
            self._reviews.append(snapshot)

    def get_overview(self) -> dict[str, Any]:
        with self._lock:
            reviews = list(self._reviews)

        total = len(reviews)
        if total == 0:
            return {
                "total_reviews": 0,
                "avg_score": 0,
                "avg_security_score": 0,
                "total_issues": 0,
                "total_critical": 0,
                "total_security_issues": 0,
                "total_ai_slop": 0,
                "blocked_merges": 0,
                "secret_leaks": 0,
            }

        return {
            "total_reviews": total,
            "avg_score": round(sum(r["score"] for r in reviews) / total, 1),
            "avg_security_score": round(sum(r["security_score"] for r in reviews) / total, 1),
            "total_issues": sum(r["total_issues"] for r in reviews),
            "total_critical": sum(r["critical_count"] for r in reviews),
            "total_security_issues": sum(r["security_issues_count"] for r in reviews),
            "total_ai_slop": sum(r["ai_slop_count"] for r in reviews),
            "blocked_merges": sum(1 for r in reviews if r["block_merge"]),
            "secret_leaks": sum(1 for r in reviews if r["secret_leak_detected"]),
        }

    def get_score_trend(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            reviews = list(self._reviews)
        return [
            {
                "ts": r["ts"],
                "score": r["score"],
                "security_score": r["security_score"],
                "pr_id": r["pr_id"],
            }
            for r in reviews[-limit:]
        ]

    def get_top_issues(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            reviews = list(self._reviews)

        category_totals: dict[str, int] = defaultdict(int)
        for r in reviews:
            for cat, count in r.get("categories", {}).items():
                category_totals[cat] += count

        sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        return [{"category": c, "count": n} for c, n in sorted_cats[:limit]]

    def get_security_breakdown(self) -> dict[str, Any]:
        with self._lock:
            reviews = list(self._reviews)

        owasp_hits: dict[str, int] = defaultdict(int)
        threat_totals: dict[str, int] = defaultdict(int)
        for r in reviews:
            for o in r.get("owasp_categories_hit", []):
                owasp_hits[o] += 1
            for t, count in r.get("threat_types", {}).items():
                threat_totals[t] += count

        return {
            "owasp_distribution": dict(owasp_hits),
            "threat_types": dict(threat_totals),
            "total_secret_leaks": sum(1 for r in reviews if r["secret_leak_detected"]),
            "avg_security_score": round(
                sum(r["security_score"] for r in reviews) / max(len(reviews), 1), 1
            ),
        }

    def get_author_stats(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            reviews = list(self._reviews)

        by_author: dict[str, list[dict]] = defaultdict(list)
        for r in reviews:
            if r.get("author"):
                by_author[r["author"]].append(r)

        stats = []
        for author, author_reviews in by_author.items():
            n = len(author_reviews)
            stats.append({
                "author": author,
                "reviews": n,
                "avg_score": round(sum(r["score"] for r in author_reviews) / n, 1),
                "total_issues": sum(r["total_issues"] for r in author_reviews),
                "blocked": sum(1 for r in author_reviews if r["block_merge"]),
            })
        stats.sort(key=lambda x: x["reviews"], reverse=True)
        return stats[:limit]

    def get_recent_reviews(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._reviews)[-limit:]
