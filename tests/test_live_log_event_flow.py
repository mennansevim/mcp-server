from types import SimpleNamespace

from server import CodeReviewServer


def _mock_pr_data():
    return SimpleNamespace(
        platform=SimpleNamespace(value="github"),
        pr_id="42",
        title="feat: auth middleware",
        author="mehmet",
        source_branch="feature/auth",
        target_branch="main",
        repo_full_name="acme/backend-api",
    )


def test_live_log_lifecycle_hooks_complete_run():
    review_server = CodeReviewServer()
    pr_data = _mock_pr_data()

    run_id = review_server._start_live_run(pr_data)
    assert run_id

    review_server._emit_live_event(run_id, step="step_1", message="Fetching diff")
    review_server._emit_live_event(run_id, step="step_2", message="Analyzing diff")
    review_server._complete_live_run(run_id, score=7, issues=5, critical=0)

    assert review_server.live_logs.list_active_runs() == []

    summary, events, next_cursor = review_server.live_logs.get_events_since(run_id, cursor=0, limit=100)
    assert summary["status"] == "completed"
    assert summary["score"] == 7
    assert len(events) == 2
    assert events[0]["message"] == "Fetching diff"
    assert events[1]["message"] == "Analyzing diff"
    assert next_cursor == 2


def test_live_log_lifecycle_hooks_fail_run():
    review_server = CodeReviewServer()
    pr_data = _mock_pr_data()

    run_id = review_server._start_live_run(pr_data)
    review_server._emit_live_event(run_id, step="step_1", message="Fetching diff")
    review_server._fail_live_run(run_id, error="Failed to fetch diff")

    assert review_server.live_logs.list_active_runs() == []

    summary, events, next_cursor = review_server.live_logs.get_events_since(run_id, cursor=0, limit=100)
    assert summary["status"] == "error"
    assert summary["error"] == "Failed to fetch diff"
    assert len(events) == 1
    assert next_cursor == 1
