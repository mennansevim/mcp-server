from pathlib import Path

from fastapi.testclient import TestClient

from server import app


def test_ui_route_serves_index_when_dist_exists():
    client = TestClient(app)

    dist_index = Path('ui/dist/index.html')
    if not dist_index.exists():
        # If UI is not built in this environment, skip strict assertion.
        resp = client.get('/ui')
        assert resp.status_code in (200, 404)
        return

    resp = client.get('/ui')
    assert resp.status_code == 200
    assert 'text/html' in resp.headers.get('content-type', '')
