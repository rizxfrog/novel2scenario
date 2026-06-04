from __future__ import annotations

import json
import logging
from typing import Any

from backend.agents.engine import run_agent
from backend.agents.prompts import EPISODE_STRUCTURE_PROMPT

logger = logging.getLogger(__name__)


async def structure_episodes(
    characters: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = await run_agent(
        EPISODE_STRUCTURE_PROMPT,
        {
            "characters": json.dumps(characters, ensure_ascii=False),
            "scenes": json.dumps(scenes, ensure_ascii=False, indent=2),
        },
    )
    episodes = result.get("episodes", [])
    logger.info(f"Structured {len(scenes)} scenes into {len(episodes)} episodes")
    return episodes
