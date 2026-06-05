from __future__ import annotations

import re
import logging
from typing import Optional

from backend.agents.engine import run_agent
from backend.agents.prompts import CHAPTER_SPLIT_PROMPT

logger = logging.getLogger(__name__)

DELIMITER_PATTERNS = [
    r"第[零一二三四五六七八九十百千\d]+章\s*[^\n]*",
    r"第[零一二三四五六七八九十百千\d]+节\s*[^\n]*",
    r"Chapter\s+\d+[^\n]*",
    r"^\d+\.\s+[^\n]+",
]


def _detect_delimiter(text: str) -> Optional[str]:
    for pattern in DELIMITER_PATTERNS:
        matches = re.findall(pattern, text, re.MULTILINE)
        if len(matches) >= 3:
            return pattern
    return None


def _split_by_delimiter(text: str, pattern: str) -> list[dict]:
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    chapters = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading = match.group().strip()
        # Extract just the title part after "第X章"
        title_match = re.search(r"第[^\s\d章节]+章\s*(.*)", heading)
        if title_match and title_match.group(1).strip():
            title = title_match.group(1).strip()
        else:
            # Try "第X章 Title" pattern
            title_match = re.search(r"第[\d]+章\s*(.*)", heading)
            if title_match and title_match.group(1).strip():
                title = title_match.group(1).strip()
            else:
                title = heading
        content = text[start:end].strip()
        content = re.sub(r"^" + re.escape(heading) + r"\s*\n*", "", content)
        chapters.append({
            "number": i + 1,
            "title": title,
            "content": content.strip(),
        })
    return chapters


async def split_chapters(novel_text: str) -> list[dict]:
    pattern = _detect_delimiter(novel_text)
    if pattern:
        chapters = _split_by_delimiter(novel_text, pattern)
        logger.info(f"Split into {len(chapters)} chapters using regex pattern: {pattern}")
        return chapters

    logger.info("No clear delimiter found, using LLM for chapter splitting")
    result = await run_agent(
        CHAPTER_SPLIT_PROMPT,
        {"text": novel_text},
        max_completion_tokens=32768,
    )
    return result.get("chapters", [])
