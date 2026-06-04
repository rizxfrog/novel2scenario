from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from backend.agents.engine import run_agent
from backend.agents.prompts import SCRIPT_ASSEMBLY_PROMPT

logger = logging.getLogger(__name__)


async def assemble_script(
    meta: dict[str, Any],
    characters: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
) -> dict[str, Any]:
    scene_map = {s["id"]: s for s in scenes}

    output_episodes = []
    for ep in episodes:
        ep_scenes = []
        for i, sid in enumerate(ep.get("scene_ids", []), 1):
            s = scene_map.get(sid)
            if s:
                ep_scenes.append({
                    "id": f"S01E{ep['number']:02d}-{i:02d}",
                    "heading": s.get("heading", ""),
                    "setting": s.get("setting", s.get("setting_json", {})),
                    "characters_present": s.get("characters_present", []),
                    "summary": s.get("summary", ""),
                    "beats": s.get("beats", []),
                })
        output_episodes.append({
            "number": ep["number"],
            "title": ep.get("title", ""),
            "summary": ep.get("summary", ""),
            "novel_chapters": ep.get("novel_chapters", []),
            "scenes": ep_scenes,
        })

    dramatis_personae = []
    for char in characters:
        dramatis_personae.append({
            "name": char["name"],
            "role": char.get("role", "supporting"),
            "traits": char.get("traits", []),
            "description": char.get("description", ""),
            "first_appearance": char.get("first_appearance", 1),
            "relationships": char.get("relationships", []),
        })

    result = await run_agent(
        SCRIPT_ASSEMBLY_PROMPT,
        {
            "characters": json.dumps(characters, ensure_ascii=False),
            "episodes": json.dumps(output_episodes, ensure_ascii=False, indent=2),
        },
    )

    return {
        "meta": {
            "title": meta.get("title", "Untitled"),
            "author": meta.get("author"),
            "total_episodes": len(output_episodes),
            "total_chapters_in_novel": meta.get("total_chapters_in_novel", 0),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "dramatis_personae": dramatis_personae,
        "episodes": output_episodes,
        "adaptation_notes": result.get("adaptation_notes", []),
    }
