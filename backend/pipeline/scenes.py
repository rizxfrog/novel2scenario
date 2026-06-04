from __future__ import annotations

import logging
from typing import Any

from backend.agents.engine import run_agent, run_parallel
from backend.agents.prompts import SCENE_ANALYZE_PROMPT

logger = logging.getLogger(__name__)


async def _analyze_chapter(number: int, title: str, content: str) -> dict[str, Any]:
    result = await run_agent(
        SCENE_ANALYZE_PROMPT,
        {"number": number, "title": title, "content": content[:8000]},
    )
    return result


async def analyze_scenes(chapters: list[dict]) -> list[dict]:
    items = [
        {"number": ch["number"], "title": ch["title"], "content": ch["content"]}
        for ch in chapters
    ]
    results = await run_parallel(_analyze_chapter, items)
    all_scenes = []
    for result in results:
        for scene in result.get("scenes", []):
            all_scenes.append(scene)
    logger.info(f"Analyzed {len(all_scenes)} scenes from {len(chapters)} chapters")
    return all_scenes
