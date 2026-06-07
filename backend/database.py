import os
import sqlite3
import threading

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "novel2scenario.db"
)

_local = threading.local()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL DEFAULT 'queued',
    pipeline_stage TEXT NOT NULL DEFAULT 'chapter_splitting',
    novel_text TEXT NOT NULL,
    title TEXT,
    author TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT,
    content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT,
    traits TEXT,
    description TEXT,
    first_appearance INTEGER
);

CREATE TABLE IF NOT EXISTS character_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    related_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    relation TEXT,
    dynamic TEXT
);

CREATE TABLE IF NOT EXISTS scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    heading TEXT,
    setting_json TEXT,
    summary TEXT,
    characters_present TEXT
);

CREATE TABLE IF NOT EXISTS scene_beats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id INTEGER NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    type TEXT NOT NULL,
    speaker TEXT,
    line TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    novel_chapters TEXT
);

CREATE TABLE IF NOT EXISTS episode_scenes (
    episode_id INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
    scene_id INTEGER NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    scene_order INTEGER NOT NULL,
    PRIMARY KEY (episode_id, scene_id)
);

CREATE TABLE IF NOT EXISTS adaptation_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    type TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS stage_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    output_summary TEXT,
    started_at TEXT,
    completed_at TEXT,
    UNIQUE(job_id, stage)
);
"""


def _create_connection(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_db():
    if not hasattr(_local, "connection") or _local.connection is None:
        _local.connection = _create_connection(DB_PATH)
    return _local.connection


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
