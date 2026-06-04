# tests/test_integration.py
import tempfile
import threading
import pytest
import os


@pytest.fixture(autouse=True)
def setup():
    import backend.database as db
    db.DB_PATH = ":memory:"
    db._local = threading.local()
    db.init_db()


def test_full_pipeline_smoke():
    """Test the pipeline structure with regex-based chapter splitting (no LLM)."""
    from backend.pipeline.orchestrator import create_job, get_job, advance_pipeline
    from backend.database import get_db
    import asyncio

    # Create job
    novel = "第一章 开始\n\n故事开始于一个清晨。\n\n第二章 发展\n\n故事不断发展。\n\n第三章 结局\n\n故事完美收官。"
    job = create_job(novel_text=novel, title="Test Novel")
    assert job["id"] == 1
    assert job["status"] == "queued"
    assert job["pipeline_stage"] == "chapter_splitting"

    # Advance through chapter splitting (regex-based, no LLM needed)
    updated = asyncio.run(advance_pipeline(job["id"]))
    assert updated["pipeline_stage"] == "chapter_splitting"
    assert updated["status"] == "awaiting_review"

    # Verify chapters were stored
    db = get_db()
    chapters = db.execute("SELECT * FROM chapters WHERE job_id = ? ORDER BY number", (job["id"],)).fetchall()
    assert len(chapters) == 3
    assert chapters[0]["number"] == 1


def test_api_client_structure():
    """Test that the FastAPI app can be created and routes are registered."""
    import backend.database as db

    # Use a temp file to avoid :memory: thread isolation issues
    db_fd, db_file = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)  # Close the fd so SQLite can use the file

    try:
        db.DB_PATH = db_file
        db._local = threading.local()
        db.init_db()

        from fastapi.testclient import TestClient
        from backend.main import app

        # Override the startup event to re-init with correct DB path
        client = TestClient(app)

        # Create a job via the API
        novel = "第一章 开始\n\n故事开始于一个清晨。\n\n第二章 发展\n\n故事不断发展。\n\n第三章 结局\n\n故事完美收官。"
        resp = client.post("/api/jobs", json={"novel_text": novel, "title": "Test Novel"})
        assert resp.status_code == 201
        job_id = resp.json()["id"]

        # Advance through chapter splitting
        resp = client.post(f"/api/jobs/{job_id}/continue")
        assert resp.status_code == 200
        assert resp.json()["pipeline_stage"] == "chapter_splitting"
        assert resp.json()["status"] == "awaiting_review"

        # Check chapters stored
        db_conn = db.get_db()
        chapters = db_conn.execute("SELECT COUNT(*) FROM chapters WHERE job_id = ?", (job_id,)).fetchone()[0]
        assert chapters == 3
    finally:
        # Close all DB connections before cleanup
        import backend.database as db_mod
        if hasattr(db_mod._local, 'connection') and db_mod._local.connection:
            db_mod._local.connection.close()
            db_mod._local.connection = None
        try:
            os.unlink(db_file)
        except PermissionError:
            pass  # File may still be locked on Windows, cleanup on next run
