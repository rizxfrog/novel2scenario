import os
import tempfile
import threading
import pytest
import yaml
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db


@pytest.fixture(autouse=True)
def setup():
    import backend.database as db
    db_fd, db_file = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    db.DB_PATH = db_file
    db._local = threading.local()
    init_db()
    yield
    if hasattr(db._local, "connection") and db._local.connection:
        db._local.connection.close()
        db._local.connection = None
    try:
        os.unlink(db_file)
    except (PermissionError, FileNotFoundError):
        pass


@pytest.fixture
def client():
    return TestClient(app)


SAMPLE_NOVEL = """第一章 故事的开始

清晨的阳光透过窗帘洒进房间。李明睁开惺忪的睡眼。

第二章 命运的选择

李明站在十字路口，左右张望。

第三章 转折

一场突如其来的大雨打乱了所有计划。"""


def test_create_job_and_get_status(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL, "title": "Test"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == 1
    assert data["status"] == "queued"

    resp = client.get(f"/api/jobs/{data['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test"


def test_advance_through_chapter_splitting(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    # Advance to chapter splitting (should work without LLM due to regex)
    resp = client.post(f"/api/jobs/{job_id}/continue")
    assert resp.status_code == 200
    assert resp.json()["pipeline_stage"] == "chapter_splitting"
    assert resp.json()["status"] == "awaiting_review"

    # Verify chapters stored
    from backend.database import get_db
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM chapters WHERE job_id = ?", (job_id,)).fetchone()[0]
    assert count == 3


def test_character_routes(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    # Characters should be empty before extraction
    resp = client.get(f"/api/jobs/{job_id}/characters")
    assert resp.status_code == 200
    assert resp.json() == []


def test_scene_routes(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    resp = client.get(f"/api/jobs/{job_id}/scenes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_episode_routes(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    resp = client.get(f"/api/jobs/{job_id}/episodes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_script_route_default_json(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    resp = client.get(f"/api/jobs/{job_id}/script")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    data = resp.json()
    assert "meta" in data
    assert "dramatis_personae" in data
    assert "episodes" in data
    assert "adaptation_notes" in data


def test_script_route_format_json(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    resp = client.get(f"/api/jobs/{job_id}/script?format=json")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert "meta" in resp.json()


def test_script_route_format_yaml(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    resp = client.get(f"/api/jobs/{job_id}/script?format=yaml")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/x-yaml"

    # Verify valid YAML with expected top-level keys
    data = yaml.safe_load(resp.text)
    assert isinstance(data, dict)
    assert "meta" in data
    assert "dramatis_personae" in data
    assert "episodes" in data
    assert "adaptation_notes" in data
    # Verify meta fields
    assert "title" in data["meta"]
    assert "total_episodes" in data["meta"]
    assert "total_chapters_in_novel" in data["meta"]


def test_script_route_invalid_format(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    resp = client.get(f"/api/jobs/{job_id}/script?format=xml")
    assert resp.status_code == 422  # FastAPI validation error


def test_job_not_found(client):
    resp = client.get("/api/jobs/999")
    assert resp.status_code == 404


def test_contribute_completed_job(client):
    resp = client.post("/api/jobs", json={"novel_text": SAMPLE_NOVEL})
    job_id = resp.json()["id"]

    # Manually set to completed
    from backend.database import get_db
    db = get_db()
    db.execute("UPDATE jobs SET status = 'completed', pipeline_stage = 'completed' WHERE id = ?", (job_id,))
    db.commit()

    resp = client.post(f"/api/jobs/{job_id}/continue")
    assert resp.status_code == 400  # Cannot continue completed job
