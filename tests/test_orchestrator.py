import pytest
from backend.database import get_db, init_db
from backend.pipeline.orchestrator import create_job, get_job, advance_pipeline


@pytest.fixture(autouse=True)
def setup_db():
    import backend.database as db_mod
    db_mod.DB_PATH = ":memory:"
    init_db()


@pytest.mark.asyncio
async def test_create_job():
    job = create_job(novel_text="第一章 开始\n\n故事开始了\n\n第二章 结束\n\n故事结束了")
    assert job["id"] == 1
    assert job["status"] == "queued"
    assert job["pipeline_stage"] == "chapter_splitting"


@pytest.mark.asyncio
async def test_advance_through_splitting():
    job = create_job(novel_text="第一章 测试\n\n测试内容\n\n第二章 更多\n\n更多内容\n\n第三章 终章\n\n结束了")
    result = await advance_pipeline(job["id"])
    assert result["pipeline_stage"] == "chapter_splitting"
    assert result["status"] == "awaiting_review"
    db = get_db()
    chapters = db.execute("SELECT COUNT(*) FROM chapters WHERE job_id = ?", (job["id"],)).fetchone()[0]
    assert chapters == 3
