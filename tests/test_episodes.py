import pytest
from unittest.mock import patch
from backend.pipeline.episodes import structure_episodes


@pytest.mark.asyncio
async def test_structure_episodes():
    characters = [{"name": "Alice", "role": "protagonist"}]
    scenes = [
        {"id": 1, "summary": "Opening scene", "characters_present": ["Alice"]},
        {"id": 2, "summary": "Conflict scene", "characters_present": ["Alice"]},
        {"id": 3, "summary": "Closing scene", "characters_present": ["Alice"]},
    ]

    async def mock_agent(*args, **kwargs):
        return {"episodes": [
            {"number": 1, "title": "Episode 1", "summary": "...", "novel_chapters": [1], "scene_ids": [1, 2]},
            {"number": 2, "title": "Episode 2", "summary": "...", "novel_chapters": [2], "scene_ids": [3]},
        ]}

    with patch("backend.pipeline.episodes.run_agent", side_effect=mock_agent):
        result = await structure_episodes(characters, scenes)

    assert len(result) == 2
    assert result[0]["title"] == "Episode 1"
    assert 1 in result[0]["scene_ids"]
