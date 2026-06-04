import pytest
from backend.database import get_db, init_db


@pytest.fixture
def test_db():
    import backend.database as db_mod

    db_mod.DB_PATH = ":memory:"
    init_db()
    yield


def test_init_db_creates_tables(test_db):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    expected = [
        "adaptation_notes",
        "chapters",
        "character_relationships",
        "characters",
        "episode_scenes",
        "episodes",
        "jobs",
        "scene_beats",
        "scenes",
    ]
    assert tables == expected
