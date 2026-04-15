"""
Persistent review storage backed by SQLite.

Stores completed review results and their issues so that the feedback
loop (FeedbackAnalyzer / RuleEvolver) can learn from historical data.
"""

from __future__ import annotations

import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import structlog

from models import ReviewResult

logger = structlog.get_logger()

_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "reviews.db"


class ReviewStore:
    """Thread-safe SQLite store for review results."""

    _instance: Optional[ReviewStore] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[Path] = None) -> ReviewStore:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._db_path = db_path or _DEFAULT_DB_PATH
                inst._db_path.parent.mkdir(parents=True, exist_ok=True)
                inst._local = threading.local()
                inst._init_schema()
                cls._instance = inst
            return cls._instance

    # -- connection helpers ---------------------------------------------------

    @contextmanager
    def _conn(self):
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn = conn
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id   TEXT PRIMARY KEY,
                    repo        TEXT NOT NULL,
                    pr_id       TEXT NOT NULL DEFAULT '',
                    platform    TEXT NOT NULL DEFAULT '',
                    author      TEXT NOT NULL DEFAULT '',
                    score       INTEGER NOT NULL DEFAULT 0,
                    security_score INTEGER NOT NULL DEFAULT 10,
                    block_merge INTEGER NOT NULL DEFAULT 0,
                    approval    INTEGER NOT NULL DEFAULT 1,
                    ai_slop     INTEGER NOT NULL DEFAULT 0,
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS issues (
                    issue_id    TEXT PRIMARY KEY,
                    review_id   TEXT NOT NULL REFERENCES reviews(review_id),
                    severity    TEXT NOT NULL,
                    title       TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    category    TEXT NOT NULL DEFAULT 'general',
                    file_path   TEXT,
                    line_number INTEGER,
                    suggestion  TEXT,
                    owasp_id    TEXT,
                    cwe_id      TEXT,
                    threat_type TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_issues_review ON issues(review_id);
                CREATE INDEX IF NOT EXISTS idx_reviews_repo   ON reviews(repo);
                CREATE INDEX IF NOT EXISTS idx_issues_category ON issues(category);
                """
            )
        logger.info("review_store_initialized", db=str(self._db_path))

    # -- write ----------------------------------------------------------------

    def persist_review(
        self,
        result: ReviewResult,
        *,
        repo: str,
        pr_id: str = "",
        platform: str = "",
        author: str = "",
    ) -> str:
        review_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO reviews
                    (review_id, repo, pr_id, platform, author,
                     score, security_score, block_merge, approval, ai_slop, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    repo,
                    pr_id,
                    platform,
                    author,
                    result.score,
                    result.security_score,
                    int(result.block_merge),
                    int(result.approval_recommended),
                    result.ai_slop_count,
                    now,
                ),
            )

            for issue in result.issues:
                conn.execute(
                    """
                    INSERT INTO issues
                        (issue_id, review_id, severity, title, description,
                         category, file_path, line_number, suggestion,
                         owasp_id, cwe_id, threat_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid.uuid4().hex,
                        review_id,
                        issue.severity.value,
                        issue.title,
                        issue.description,
                        issue.category,
                        issue.file_path,
                        issue.line_number,
                        issue.suggestion,
                        issue.owasp_id,
                        issue.cwe_id,
                        issue.threat_type,
                    ),
                )

        logger.info(
            "review_persisted",
            review_id=review_id,
            repo=repo,
            issues=len(result.issues),
        )
        return review_id

    # -- read -----------------------------------------------------------------

    def get_repo_issues(
        self,
        repo: str,
        *,
        limit: int = 200,
        category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT i.*, r.repo, r.pr_id, r.created_at AS review_ts
            FROM issues i
            JOIN reviews r ON r.review_id = i.review_id
            WHERE r.repo = ?
        """
        params: list[Any] = [repo]
        if category:
            query += " AND i.category = ?"
            params.append(category)
        query += " ORDER BY r.created_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_repo_reviews(
        self, repo: str, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM reviews WHERE repo = ? ORDER BY created_at DESC LIMIT ?",
                (repo, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_repo_review_count(self, repo: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM reviews WHERE repo = ?", (repo,)
            ).fetchone()
        return row["cnt"] if row else 0

    def get_category_frequency(
        self, repo: str, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT i.category, COUNT(*) AS cnt
                FROM issues i
                JOIN reviews r ON r.review_id = i.review_id
                WHERE r.repo = ?
                GROUP BY i.category
                ORDER BY cnt DESC
                LIMIT ?
                """,
                (repo, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_owasp_frequency(
        self, repo: str, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT i.owasp_id, COUNT(*) AS cnt
                FROM issues i
                JOIN reviews r ON r.review_id = i.review_id
                WHERE r.repo = ? AND i.owasp_id IS NOT NULL AND i.owasp_id != ''
                GROUP BY i.owasp_id
                ORDER BY cnt DESC
                LIMIT ?
                """,
                (repo, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_file_pattern_frequency(
        self, repo: str, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT i.file_path, i.category, COUNT(*) AS cnt
                FROM issues i
                JOIN reviews r ON r.review_id = i.review_id
                WHERE r.repo = ? AND i.file_path IS NOT NULL
                GROUP BY i.file_path, i.category
                ORDER BY cnt DESC
                LIMIT ?
                """,
                (repo, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_severity_distribution(self, repo: str) -> dict[str, int]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT i.severity, COUNT(*) AS cnt
                FROM issues i
                JOIN reviews r ON r.review_id = i.review_id
                WHERE r.repo = ?
                GROUP BY i.severity
                """,
                (repo,),
            ).fetchall()
        return {r["severity"]: r["cnt"] for r in rows}

    def get_threat_type_frequency(
        self, repo: str, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT i.threat_type, COUNT(*) AS cnt
                FROM issues i
                JOIN reviews r ON r.review_id = i.review_id
                WHERE r.repo = ? AND i.threat_type IS NOT NULL AND i.threat_type != ''
                GROUP BY i.threat_type
                ORDER BY cnt DESC
                LIMIT ?
                """,
                (repo, limit),
            ).fetchall()
        return [dict(r) for r in rows]
