import pytest
from unittest.mock import patch
from backend.pipeline.characters import extract_characters, merge_characters


@pytest.mark.asyncio
async def test_extract_characters_parallel():
    chapters = [
        {"number": 1, "title": "Ch1", "content": "Alice met Bob."},
        {"number": 2, "title": "Ch2", "content": "Alice fought Charlie."},
    ]

    async def mock_extract_one(**kwargs):
        num = kwargs["number"]
        if num == 1:
            return {"characters": [{"name": "Alice", "role": "protagonist", "traits": ["brave"], "description": "A hero", "first_appearance": 1}]}
        else:
            return {"characters": [
                {"name": "Alice", "role": "protagonist", "traits": ["determined"], "description": "Still a hero", "first_appearance": 1},
                {"name": "Charlie", "role": "antagonist", "traits": ["evil"], "description": "A villain", "first_appearance": 2},
            ]}

    with patch("backend.pipeline.characters._extract_from_chapter", side_effect=mock_extract_one):
        result = await extract_characters(chapters)

    assert len(result) == 2
    alice = next(c for c in result if c["name"] == "Alice")
    assert alice["role"] == "protagonist"


def test_merge_characters_deduplicates():
    raw = [
        {"name": "Alice", "role": "protagonist", "traits": ["brave"], "description": "desc1", "first_appearance": 1},
        {"name": "Alice", "role": None, "traits": ["smart"], "description": "desc2", "first_appearance": 2},
        {"name": "Bob", "role": "supporting", "traits": ["funny"], "description": "desc3", "first_appearance": 1},
    ]
    merged = merge_characters(raw)
    assert len(merged) == 2
    alice = next(c for c in merged if c["name"] == "Alice")
    assert alice["first_appearance"] == 1
    assert "brave" in alice["traits"]
    assert "smart" in alice["traits"]
