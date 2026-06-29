import pytest
from fastapi.testclient import TestClient

from vera.api.main import app


@pytest.mark.lab
def test_list_triggers():
    client = TestClient(app)
    r = client.get("/api/v1/lab/triggers")
    assert r.status_code == 200
    assert len(r.json()["triggers"]) >= 5
