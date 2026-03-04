from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LiveLogStore:
    """In-memory buffer for active PR review runs and their events."""

    def __init__(self, max_events_per_run: int = 200):
        self.max_events_per_run = max(1, int(max_events_per_run))
        self._lock = Lock()
        self._runs: dict[str, dict[str, Any]] = {}
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._next_seq: dict[str, int] = {}

    def start_run(
        self,
        *,
        platform: str,
        pr_id: str,
        title: str,
        author: str,
        source_branch: str | None = None,
        target_branch: str | None = None,
        repo: str | None = None,
    ) -> str:
        with self._lock:
            run_id = str(uuid4())
            now = _utc_now_iso()
            self._runs[run_id] = {
                "run_id": run_id,
                "platform": platform,
                "pr_id": pr_id,
                "title": title,
                "author": author,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "repo": repo,
                "started_at": now,
                "updated_at": now,
                "status": "active",
                "score": None,
                "issues": None,
                "critical": None,
                "error": None,
            }
            self._events[run_id] = []
            self._next_seq[run_id] = 1
            return run_id

    def append_event(
        self,
        run_id: str,
        *,
        step: str,
        message: str,
        level: str = "info",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                raise KeyError(f"run not found: {run_id}")

            seq = self._next_seq[run_id]
            self._next_seq[run_id] = seq + 1

            event = {
                "seq": seq,
                "ts": _utc_now_iso(),
                "level": level,
                "step": step,
                "message": message,
                "meta": meta or {},
            }

            events = self._events[run_id]
            events.append(event)
            if len(events) > self.max_events_per_run:
                # Keep the most recent events only.
                self._events[run_id] = events[-self.max_events_per_run :]

            run["updated_at"] = event["ts"]
            return event

    def complete_run(self, run_id: str, *, score: int, issues: int, critical: int) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                raise KeyError(f"run not found: {run_id}")
            run["status"] = "completed"
            run["score"] = score
            run["issues"] = issues
            run["critical"] = critical
            run["updated_at"] = _utc_now_iso()

    def fail_run(self, run_id: str, *, error: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                raise KeyError(f"run not found: {run_id}")
            run["status"] = "error"
            run["error"] = error
            run["updated_at"] = _utc_now_iso()

    def list_active_runs(self) -> list[dict[str, Any]]:
        with self._lock:
            active = [r.copy() for r in self._runs.values() if r.get("status") == "active"]
            active.sort(key=lambda x: x["updated_at"], reverse=True)
            return active

    def list_runs(self) -> list[dict[str, Any]]:
        with self._lock:
            items = [r.copy() for r in self._runs.values()]
            items.sort(key=lambda x: x["updated_at"], reverse=True)
            return items

    def set_max_events_per_run(self, value: int) -> None:
        with self._lock:
            self.max_events_per_run = max(1, int(value))
            for run_id, events in self._events.items():
                if len(events) > self.max_events_per_run:
                    self._events[run_id] = events[-self.max_events_per_run :]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            run = self._runs.get(run_id)
            return run.copy() if run else None

    def get_events_since(
        self,
        run_id: str,
        *,
        cursor: int = 0,
        limit: int = 200,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                raise KeyError(f"run not found: {run_id}")

            effective_limit = max(1, min(int(limit), 1000))
            events = self._events.get(run_id, [])
            filtered = [e for e in events if int(e["seq"]) > int(cursor)]
            chunk = filtered[:effective_limit]
            next_cursor = int(chunk[-1]["seq"]) if chunk else int(cursor)
            return run.copy(), [e.copy() for e in chunk], next_cursor
