from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, cast

from backend.database import get_db
from backend.pipeline.splitter import split_chapters
from backend.pipeline.characters import extract_characters
from backend.pipeline.scenes import analyze_scenes
from backend.pipeline.episodes import structure_episodes
from backend.pipeline.assembler import assemble_script

logger = logging.getLogger(__name__)

STAGES = [
    "chapter_splitting", "character_extraction", "scene_analysis",
    "episode_structuring", "script_assembly",
]

NEXT_STAGE = {
    "chapter_splitting": "character_extraction",
    "character_extraction": "scene_analysis",
    "scene_analysis": "episode_structuring",
    "episode_structuring": "script_assembly",
    "script_assembly": "completed",
}


def create_job(novel_text: str, title: str | None = None, author: str | None = None) -> dict:
    db = get_db()
    cursor = db.execute(
        "INSERT INTO jobs (novel_text, title, author) VALUES (?, ?, ?)",
        (novel_text, title, author),
    )
    db.commit()
    init_stage_statuses(cursor.lastrowid)
    return get_job(cursor.lastrowid)


def get_job(job_id: int) -> dict:
    db = get_db()
    row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise ValueError(f"Job {job_id} not found")
    return dict(row)


def list_jobs(search: str | None = None, status_filter: str | None = None) -> list[dict[str, Any]]:
    db = get_db()
    query = "SELECT * FROM jobs"
    params: list[Any] = []
    conditions: list[str] = []

    if search:
        conditions.append("(title LIKE ? OR author LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if status_filter:
        conditions.append("status = ?")
        params.append(status_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY updated_at DESC"

    rows = db.execute(query, tuple(params)).fetchall()
    return [dict(r) for r in rows]


def delete_job(job_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    db.commit()


def update_job_status(job_id: int, status: str, stage: str | None = None):
    db = get_db()
    if stage:
        db.execute(
            "UPDATE jobs SET status = ?, pipeline_stage = ?, updated_at = datetime('now') WHERE id = ?",
            (status, stage, job_id),
        )
    else:
        db.execute(
            "UPDATE jobs SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, job_id),
        )
    db.commit()


def init_stage_statuses(job_id: int) -> None:
    db = get_db()
    for stage in STAGES:
        db.execute(
            "INSERT OR IGNORE INTO stage_status (job_id, stage) VALUES (?, ?)",
            (job_id, stage),
        )
    db.commit()


def get_stage_statuses(job_id: int) -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM stage_status WHERE job_id = ? ORDER BY id",
        (job_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_stage_status(
    job_id: int,
    stage: str,
    status: str,
    error_message: str | None = None,
    output_summary: str | None = None,
) -> None:
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    if status == "running":
        db.execute(
            "UPDATE stage_status SET status = ?, started_at = ?, error_message = NULL WHERE job_id = ? AND stage = ?",
            (status, now, job_id, stage),
        )
    elif status in ("completed", "awaiting_review", "failed"):
        db.execute(
            "UPDATE stage_status SET status = ?, completed_at = ?, output_summary = ?, error_message = ? WHERE job_id = ? AND stage = ?",
            (status, now, output_summary, error_message, job_id, stage),
        )
    else:
        db.execute(
            "UPDATE stage_status SET status = ? WHERE job_id = ? AND stage = ?",
            (status, job_id, stage),
        )
    db.commit()


async def _run_chapter_splitting(job_id: int, novel_text: str) -> None:
    chapters = await split_chapters(novel_text)
    db = get_db()
    for ch in chapters:
        db.execute(
            "INSERT INTO chapters (job_id, number, title, content) VALUES (?, ?, ?, ?)",
            (job_id, ch["number"], ch.get("title", ""), ch.get("content", "")),
        )
    db.commit()


async def _run_character_extraction(job_id: int) -> None:
    db = get_db()
    chapters = [dict(r) for r in db.execute(
        "SELECT * FROM chapters WHERE job_id = ? ORDER BY number", (job_id,)
    ).fetchall()]
    characters = await extract_characters(chapters)
    for ch in characters:
        db.execute(
            "INSERT INTO characters (job_id, name, role, traits, description, first_appearance) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, ch["name"], ch.get("role"), json.dumps(ch.get("traits", [])),
             ch.get("description"), ch.get("first_appearance")),
        )
    db.commit()


async def _run_scene_analysis(job_id: int) -> None:
    db = get_db()
    chapters_raw = db.execute(
        "SELECT * FROM chapters WHERE job_id = ? ORDER BY number", (job_id,)
    ).fetchall()
    chapters = [dict(r) for r in chapters_raw]

    scenes = await analyze_scenes(chapters)

    db.execute("DELETE FROM scene_beats WHERE scene_id IN (SELECT id FROM scenes WHERE job_id = ?)", (job_id,))
    db.execute("DELETE FROM scenes WHERE job_id = ?", (job_id,))

    for global_num, scene in enumerate(scenes, 1):
        cursor = db.execute(
            "INSERT INTO scenes (job_id, chapter_id, number, heading, setting_json, summary, characters_present) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, 1, global_num, scene.get("heading"),
             json.dumps(scene.get("setting", {})), scene.get("summary"),
             json.dumps(scene.get("characters_present", []))),
        )
        scene_id = cursor.lastrowid
        for beat_num, beat in enumerate(scene.get("beats", []), 1):
            db.execute(
                "INSERT INTO scene_beats (scene_id, number, type, speaker, line, description) VALUES (?, ?, ?, ?, ?, ?)",
                (scene_id, beat_num, beat.get("type"), beat.get("speaker"),
                 beat.get("line"), beat.get("description")),
            )
    db.commit()


async def _run_episode_structuring(job_id: int) -> None:
    db = get_db()
    characters = cast(list[dict[str, Any]], [dict(r) for r in db.execute(
        "SELECT * FROM characters WHERE job_id = ?", (job_id,)
    ).fetchall()])
    scenes = cast(list[dict[str, Any]], [dict(r) for r in db.execute(
        "SELECT * FROM scenes WHERE job_id = ? ORDER BY id", (job_id,)
    ).fetchall()])

    episodes = await structure_episodes(characters, scenes)

    for ep in episodes:
        cursor = db.execute(
            "INSERT INTO episodes (job_id, number, title, summary, novel_chapters) VALUES (?, ?, ?, ?, ?)",
            (job_id, ep["number"], ep.get("title"), ep.get("summary"),
             json.dumps(ep.get("novel_chapters", []))),
        )
        ep_id = cursor.lastrowid
        for order, sid in enumerate(ep.get("scene_ids", []), 1):
            db.execute(
                "INSERT INTO episode_scenes (episode_id, scene_id, scene_order) VALUES (?, ?, ?)",
                (ep_id, sid, order),
            )
    db.commit()


async def _run_script_assembly(job_id: int) -> None:
    db = get_db()
    characters = [dict(r) for r in db.execute(
        "SELECT * FROM characters WHERE job_id = ?", (job_id,)
    ).fetchall()]
    episodes = [dict(r) for r in db.execute(
        "SELECT * FROM episodes WHERE job_id = ? ORDER BY number", (job_id,)
    ).fetchall()]
    scenes = [dict(r) for r in db.execute(
        "SELECT * FROM scenes WHERE job_id = ? ORDER BY id", (job_id,)
    ).fetchall()]

    for sc in scenes:
        beats = [dict(r) for r in db.execute(
            "SELECT * FROM scene_beats WHERE scene_id = ? ORDER BY number", (sc["id"],)
        ).fetchall()]
        sc["beats"] = [{"id": b["id"], "number": b["number"], "type": b["type"],
                        "speaker": b["speaker"], "line": b["line"],
                        "description": b["description"]} for b in beats]

    job = get_job(job_id)
    chapter_count = db.execute(
        "SELECT COUNT(*) FROM chapters WHERE job_id = ?", (job_id,)
    ).fetchone()[0]

    meta = {"title": job.get("title", ""), "author": job.get("author"),
            "total_chapters_in_novel": chapter_count}

    script = await assemble_script(meta, characters, episodes, scenes)

    for note in script.get("adaptation_notes", []):
        db.execute(
            "INSERT INTO adaptation_notes (job_id, type, description) VALUES (?, ?, ?)",
            (job_id, note.get("type"), note.get("description")),
        )
    db.commit()


STAGE_RUNNERS = {
    "chapter_splitting": _run_chapter_splitting,
    "character_extraction": _run_character_extraction,
    "scene_analysis": _run_scene_analysis,
    "episode_structuring": _run_episode_structuring,
    "script_assembly": _run_script_assembly,
}


async def advance_pipeline(job_id: int) -> dict[str, Any]:
    job = get_job(job_id)
    current_stage = job["pipeline_stage"]

    if current_stage == "completed":
        raise ValueError("Job is already completed")

    if job["status"] == "awaiting_review":
        next_stage = NEXT_STAGE.get(current_stage)
        if next_stage == "completed":
            update_job_status(job_id, "completed", "completed")
            update_stage_status(job_id, "completed", "completed")
            return get_job(job_id)
        update_job_status(job_id, "running", next_stage)
        update_stage_status(job_id, next_stage, "running")
        runner = STAGE_RUNNERS.get(next_stage)
        if runner:
            try:
                await runner(job_id)
            except Exception as e:
                logger.error(f"Pipeline stage {next_stage} failed: {e}")
                update_job_status(job_id, "failed", next_stage)
                update_stage_status(job_id, next_stage, "failed", error_message=str(e))
                raise
        output_summary = None
        if next_stage == "character_extraction":
            count = get_db().execute(
                "SELECT COUNT(*) FROM characters WHERE job_id = ?", (job_id,)
            ).fetchone()[0]
            output_summary = f"{count} 个角色"
        if next_stage == "completed":
            update_job_status(job_id, "completed", "completed")
            update_stage_status(job_id, "completed", "completed")
        else:
            update_job_status(job_id, "awaiting_review", next_stage)
            update_stage_status(job_id, next_stage, "awaiting_review", output_summary=output_summary)
        return get_job(job_id)

    if job["status"] == "queued":
        update_job_status(job_id, "running", "chapter_splitting")
        update_stage_status(job_id, "chapter_splitting", "running")
        try:
            await _run_chapter_splitting(job_id, job["novel_text"])
        except Exception as e:
            logger.error(f"Pipeline stage chapter_splitting failed: {e}")
            update_job_status(job_id, "failed", "chapter_splitting")
            update_stage_status(job_id, "chapter_splitting", "failed", error_message=str(e))
            raise
        chapter_count = get_db().execute(
            "SELECT COUNT(*) FROM chapters WHERE job_id = ?", (job_id,)
        ).fetchone()[0]
        update_stage_status(job_id, "chapter_splitting", "awaiting_review", output_summary=f"{chapter_count} 章")
        update_job_status(job_id, "awaiting_review", "chapter_splitting")
        return get_job(job_id)

    raise ValueError(f"Unexpected job state: status={job['status']}, stage={current_stage}")


def _cleanup_downstream(job_id: int, from_stage: str) -> None:
    db = get_db()
    stage_order = {
        "chapter_splitting": 0, "character_extraction": 1,
        "scene_analysis": 2, "episode_structuring": 3, "script_assembly": 4,
    }
    cutoff = stage_order[from_stage]

    if cutoff <= 1:
        db.execute("DELETE FROM characters WHERE job_id = ?", (job_id,))
    if cutoff <= 2:
        scene_ids = [r[0] for r in db.execute(
            "SELECT id FROM scenes WHERE job_id = ?", (job_id,)
        ).fetchall()]
        for sid in scene_ids:
            db.execute("DELETE FROM scene_beats WHERE scene_id = ?", (sid,))
        db.execute("DELETE FROM scenes WHERE job_id = ?", (job_id,))
    if cutoff <= 3:
        ep_ids = [r[0] for r in db.execute(
            "SELECT id FROM episodes WHERE job_id = ?", (job_id,)
        ).fetchall()]
        for eid in ep_ids:
            db.execute("DELETE FROM episode_scenes WHERE episode_id = ?", (eid,))
        db.execute("DELETE FROM episodes WHERE job_id = ?", (job_id,))
    if cutoff <= 4:
        db.execute("DELETE FROM adaptation_notes WHERE job_id = ?", (job_id,))
    db.commit()


async def retry_pipeline(job_id: int, from_stage: str, rerun_stages: list[str]) -> dict[str, Any]:
    _cleanup_downstream(job_id, from_stage)

    all_affected = [from_stage] + rerun_stages
    stage_order = {s: i for i, s in enumerate(STAGES)}
    ordered = sorted(all_affected, key=lambda s: stage_order.get(s, 99))

    for stage in ordered:
        update_stage_status(job_id, stage, "pending")

    update_job_status(job_id, "running", from_stage)
    update_stage_status(job_id, from_stage, "running")

    runner = STAGE_RUNNERS.get(from_stage)
    if not runner:
        raise ValueError(f"Unknown stage: {from_stage}")
    await runner(job_id)

    update_stage_status(job_id, from_stage, "awaiting_review")
    update_job_status(job_id, "awaiting_review", from_stage)

    return get_job(job_id)


# ---- Data access helpers ----

def get_chapters(job_id: int) -> list[dict]:
    db = get_db()
    chapters = [dict(r) for r in db.execute(
        "SELECT id, job_id, number, title, content FROM chapters WHERE job_id = ? ORDER BY number",
        (job_id,),
    ).fetchall()]
    return chapters


def get_characters(job_id: int) -> list[dict]:
    db = get_db()
    chars = [dict(r) for r in db.execute(
        "SELECT * FROM characters WHERE job_id = ? ORDER BY id", (job_id,)
    ).fetchall()]
    for ch in chars:
        ch["traits"] = json.loads(ch.get("traits", "[]"))
    return chars


def update_characters(job_id: int, characters: list[dict]) -> None:
    db = get_db()
    db.execute("DELETE FROM characters WHERE job_id = ?", (job_id,))
    for ch in characters:
        db.execute(
            "INSERT INTO characters (job_id, name, role, traits, description, first_appearance) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, ch["name"], ch.get("role"), json.dumps(ch.get("traits", [])),
             ch.get("description"), ch.get("first_appearance")),
        )
    db.commit()


def get_scenes(job_id: int) -> list[dict]:
    db = get_db()
    scenes = [dict(r) for r in db.execute(
        "SELECT s.*, c.title as chapter_title FROM scenes s LEFT JOIN chapters c ON s.chapter_id = c.id WHERE s.job_id = ? ORDER BY s.id", (job_id,)
    ).fetchall()]
    for sc in scenes:
        sc["setting"] = json.loads(sc.get("setting_json", "{}"))
        sc["characters_present"] = json.loads(sc.get("characters_present", "[]"))
        beats = [dict(r) for r in db.execute(
            "SELECT * FROM scene_beats WHERE scene_id = ? ORDER BY number", (sc["id"],)
        ).fetchall()]
        sc["beats"] = beats
    return scenes


def update_scenes(job_id: int, scenes: list[dict]) -> None:
    db = get_db()
    scene_ids = [r[0] for r in db.execute("SELECT id FROM scenes WHERE job_id = ?", (job_id,)).fetchall()]
    for sid in scene_ids:
        db.execute("DELETE FROM scene_beats WHERE scene_id = ?", (sid,))
    db.execute("DELETE FROM scenes WHERE job_id = ?", (job_id,))
    for sc in scenes:
        cursor = db.execute(
            "INSERT INTO scenes (job_id, chapter_id, number, heading, setting_json, summary, characters_present) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, sc.get("chapter_id", 1), sc.get("number", 1), sc.get("heading"),
             json.dumps(sc.get("setting", {})), sc.get("summary"),
             json.dumps(sc.get("characters_present", []))),
        )
        sid = cursor.lastrowid
        for beat in sc.get("beats", []):
            db.execute(
                "INSERT INTO scene_beats (scene_id, number, type, speaker, line, description) VALUES (?, ?, ?, ?, ?, ?)",
                (sid, beat.get("number", 1), beat.get("type"), beat.get("speaker"),
                 beat.get("line"), beat.get("description")),
            )
    db.commit()


