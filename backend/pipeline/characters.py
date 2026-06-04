from __future__ import annotations

import logging
from typing import Any

from backend.agents.engine import run_agent, run_parallel
from backend.agents.prompts import CHARACTER_EXTRACT_PROMPT

logger = logging.getLogger(__name__)


async def _extract_from_chapter(number: int, title: str, content: str) -> dict[str, Any]:
    result = await run_agent(
        CHARACTER_EXTRACT_PROMPT,
        {"number": number, "title": title, "content": content[:8000]},
    )
    return result


def merge_characters(raw_characters: list[dict]) -> list[dict]:
    by_name: dict[str, dict] = {}
    for char in raw_characters:
        name = char["name"]
        if name not in by_name:
            by_name[name] = {**char, "traits": list(char.get("traits", []))}
        else:
            existing = by_name[name]
            for trait in char.get("traits", []):
                if trait not in existing["traits"]:
                    existing["traits"].append(trait)
            if char.get("role") and not existing.get("role"):
                existing["role"] = char["role"]
            if char.get("first_appearance", 999) < existing.get("first_appearance", 999):
                existing["first_appearance"] = char["first_appearance"]
            if len(char.get("description", "")) > len(existing.get("description", "")):
                existing["description"] = char["description"]
    return list(by_name.values())


async def extract_characters(chapters: list[dict]) -> list[dict]:
    items = [
        {"number": ch["number"], "title": ch["title"], "content": ch["content"]}
        for ch in chapters
    ]
    results = await run_parallel(_extract_from_chapter, items)
    all_characters = []
    for result in results:
        all_characters.extend(result.get("characters", []))
    merged = merge_characters(all_characters)
    logger.info(f"Extracted {len(merged)} unique characters from {len(chapters)} chapters")
    return merged
