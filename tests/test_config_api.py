from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture(autouse=True)
def use_temp_overrides_file(tmp_path: Path):
    old = server.CONFIG_OVERRIDES_PATH
    server.CONFIG_OVERRIDES_PATH = tmp_path / "config.overrides.yaml"
    try:
        yield
    finally:
        server.CONFIG_OVERRIDES_PATH = old


def test_get_config_returns_editable_fields():
    client = TestClient(server.app)
    resp = client.get('/api/config')
    assert resp.status_code == 200

    data = resp.json()
    assert 'ui' in data
    assert 'review' in data
    assert 'ai' in data
    assert 'logs' in data['ui']
    assert 'poll_interval_seconds' in data['ui']['logs']
    assert 'max_events_per_poll' in data['ui']['logs']
    assert 'comment_strategy' in data['review']
    assert 'focus' in data['review']
    assert 'provider' in data['ai']
    assert 'model' in data['ai']


def test_put_config_updates_runtime_values():
    client = TestClient(server.app)
    original = client.get('/api/config').json()

    payload = {
        'ui': {'logs': {'poll_interval_seconds': 5, 'max_events_per_poll': 240}},
        'review': {'comment_strategy': 'both', 'focus': ['security', 'bugs']},
        'ai': {'provider': 'openai', 'model': 'gpt-4o'}
    }

    try:
        update_resp = client.put('/api/config', json=payload)
        assert update_resp.status_code == 200
        updated = update_resp.json()

        assert updated['ui']['logs']['poll_interval_seconds'] == 5
        assert updated['ui']['logs']['max_events_per_poll'] == 240
        assert updated['review']['comment_strategy'] == 'both'
        assert updated['review']['focus'] == ['security', 'bugs']
        assert updated['ai']['provider'] == 'openai'
        assert updated['ai']['model'] == 'gpt-4o'

        logs_cfg = client.get('/api/logs/config').json()
        assert logs_cfg['poll_interval_seconds'] == 5
        assert logs_cfg['max_events_per_poll'] == 240

        persisted = server._read_yaml_file(server.CONFIG_OVERRIDES_PATH)
        assert persisted['ui']['logs']['poll_interval_seconds'] == 5
        assert persisted['ui']['logs']['max_events_per_poll'] == 240
        assert persisted['review']['comment_strategy'] == 'both'
        assert persisted['review']['focus'] == ['security', 'bugs']
        assert persisted['ai']['provider'] == 'openai'
        assert persisted['ai']['model'] == 'gpt-4o'
    finally:
        client.put('/api/config', json=original)


def test_put_config_rejects_invalid_comment_strategy():
    client = TestClient(server.app)
    bad_payload = {
        'review': {'comment_strategy': 'invalid-strategy'}
    }

    resp = client.put('/api/config', json=bad_payload)
    assert resp.status_code == 400


def test_put_config_rejects_invalid_ai_model_for_provider():
    client = TestClient(server.app)
    bad_payload = {
        'ai': {'provider': 'openai', 'model': 'llama-3.3-70b-versatile'}
    }

    resp = client.put('/api/config', json=bad_payload)
    assert resp.status_code == 400