def get_episodes(job_id: int) -> list[dict]:
    db = get_db()
    episodes = [dict(r) for r in db.execute(
        "SELECT * FROM episodes WHERE job_id = ? ORDER BY number", (job_id,)
    ).fetchall()]
    for ep in episodes:
        ep["novel_chapters"] = json.loads(ep.get("novel_chapters", "[]"))
        scene_rows = db.execute(
            "SELECT scene_id FROM episode_scenes WHERE episode_id = ? ORDER BY scene_order", (ep["id"],)
        ).fetchall()
        ep["scene_ids"] = [r[0] for r in scene_rows]
    return episodes


def update_episodes(job_id: int, episodes: list[dict]) -> None:
    db = get_db()
    ep_ids = [r[0] for r in db.execute("SELECT id FROM episodes WHERE job_id = ?", (job_id,)).fetchall()]
    for eid in ep_ids:
        db.execute("DELETE FROM episode_scenes WHERE episode_id = ?", (eid,))
    db.execute("DELETE FROM episodes WHERE job_id = ?", (job_id,))
    for ep in episodes:
        cursor = db.execute(
            "INSERT INTO episodes (job_id, number, title, summary, novel_chapters) VALUES (?, ?, ?, ?, ?)",
            (job_id, ep.get("number", 1), ep.get("title"), ep.get("summary"),
             json.dumps(ep.get("novel_chapters", []))),
        )
        eid = cursor.lastrowid
        for order, sid in enumerate(ep.get("scene_ids", []), 1):
            db.execute(
                "INSERT INTO episode_scenes (episode_id, scene_id, scene_order) VALUES (?, ?, ?)",
                (eid, sid, order),
            )
    db.commit()


