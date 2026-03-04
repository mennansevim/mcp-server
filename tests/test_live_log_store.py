import importlib.util
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "services" / "live_log_store.py"
    spec = importlib.util.spec_from_file_location("live_log_store", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load live_log_store module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_start_run_and_append_event():
    LiveLogStore = _load_module().LiveLogStore

    store = LiveLogStore(max_events_per_run=10)
    run_id = store.start_run(
        platform="github",
        pr_id="142",
        title="feat: auth",
        author="mehmet",
        source_branch="feature/auth",
        target_branch="main",
    )
    store.append_event(run_id, step="step_1", message="Fetching diff")

    summary, events, next_cursor = store.get_events_since(run_id, cursor=0, limit=50)
    assert summary["pr_id"] == "142"
    assert summary["status"] == "active"
    assert len(events) == 1
    assert events[0]["message"] == "Fetching diff"
    assert next_cursor == 1


def test_complete_run_is_not_listed_as_active():
    LiveLogStore = _load_module().LiveLogStore

    store = LiveLogStore(max_events_per_run=2)
    run_id = store.start_run(platform="github", pr_id="1", title="t", author="u")
    store.append_event(run_id, step="step_1", message="Start")
    store.append_event(run_id, step="step_2", message="Analyze")
    store.append_event(run_id, step="step_3", message="Review")
    store.complete_run(run_id, score=7, issues=5, critical=0)

    active_runs = store.list_active_runs()
    assert active_runs == []

    summary, events, next_cursor = store.get_events_since(run_id, cursor=0, limit=50)
    assert summary["status"] == "completed"
    assert summary["score"] == 7
    assert len(events) == 2
    assert [e["message"] for e in events] == ["Analyze", "Review"]
    assert next_cursor == 3


def test_list_runs_returns_all_statuses():
    LiveLogStore = _load_module().LiveLogStore

    store = LiveLogStore(max_events_per_run=10)
    active_id = store.start_run(platform="github", pr_id="11", title="active", author="u1")
    completed_id = store.start_run(platform="github", pr_id="12", title="completed", author="u2")
    error_id = store.start_run(platform="github", pr_id="13", title="error", author="u3")

    store.complete_run(completed_id, score=9, issues=1, critical=0)
    store.fail_run(error_id, error="fetch failed")

    runs = store.list_runs()
    run_ids = {run["run_id"] for run in runs}
    assert run_ids == {active_id, completed_id, error_id}
    statuses = {run["run_id"]: run["status"] for run in runs}
    assert statuses[active_id] == "active"
    assert statuses[completed_id] == "completed"
    assert statuses[error_id] == "error"
