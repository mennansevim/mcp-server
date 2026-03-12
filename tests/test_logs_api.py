from fastapi.testclient import TestClient

from server import app, review_server


def test_get_logs_config():
    client = TestClient(app)
    resp = client.get("/api/logs/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "poll_interval_seconds" in data
    assert "max_events_per_poll" in data
    assert data["poll_interval_seconds"] >= 1


def test_get_active_runs_and_incremental_events():
    client = TestClient(app)

    run_id = review_server.live_logs.start_run(
        platform="github",
        pr_id="314",
        title="feat: dashboard logs",
        author="mehmet",
        source_branch="feature/ui-logs",
        target_branch="main",
        repo="acme/backend-api",
    )
    review_server.live_logs.append_event(run_id, step="step_1", message="Fetching diff")

    active_resp = client.get("/api/logs/active")
    assert active_resp.status_code == 200
    active_data = active_resp.json()
    assert active_data["count"] >= 1
    assert any(r["run_id"] == run_id for r in active_data["runs"])

    events_resp = client.get(
        f"/api/logs/active/{run_id}/events",
        params={"cursor": 0, "limit": 50},
    )
    assert events_resp.status_code == 200
    events_data = events_resp.json()
    assert events_data["run"]["run_id"] == run_id
    assert len(events_data["events"]) == 1
    assert events_data["events"][0]["message"] == "Fetching diff"
    assert events_data["next_cursor"] == 1


def test_get_events_not_found_returns_404():
    client = TestClient(app)
    resp = client.get("/api/logs/active/not-found/events")
    assert resp.status_code == 404


def test_get_all_runs_includes_completed_and_error():
    client = TestClient(app)

    active_id = review_server.live_logs.start_run(
        platform="github",
        pr_id="901",
        title="feat: active",
        author="alice",
    )
    completed_id = review_server.live_logs.start_run(
        platform="github",
        pr_id="902",
        title="feat: completed",
        author="bob",
    )
    error_id = review_server.live_logs.start_run(
        platform="github",
        pr_id="903",
        title="feat: error",
        author="charlie",
    )
    review_server.live_logs.complete_run(completed_id, score=8, issues=2, critical=0)
    review_server.live_logs.fail_run(error_id, error="failed to fetch diff")

    resp = client.get("/api/logs/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 3
    by_id = {item["run_id"]: item for item in data["runs"]}
    assert by_id[active_id]["status"] == "active"
    assert by_id[completed_id]["status"] == "completed"
    assert by_id[error_id]["status"] == "error"