def get_script(job_id: int) -> dict[str, Any]:
    db = get_db()
    job = get_job(job_id)
    characters = get_characters(job_id)
    episodes = get_episodes(job_id)
    scenes = get_scenes(job_id)
    scene_map = {s["id"]: s for s in scenes}

    dramatis_personae = []
    for ch in characters:
        dramatis_personae.append({
            "name": ch["name"],
            "role": ch.get("role"),
            "traits": ch.get("traits", []),
            "description": ch.get("description"),
            "first_appearance": ch.get("first_appearance"),
            "relationships": [],
        })

    output_episodes = []
    for ep in episodes:
        ep_scenes = []
        for i, sid in enumerate(ep.get("scene_ids", []), 1):
            sc = scene_map.get(sid)
            if sc:
                ep_scenes.append({
                    "id": f"S01E{ep['number']:02d}-{i:02d}",
                    "heading": sc.get("heading", ""),
                    "setting": sc.get("setting", {}),
                    "characters_present": sc.get("characters_present", []),
                    "summary": sc.get("summary", ""),
                    "beats": sc.get("beats", []),
                })
        output_episodes.append({
            "number": ep["number"],
            "title": ep.get("title", ""),
            "summary": ep.get("summary", ""),
            "novel_chapters": ep.get("novel_chapters", []),
            "scenes": ep_scenes,
        })

    notes = [dict(r) for r in db.execute(
        "SELECT type, description FROM adaptation_notes WHERE job_id = ?", (job_id,)
    ).fetchall()]

    chapter_count = db.execute(
        "SELECT COUNT(*) FROM chapters WHERE job_id = ?", (job_id,)
    ).fetchone()[0]

    return {
        "meta": {
            "title": job.get("title", ""),
            "author": job.get("author"),
            "total_episodes": len(output_episodes),
            "total_chapters_in_novel": chapter_count,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "dramatis_personae": dramatis_personae,
        "episodes": output_episodes,
        "adaptation_notes": notes,
    }
